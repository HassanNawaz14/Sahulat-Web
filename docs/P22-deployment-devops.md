# P22 — Deployment & DevOps

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P02 (Tech Stack), P03 (Database Schema), P05 (Scraper System), P19 (Notifications), P20 (Frontend), P21 (API Spec)  
**Required By:** All production operations

---

## 1. Scope

This document defines deployment, environments, CI/CD, secrets, cron jobs, database migrations, backups, monitoring, and operational rules for Sahulat.

V1 target cost is near-zero: Vercel free tier, Railway free/starter tier, Supabase free tier, domain only paid.

---

## 2. Environments

| Environment | Purpose | Services |
|-------------|---------|----------|
| Local | Developer machine | Local Next.js/FastAPI, Supabase cloud dev |
| Staging | Pre-production testing | Vercel preview, Railway staging, Supabase staging |
| Production | Public users | Vercel prod, Railway prod, Supabase prod |

Production data must never be used in local development unless anonymized.

---

## 3. Repositories

Recommended monorepo:

```
/
  frontend/
  backend/
  supabase/
    migrations/
    seed/
  docs/
  scripts/
```

---

## 4. Deployment Targets

| Component | Target | Notes |
|-----------|--------|-------|
| Frontend | Vercel | Next.js PWA |
| Backend API | Railway | FastAPI + Uvicorn/Gunicorn |
| Cron jobs | Railway | APScheduler or separate worker process |
| Database | Supabase | PostgreSQL + Auth + Storage |
| Storage | Supabase | Cached PDFs, exports, avatars |
| Domain | `sahulat.pk` | Primary |

---

## 5. Environment Variables

### Frontend

```env
NEXT_PUBLIC_APP_URL=
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_BASE_URL=
NEXT_PUBLIC_VAPID_PUBLIC_KEY=
NEXT_PUBLIC_ADSENSE_CLIENT_ID=
```

### Backend

```env
APP_ENV=
DATABASE_URL=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
ENCRYPTION_KEY=
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
RAILWAY_ENVIRONMENT=
SENTRY_DSN=
```

Never expose service role key to frontend.

---

## 6. CI/CD

Required checks before merge:

| Area | Command |
|------|---------|
| Frontend lint | `npm run lint` |
| Frontend build | `npm run build` |
| Backend tests | `pytest` |
| Backend type/format | `ruff check` |
| Migrations | dry-run migration check |

Deployment:

- main branch deploys production
- pull requests create Vercel preview
- Railway deploys backend on main only

---

## 7. Cron Jobs

| Job | Schedule | Owner |
|-----|----------|-------|
| Refresh bills | Daily 07:00 PKT | P06 |
| Parse load shedding PDFs | Monday 09:00 PKT | P09 |
| Notification scheduler | Every 5 min | P19 |
| Slab boundary check | Daily 20:00 PKT | P07 |
| Solar sync | Every 30 min daytime | P11 |
| Expire community reports | Every 15 min | P12 |
| Tariff freshness check | Weekly | P08 |

Cron job failures must log to `scraper_runs` or operational logs and alert admin after repeated failure.

---

## 8. Backups

Supabase free tier limitations require manual discipline.

Minimum backup plan:

- weekly `pg_dump` once users exist
- monthly off-platform encrypted backup
- export docs and migrations in git
- never rely only on dashboard state

---

## 9. Monitoring

Track:

- backend uptime
- API error rate
- scraper failure rate by provider
- bill fetch latency
- push notification failures
- database size vs Supabase limit
- Vercel build failures

Use Sentry or a free equivalent when possible.

---

## 10. Release Process

1. Update docs if behavior changes.
2. Run tests locally.
3. Merge to main.
4. Verify Vercel and Railway deployments.
5. Run smoke tests:
   - login
   - add/fetch LESCO bill
   - estimator
   - outage page
   - push test in staging
6. Monitor logs for 30 minutes after release.

---

## 11. Acceptance Criteria

- Production deploy can be reproduced from git.
- Secrets are stored only in platform secret managers.
- Migrations are versioned.
- Cron jobs are documented and observable.
- Rollback path exists for frontend and backend.
