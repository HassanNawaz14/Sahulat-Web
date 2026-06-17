# P04 — Auth & User System

**Document Type:** Rigid Plan
**Status:** Authoritative — do not deviate without versioning this document
**Depends On:** P01 (Project Overview), P02 (Tech Stack), P03 (Database Schema)
**Required By:** P05, P06, P07, P08, P09, P10, P11, P12, P13, P14, P15, P16, P17, P19, P20, P21

---

## 1. Scope

This document defines the complete authentication, registration, onboarding, profile management, and multi-home system for Sahulat. It covers every screen, every API contract, and every state transition involved in getting a user from "never heard of Sahulat" to "fully onboarded with at least one consumer account linked."

All auth is handled by **Supabase Auth**. FastAPI never issues its own tokens — it only validates Supabase-issued JWTs.

---

## 2. Supported Sign-In Methods

| Method | Provider | V1/V2 |
|--------|----------|-------|
| Email + OTP (passwordless) | Supabase Auth (email OTP) | V1 |
| Phone + OTP (SMS) | Supabase Auth (Twilio integration) | V1 |
| Google OAuth | Supabase Auth (Google provider) | V1 |
| Email + Password | Supabase Auth | V2 (fallback only, hidden by default) |

**Default flow shown to new users:** Phone number entry → OTP. Pakistani users trust SMS OTP far more than email for a utility app. Email OTP and Google OAuth are offered as secondary options on the same screen.

**Phone number format:** Stored and validated as E.164 (`+92XXXXXXXXXX`). Frontend input mask: `+92` prefix locked, 10 digits after.

---

## 3. Signup / Login Flow (Exact Sequence)

### 3.1 Entry Screen (`/auth/login`)

```
┌─────────────────────────────┐
│      Sahulat Logo            │
│   "Apni utilities, ek jagah" │
│                               │
│  [ Phone Number Input ]      │
│  [ Continue with Phone ]     │
│                               │
│  ── or ──                    │
│                               │
│  [ Continue with Google ]    │
│  [ Continue with Email ]     │
└─────────────────────────────┘
```

### 3.2 Phone OTP Flow

1. User enters phone number → frontend validates E.164 format client-side (regex: `^\+92[0-9]{10}$`)
2. Frontend calls `supabase.auth.signInWithOtp({ phone })`
3. Supabase sends SMS OTP via configured provider (Twilio, configured in Supabase dashboard — not application code)
4. Frontend navigates to `/auth/verify?method=phone&phone=...`
5. User enters 6-digit OTP
6. Frontend calls `supabase.auth.verifyOtp({ phone, token, type: 'sms' })`
7. On success: Supabase returns session (access_token, refresh_token). Trigger `handle_new_user()` (P03 §13.1) fires automatically on first-ever login, creating `profiles` row and `notification_preferences` row.
8. Frontend checks: does `profiles.city` exist (i.e., has onboarding been completed)? If `NULL` → redirect to `/onboarding`. Else → redirect to `/dashboard`.

### 3.3 Email OTP Flow

Identical to phone flow but uses `supabase.auth.signInWithOtp({ email })` and `type: 'email'` on verify. OTP delivered via Supabase's built-in email (or custom SMTP configured later).

### 3.4 Google OAuth Flow

1. Frontend calls `supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: '<APP_URL>/auth/callback' } })`
2. User completes Google consent screen
3. Redirected to `/auth/callback`, which exchanges the code for a session automatically (handled by Supabase JS client)
4. Same post-login check as §3.2 step 8

### 3.5 Session Persistence

- Supabase JS client persists session in browser storage automatically (handled internally by the `@supabase/ssr` package — **not** manual localStorage, since this must work correctly with Next.js SSR cookies).
- Access token: 1 hour expiry. Refresh token: 7 days expiry, auto-rotated on use.
- Frontend wraps the app in a `SessionProvider` (React Context) that exposes `user`, `session`, `isLoading` to all components.

---

## 4. Onboarding Flow (`/onboarding`)

Triggered exactly once per user, immediately after first successful login (detected via `profiles.city IS NULL`). Cannot be skipped — utility tracking is meaningless without city/area. Multi-step wizard, no page reloads between steps (client-side state).

