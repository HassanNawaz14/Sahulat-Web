# P15 — Pay Gateway Lite Module (M8)

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P03 (Database Schema), P04 (Auth), P06 (Bill Tracker), P10 (Budget Manager)  
**Required By:** P18 (Monetization), P20 (Frontend), P21 (API Spec)

---

## 1. Scope

Pay Gateway Lite reduces bill payment friction without processing payments directly. Sahulat does not hold money, initiate bank transfers, or act as a payment institution in V1/V2. Instead, it deep-links users to JazzCash, EasyPaisa, bank apps, or provider payment pages with the consumer number and amount pre-filled where supported.

Actual payment processing is out of scope until Sahulat has business registration, merchant agreements, and compliance review.

---

## 2. User-Facing Features

| Feature | Priority | Description |
|---------|----------|-------------|
| Pay button on bill card | P2 | Opens payment options sheet |
| Copy consumer number | P2 | One tap copy with provider label |
| Deep-link payment app | P2 | JazzCash/EasyPaisa/bank link where possible |
| Payment instructions | P2 | Step-by-step provider-specific flow |
| Mark as paid after return | P2 | Manual confirmation updates bill status |
| Payment reminder | P2 | Notify before due date |

---

## 3. Payment Options

| Option | V1 Behavior |
|--------|-------------|
| JazzCash | Deep-link or show instructions |
| EasyPaisa | Deep-link or show instructions |
| Bank app | Copy consumer number + bill amount |
| Provider website | Open official payment page |
| Manual paid mark | User confirms payment after external flow |

---

## 4. Strict Boundaries

Sahulat must not:

- collect card numbers
- collect bank login details
- collect wallet PINs
- receive payment funds
- claim payment success without confirmation from provider or user
- show fake payment receipts

Every payment screen must state that payment happens in the selected official app/service.

---

## 5. Data Model

Add if absent:

```sql
CREATE TABLE public.payment_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  bill_id UUID REFERENCES bills(id) ON DELETE SET NULL,
  provider_code TEXT NOT NULL,
  payment_method TEXT NOT NULL,
  amount NUMERIC(10,2) NOT NULL,
  status TEXT DEFAULT 'opened',
  deep_link_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  confirmed_paid_at TIMESTAMPTZ
);
```

Status values: `opened`, `user_marked_paid`, `cancelled`, `failed`, `verified_later`.

---

## 6. Frontend Flow

1. User taps Pay on a bill.
2. Bottom sheet shows amount, due date, consumer number.
3. User selects payment method.
4. App creates `payment_attempt`.
5. App opens deep link or official site.
6. On return, app asks: "Did you complete this payment?"
7. If yes, bill status becomes `paid_manual` until next bill confirms arrears.

---

## 7. API Contracts

### 7.1 `POST /api/v1/payments/attempts`

Request:
```json
{
  "bill_id": "uuid",
  "payment_method": "jazzcash"
}
```

Response:
```json
{
  "attempt_id": "uuid",
  "deep_link_url": "jazzcash://...",
  "fallback_instructions": ["Open JazzCash", "Select bill payment", "Choose LESCO", "Paste reference number"]
}
```

### 7.2 `POST /api/v1/payments/attempts/{id}/confirm-paid`

Marks bill as paid manually.

---

## 8. Acceptance Criteria

- Pay flow never asks for wallet PIN or banking credentials.
- Every attempt is logged.
- User can copy consumer number and amount.
- Manual paid status is distinct from provider-verified paid status.
- Actual payment processing remains out of scope.
