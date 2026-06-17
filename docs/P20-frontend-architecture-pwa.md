# P20 — Frontend Architecture & PWA

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P01 (Project Overview), P02 (Tech Stack), P04 (Auth), P06-P19 (Feature Documents)  
**Required By:** P21 (API Spec), P22 (Deployment & DevOps)

---

## 1. Scope

This document defines the Next.js frontend architecture, route structure, PWA behavior, component system, state management, and UX rules for Sahulat.

The app is mobile-first because the primary user is an Android smartphone user in Pakistan.

---

## 2. Stack

| Layer | Tool |
|-------|------|
| Framework | Next.js 14+ App Router |
| Styling | Tailwind CSS |
| Components | Local component library + Radix primitives where needed |
| Icons | Lucide React |
| Forms | React Hook Form + Zod |
| Server state | TanStack Query |
| Client state | Zustand |
| Charts | Recharts |
| PWA | `next-pwa` / Workbox |
| Auth | Supabase SSR client |

---

## 3. App Routes

```
/app
  /(public)
    page.tsx
    estimate/page.tsx
    isp/page.tsx
    solar/sizing/page.tsx
  /(auth)
    auth/login/page.tsx
    auth/verify/page.tsx
    auth/callback/route.ts
    onboarding/page.tsx
  /(app)
    dashboard/page.tsx
    bills/page.tsx
    bills/[consumerAccountId]/page.tsx
    consumption/page.tsx
    outages/page.tsx
    budget/page.tsx
    solar/page.tsx
    community/page.tsx
    complaints/page.tsx
    settings/page.tsx
    settings/profile/page.tsx
    settings/notifications/page.tsx
  admin/page.tsx
```

---

## 4. Component Structure

```
frontend/components/
  ui/
  layout/
  bills/
  consumption/
  outages/
  budget/
  solar/
  community/
  monetization/
  charts/
```

Rules:

- Shared primitive components live in `ui`.
- Feature-specific components stay inside feature folders.
- API calls live in `frontend/lib/api`.
- Zod schemas live near forms or in `frontend/lib/schemas`.

---

## 5. Navigation

Mobile bottom nav tabs:

1. Dashboard
2. Bills
3. Outages
4. Budget
5. More

More opens: Consumption, Solar, Community, Complaints, ISP, Settings.

Desktop uses a left sidebar.

---

## 6. PWA Requirements

| Requirement | Rule |
|-------------|------|
| Manifest | Name Sahulat, short name Sahulat |
| Install prompt | Show after user links first utility or views 3 sessions |
| Service worker | Cache shell and public SEO pages |
| Offline fallback | Show last synced dashboard data |
| Push | Integrate with P19 |
| Icons | 192x192 and 512x512 required |

---

## 7. UX Rules

- Utility status must be visible within 2 taps.
- Dashboard first screen shows linked bills, outage status, and key alert.
- Avoid decorative screens after login.
- Urdu labels may appear as helper text, but primary UI is English.
- Critical actions require confirmation: delete account, submit complaint, external payment.
- Loading states must use skeletons for bill/outage cards.

---

## 8. API Client Rules

All backend calls go through:

```
frontend/lib/api/client.ts
```

Responsibilities:

- attach Supabase access token
- handle 401 by refreshing session
- map API errors to typed frontend errors
- add request id header for debugging

---

## 9. SEO Rules

Public pages that must be indexable:

- `/estimate`
- `/estimate/electricity`
- `/isp`
- `/isp/[city]`
- `/solar/sizing`
- public explainer pages for DISCO bill checking later

Authenticated dashboard pages must not be indexed.

---

## 10. Acceptance Criteria

- App works as installable PWA on Android Chrome.
- Dashboard is usable on 360px wide screens.
- Authenticated routes redirect unauthenticated users.
- Public calculator pages render SEO content server-side.
- Push subscription flow connects to P19.
