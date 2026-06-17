# P12 — Community Reports Module (M10)

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P03 (Database Schema), P04 (Auth), P09 (Outage Tracker), P19 (Notifications)  
**Required By:** P09 (Outage Tracker), P14 (ISP Comparison), P17 (Usage Insights), P20 (Frontend), P21 (API Spec)

---

## 1. Scope

Community Reports is the hyperlocal public signal layer of Sahulat. It lets users report and view real-time problems in their area: power outage, gas pressure, water shortage, internet down, wrong bill, and service restoration.

P09 uses the same reporting base for outages; P12 expands it into a broader city/area feed with verification, reputation, moderation, and sharing.

---

## 2. Report Types

| Code | Utility | Description |
|------|---------|-------------|
| `electricity_outage` | Electricity | Power is gone |
| `voltage_issue` | Electricity | Low/high voltage |
| `gas_low_pressure` | Gas | Low pressure |
| `gas_outage` | Gas | No gas supply |
| `water_shortage` | Water | No water supply |
| `dirty_water` | Water | Bad water quality report; informational only |
| `internet_down` | Internet | ISP service down |
| `bill_issue` | Any | Abnormally high/wrong bill |
| `restored` | Any | Service restored |

---

## 3. User-Facing Features

| Feature | Priority | Description |
|---------|----------|-------------|
| Area feed | P2 | Latest reports near user's area |
| Report composer | P2 | Utility, type, severity, optional note |
| Verification badge | P2 | Based on report volume and reputation |
| Map/list view | P2 | Mobile-first list, map optional |
| WhatsApp share | P2 | Share verified report link |
| Follow area | P2 | Receive alerts for saved areas |
| Report restored | P2 | Mark problem resolved |
| Moderation queue | P2 | Admin hides abuse/spam |

---

## 4. Reputation Rules

Each user has an internal report reputation score. It is not shown directly.

| Action | Score Impact |
|--------|--------------|
| Report later verified | +2 |
| Report marked restored by others | +1 |
| Duplicate false report | -1 |
| Admin hides report as spam | -5 |
| Excess reports in short window | Temporary rate limit |

Reputation affects confidence score but must never block emergency reporting entirely unless abuse is severe.

---

## 5. API Contracts

### 5.1 `GET /api/v1/community/feed`

Query params: `city`, `area`, `utility_type`, `limit`, `cursor`.

Response:
```json
{
  "items": [
    {
      "id": "uuid",
      "type": "gas_low_pressure",
      "utility_type": "gas",
      "city": "lahore",
      "area": "DHA Phase 5",
      "severity": "medium",
      "status": "active",
      "confidence_score": 0.74,
      "report_count": 14,
      "created_at": "2025-06-17T12:10:00Z"
    }
  ],
  "next_cursor": null
}
```

### 5.2 `POST /api/v1/community/reports`

Creates a report. Same ownership and rate-limit rules as P09.

### 5.3 `POST /api/v1/community/reports/{id}/restore`

Marks a report cluster as restored from the current user's perspective.

---

## 6. Clustering Logic

Reports cluster when:

- same `utility_type`
- same `report_type`
- same city and normalized area slug
- created within the active report window

Default active windows:

| Utility | Window |
|---------|--------|
| Electricity | 3 hours |
| Gas | 6 hours |
| Water | 12 hours |
| Internet | 4 hours |
| Bill issue | 30 days |

---

## 7. Moderation

Admin panel must support:

- hide report
- merge duplicate clusters
- pin official update
- mark cluster verified
- ban abusive reporter

Hidden reports remain in database for audit but are excluded from public APIs.

---

## 8. Privacy Rules

- Never show exact address.
- Public feed displays area only.
- Notes are limited to 200 characters.
- Strip phone numbers from notes before display.
- User names are hidden by default; show "Nearby user".

---

## 9. Acceptance Criteria

- Users can post and view reports by area.
- Reports cluster and expire automatically.
- Confidence score is returned in feed API.
- Moderation can hide abusive content.
- No exact user address is exposed in public feed.
