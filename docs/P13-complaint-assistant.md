# P13 — Complaint Assistant Module (M7)

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P03 (Database Schema), P04 (Auth), P05 (Scraper System), P06 (Bill Tracker), P09 (Outage Tracker)  
**Required By:** P18 (Monetization), P20 (Frontend), P21 (API Spec), P22 (Deployment & DevOps)

---

## 1. Scope

Complaint Assistant helps users file utility complaints with NEPRA, OGRA, PTA, WASA, SNGPL, SSGC, and utility provider portals. Since official APIs are not available, V1 uses guided form preparation and browser automation where feasible. The module stores complaint drafts, submitted reference numbers, and status notes.

This is a V2 module because it depends on stable user profile data, linked consumer accounts, and Playwright infrastructure.

---

## 2. Complaint Authorities

| Utility | Authority | Portal Type | V1 Method |
|---------|-----------|-------------|-----------|
| Electricity | NEPRA | Web form | Guided + Playwright autofill |
| Gas | OGRA / SNGPL / SSGC | Web form | Guided + Playwright where possible |
| Internet/mobile | PTA | Web form | Guided + Playwright autofill |
| Water | WASA/KW&SB | Web form or phone | Guided draft + contact link |
| Billing issue | Provider portal | Mixed | Guided draft |

---

## 3. User-Facing Features

| Feature | Priority | Description |
|---------|----------|-------------|
| Complaint wizard | P2 | Select utility, account, issue type |
| Auto-filled user details | P2 | Uses profile and consumer account data |
| Evidence attachment checklist | P2 | Bill screenshot, outage report, meter photo |
| Playwright auto-fill | P2 | Opens/automates supported complaint forms |
| Reference tracking | P2 | Store complaint number and status |
| Follow-up reminders | P2 | Notify after expected response window |
| Complaint history | P2 | Timeline by utility/account |

---

## 4. Complaint Flow

1. User opens `/complaints`.
2. Selects linked consumer account or utility type.
3. Selects issue category.
4. App builds complaint draft from templates.
5. User reviews text and confirms.
6. If portal supports automation, backend queues Playwright task.
7. If automation is not safe, app shows copy-ready complaint and official portal link.
8. User enters returned reference number if automation cannot read it.
9. Complaint appears in tracking timeline.

---

## 5. Issue Categories

| Code | Applies To | Description |
|------|------------|-------------|
| `wrong_bill` | Electricity/Gas/Water/Internet | Bill amount appears incorrect |
| `meter_reading_error` | Electricity/Gas/Water | Reading mismatch |
| `unscheduled_outage` | Electricity/Internet | Repeated outage not in schedule |
| `low_pressure` | Gas/Water | Service available but unusable |
| `no_supply` | Gas/Water | No supply |
| `poor_service` | Internet | Slow speed/disconnections |
| `late_resolution` | Any | Previous complaint not resolved |

---

## 6. Automation Rules

Playwright automation must be treated as fragile.

Required safeguards:

- Never submit without explicit user confirmation.
- Store screenshots of final review page only if user consents.
- If CAPTCHA appears, stop and return manual instructions.
- If selector changes, mark automation unsupported and notify admin.
- Run Playwright only in backend worker, never from frontend.

---

## 7. Data Model

If P03 does not already include complaint tables, add:

```sql
CREATE TABLE public.complaints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  consumer_account_id UUID REFERENCES consumer_accounts(id) ON DELETE SET NULL,
  authority TEXT NOT NULL,
  issue_type TEXT NOT NULL,
  status TEXT DEFAULT 'draft',
  complaint_text TEXT NOT NULL,
  reference_number TEXT,
  submitted_at TIMESTAMPTZ,
  next_followup_at TIMESTAMPTZ,
  raw_response JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

RLS: users manage only their own complaints.

---

## 8. API Contracts

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/complaints/templates` | GET | List templates |
| `/api/v1/complaints/draft` | POST | Generate complaint draft |
| `/api/v1/complaints` | POST | Save complaint |
| `/api/v1/complaints/{id}/submit` | POST | Start supported automation |
| `/api/v1/complaints/{id}/reference` | PUT | Save manual reference number |
| `/api/v1/complaints` | GET | Complaint history |

---

## 9. Acceptance Criteria

- User can generate and save a complaint draft.
- Complaint draft includes profile, account, provider, and issue details.
- Automation never submits without explicit confirmation.
- CAPTCHA or selector failure returns manual fallback.
- Complaint history persists reference numbers and follow-up dates.