### Step 1 — Basic Info
- Full name (text input, required)
- City (dropdown, required): Lahore, Karachi, Islamabad, Faisalabad, Rawalpindi, Multan, Peshawar, Gujranwala, Other
- Area (text input with autocomplete suggestions seeded per city, required) — stored as free text but slugified for `area_slug` matching used elsewhere (P09, P12)

### Step 2 — Preferred Language
- English / اردو toggle. Stored in `profiles.preferred_lang`. Does **not** block progress; defaults to `en`.

### Step 3 — Add Your First Home
- Auto-creates a `homes` row with `name = 'Home'`, `is_default = true`, `city`/`area` pre-filled from Step 1.
- User may rename (e.g., "My House") but cannot skip — every user must have at least one home.

### Step 4 — Add a Consumer Number (Optional, Skippable)
- Prompts: "Add your electricity bill to get started" with a single input for consumer number + DISCO dropdown (defaults to DISCO inferred from city, see §5.1).
- "Skip for now" button always visible — this step is the only skippable one. If skipped, an empty-state dashboard with a persistent "Add your first utility" CTA card is shown post-onboarding (see P06 §4.1).

### Step 5 — Notification Permission Prompt
- Native browser permission prompt for Web Push (see P19 §3). Explained first with a custom pre-prompt screen ("Get notified before load shedding hits your area") before triggering the actual browser permission dialog, to maximize opt-in rate (industry best practice — never trigger the native prompt cold).

### Completion
- `profiles.city` and `profiles.area` are now non-null → onboarding is considered complete for all future logins.
- Redirect to `/dashboard`.

---

## 5. Profile & Settings Management

### 5.1 DISCO Auto-Detection by City

Used during onboarding Step 4 and the "Add Utility" flow (P06) to pre-select the likely DISCO:

| City | Default DISCO |
|------|---------------|
| Lahore | LESCO |
| Karachi | K-Electric |
| Islamabad, Rawalpindi | IESCO |
| Faisalabad | FESCO |
| Multan | MEPCO |
| Gujranwala | GEPCO |
| Peshawar | PESCO |
| Quetta | QESCO |
| Hyderabad | HESCO |
| Sukkur | SEPCO |
| Other | No default — user must select manually |

This is a static lookup table maintained in `frontend/lib/constants/discoMap.ts` and mirrored in `backend/app/constants.py`. **Not** a database table — it changes too rarely to justify a query.

### 5.2 `/settings/profile` Screen

Editable fields: full name, avatar (upload to Supabase Storage bucket `avatars`, max 2MB, resized client-side to 256×256 before upload), preferred language. City/area are editable here too but changing city does **not** retroactively change existing `homes` records — it only affects the default for new homes.

### 5.3 `/settings` — Homes Management (Multi-Home)

