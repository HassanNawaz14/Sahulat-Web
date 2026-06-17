# P19 — Notifications & Alerts System

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P02 (Tech Stack), P03 (Database Schema), P04 (Auth), P06 (Bill Tracker), P07 (Consumption Monitor), P09 (Outage Tracker), P10 (Budget Manager), P11 (Solar Dashboard), P17 (Usage Insights)  
**Required By:** P20 (Frontend), P21 (API Spec), P22 (Deployment & DevOps)

---

## 1. Scope

The Notifications system sends Web Push alerts for due bills, scheduled outages, slab boundary warnings, budget limits, community reports, solar health, and reminders. Push is essential for daily stickiness and must be built before public launch.

V1 uses Web Push with VAPID keys. SMS is premium/future only.

---

## 2. Notification Types

| Code | Priority | Source |
|------|----------|--------|
| `bill_due_3_days` | P0 | P06 |
| `bill_due_today` | P0 | P06 |
| `scheduled_outage_15_min` | P0 | P09 |
| `slab_boundary` | P0 | P07/P08 |
| `reading_reminder` | P2 | P07 |
| `budget_80_percent` | P1 | P10 |
| `budget_exceeded` | P1 | P10 |
| `nearby_outage_verified` | P1 | P09/P12 |
| `solar_underperformance` | P2 | P11/P17 |
| `complaint_followup` | P2 | P13 |

---

## 3. Permission Flow

Never trigger native permission cold.

1. Show custom explanation screen during onboarding.
2. User taps Enable Alerts.
3. Browser native permission prompt appears.
4. Frontend registers service worker and push subscription.
5. Backend stores subscription.
6. User can manage categories from `/settings/notifications`.

---

## 4. Data Model

Required tables:

- `notification_preferences`
- `push_subscriptions`
- `notification_events`

`notification_events` must record every attempted send for debugging and rate limiting.

---

## 5. Backend Structure

```
backend/app/services/notifications/
  webpush.py
  preferences.py
  scheduler.py
  templates.py
```

Use `pywebpush` or equivalent for VAPID Web Push.

---

## 6. Rate Limits

| Type | Limit |
|------|-------|
| Bill due | Max 2 per bill |
| Scheduled outage | Max 1 before + 1 start per outage |
| Slab boundary | Max 1 per threshold per billing cycle |
| Community outage | Max 3 per day |
| Budget | Max 2 per category per month |
| Solar health | Max 1 per day |

---

## 7. API Contracts

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/notifications/subscribe` | POST | Save push subscription |
| `/api/v1/notifications/preferences` | GET | Get preferences |
| `/api/v1/notifications/preferences` | PUT | Update preferences |
| `/api/v1/notifications/test` | POST | Send test notification |

---

## 8. Message Rules

Notifications must be short, useful, and localized.

Example:

```json
{
  "title": "LESCO outage in 15 minutes",
  "body": "DHA Phase 5 scheduled outage: 10:00 AM to 11:00 AM.",
  "url": "/outages"
}
```

No notification may include a full consumer number. Mask it if needed.

---

## 9. Acceptance Criteria

- PWA can subscribe to Web Push on Android Chrome.
- User can disable each notification category.
- Duplicate alerts are prevented by `notification_events`.
- Notifications deep-link to the relevant screen.
- Failed subscriptions are cleaned up when push endpoint returns gone/expired.
