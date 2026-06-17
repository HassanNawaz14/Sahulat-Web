# P21 — API Spec (Backend)

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P02 (Tech Stack), P03 (Database Schema), P04 (Auth), P05 (Scraper System), P06-P20 (All Feature Documents)  
**Required By:** P20 (Frontend), P22 (Deployment & DevOps)

---

## 1. Scope

This document defines the FastAPI backend API surface for Sahulat. It consolidates endpoint families from all feature documents. FastAPI must expose OpenAPI docs in non-production environments and keep request/response models in Pydantic v2.

---

## 2. API Conventions

| Rule | Value |
|------|-------|
| Base path | `/api/v1` |
| Auth | Supabase JWT bearer token |
| Content type | JSON |
| Dates | ISO 8601 |
| Timezone storage | UTC |
| Error shape | `{ "error": { "code", "message", "details" } }` |
| Pagination | cursor-based where lists can grow |

---

## 3. Endpoint Families

| Family | Prefix | Source Doc |
|--------|--------|------------|
| Profiles/homes | `/profile`, `/homes` | P04 |
| Consumer accounts | `/consumer-accounts` | P06 |
| Bills | `/bills` | P06 |
| Consumption | `/consumption` | P07 |
| Estimates | `/estimates` | P08 |
| Outages | `/outages` | P09 |
| Budget | `/budget` | P10 |
| Solar | `/solar` | P11 |
| Community | `/community` | P12 |
| Complaints | `/complaints` | P13 |
| ISP | `/isp` | P14 |
| Payments | `/payments` | P15 |
| Insights | `/insights` | P17 |
| Notifications | `/notifications` | P19 |
| Admin | `/admin` | Internal |

---

## 4. Required Middleware

- request id middleware
- CORS restricted to frontend domains
- Supabase JWT auth dependency
- structured logging
- rate limiting for public endpoints
- exception handler mapping known errors to API error shape

---

## 5. Standard Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| `UNAUTHORIZED` | 401 | Missing/invalid token |
| `FORBIDDEN` | 403 | User does not own resource |
| `NOT_FOUND` | 404 | Resource missing |
| `VALIDATION_ERROR` | 422 | Invalid request |
| `PORTAL_UNAVAILABLE` | 503 | Utility portal down |
| `SCRAPER_PARSE_FAILED` | 502 | Portal changed or parse failed |
| `TARIFF_NOT_CONFIGURED` | 503 | Missing tariff data |
| `RATE_LIMITED` | 429 | Too many requests |

---

## 6. Auth Dependency

```python
async def get_current_user(authorization: str = Header(...)) -> CurrentUser:
    token = extract_bearer_token(authorization)
    claims = verify_supabase_jwt(token)
    return CurrentUser(user_id=claims["sub"], role=claims.get("role", "authenticated"))
```

Never trust user id from request body. Always use JWT user id.

---

## 7. Core Endpoints

### 7.1 Consumer Accounts

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/consumer-accounts` | List user's accounts |
| POST | `/consumer-accounts` | Create account and optional first fetch |
| PATCH | `/consumer-accounts/{id}` | Rename/deactivate |
| DELETE | `/consumer-accounts/{id}` | Soft delete |

### 7.2 Bills

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/bills` | List bills |
| GET | `/bills/{id}` | Bill detail |
| POST | `/bills/fetch/{consumer_account_id}` | On-demand fetch |
| POST | `/bills/{id}/mark-paid` | Manual paid mark |

### 7.3 Estimates

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/estimates/electricity` | Estimate electricity bill |
| POST | `/estimates/gas` | Estimate gas bill |
| POST | `/estimates/water` | Estimate water bill |
| POST | `/estimates/from-consumption/{id}` | Estimate from readings |

---

## 8. Admin Endpoints

Admin endpoints require `profiles.role = admin` or Supabase custom claim.

Admin can manage:

- tariff tables
- ISP packages
- outage schedule corrections
- scraper run logs
- monetization offers
- moderation queue

---

## 9. Testing Requirements

- Unit tests for services and estimators.
- API tests for auth/ownership enforcement.
- Contract tests for response shapes used by frontend.
- Scraper tests use saved HTML/PDF fixtures, not live portals.

---

## 10. Acceptance Criteria

- OpenAPI schema builds without errors.
- Every endpoint validates ownership.
- Every feature document has corresponding endpoint coverage.
- Error responses use standard shape.
- Public endpoints are rate-limited.