- List view of all `homes` rows for the user (from P03 §2.2).
- "Add Home" button → modal with name, address, city, area. Cannot exceed 5 homes on free tier (enforced at API layer, not DB constraint — see §7.3). Premium tier (P18) removes this cap.
- Each home shows count of linked consumer accounts.
- Deleting a home: confirmation modal warns "All consumer accounts linked to this home will become unassigned, not deleted." (`consumer_accounts.home_id` is `ON DELETE SET NULL` per P03 §3.1 — bills history is preserved.)
- Exactly one home must have `is_default = true` at all times. Setting a new default unsets the previous one (handled transactionally in the API, not via DB trigger, to keep logic visible in application code per documentation rule #4).

### 5.4 `/settings/notifications`

Maps directly to `notification_preferences` table (P03 §10.2). All fields editable as toggles/number inputs. Full detail in **P19 — Notifications & Alerts System**.

---

## 6. Account Deletion (GDPR-style, Required for Play Store / App Store Compliance Even as PWA)

1. User requests deletion from `/settings/profile` → "Delete Account" → confirmation requires typing "DELETE".
2. Frontend calls `POST /api/v1/auth/delete-account`.
3. Backend calls Supabase Admin API `auth.admin.deleteUser(user_id)`.
4. Because every table referencing `profiles.id` uses `ON DELETE CASCADE` (see P03 throughout), all user data is removed automatically by Postgres — no manual cleanup loop needed, **except**: `community_outage_reports.user_id` is `ON DELETE SET NULL` (anonymized, not deleted, since the report itself has community value) and `solar_production_readings` is cascaded via `solar_installations`.
5. User is signed out immediately; session invalidated.

---

## 7. Backend Auth Middleware (FastAPI)

### 7.1 JWT Verification

Every protected route depends on a shared FastAPI dependency:

```python
# backend/app/core/auth.py
from fastapi import Depends, HTTPException, Header
from jose import jwt, JWTError
import os

SUPABASE_JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]

async def get_current_user(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")
    return {"user_id": payload["sub"], "email": payload.get("email"), "phone": payload.get("phone")}
```

Every route handler that touches user data declares `current_user: dict = Depends(get_current_user)` and uses `current_user["user_id"]` for all queries — never trusts a `user_id` passed in the request body or query params.

### 7.2 Admin-Only Routes

A second dependency, `get_admin_user`, additionally checks the user's `id` against a static allowlist defined in the `ADMIN_USER_IDS` environment variable (comma-separated UUIDs), since there is no `is_admin` column in `profiles` (admin access is intentionally not stored in client-readable tables for security).

### 7.3 Plan-Limit Enforcement

Limits like "max 5 homes on free tier" and "max 10 consumer accounts on free tier" (see P18 §4 for full premium feature matrix) are enforced in the API layer at creation time:

```python
async def enforce_home_limit(user_id: str, db):
    if (await db.fetch_val(
        "SELECT premium FROM profiles WHERE id = :uid", {"uid": user_id}
    )):
        return  # premium = unlimited
    count = await db.fetch_val(
        "SELECT COUNT(*) FROM homes WHERE user_id = :uid", {"uid": user_id}
    )
    if count >= 5:
        raise HTTPException(403, "Free tier limit reached: max 5 homes. Upgrade to Premium.")
```

This pattern (fetch `premium` flag, compare count, raise 403) is reused for every limited resource.

---

## 8. API Endpoints (Auth & Profile)

Full request/response schemas in **P21 — API Spec**. Summary:

| Method | Path | Purpose | Auth Required |
|--------|------|---------|----------------|
| GET | `/api/v1/auth/me` | Returns current profile + homes | Yes |
| PATCH | `/api/v1/auth/profile` | Update name, city, area, language, avatar_url | Yes |
| POST | `/api/v1/auth/onboarding/complete` | Marks onboarding done (sets city/area if not already set via PATCH) | Yes |
| POST | `/api/v1/auth/delete-account` | Triggers account deletion (§6) | Yes |
| GET | `/api/v1/auth/homes` | List user's homes | Yes |
| POST | `/api/v1/auth/homes` | Create home (enforces §7.3 limit) | Yes |
| PATCH | `/api/v1/auth/homes/{id}` | Update home, including `is_default` swap logic | Yes |
| DELETE | `/api/v1/auth/homes/{id}` | Delete home (cascades per §5.3) | Yes |

---

## 9. Edge Cases & Rules

1. **Phone number already registered via Google with same email:** Supabase Auth treats phone and email/Google as separate identity providers unless explicitly linked. V1 does **not** implement identity linking — if a user signs up with Google then later tries phone OTP, they get a second account. This is a known V1 limitation; document it in `/settings` as "each sign-in method creates a separate account in V1."
2. **OTP rate limiting:** Supabase enforces its own OTP send rate limits (default: 1 per 60 seconds per identifier). Frontend must disable the "Resend OTP" button for 60 seconds client-side to match.
3. **Session expiry mid-action:** Axios interceptor (P02 §2.1) catches 401 responses globally, attempts a silent token refresh via `supabase.auth.refreshSession()`, and retries the original request once. If refresh also fails, force logout and redirect to `/auth/login`.
4. **Onboarding interrupted (user closes app mid-Step-3):** Detected via `profiles.city IS NULL` on next login — user resumes at Step 1 of onboarding (wizard state is not persisted across sessions in V1; re-entering basic info is low-friction enough to not warrant resume-state storage).
