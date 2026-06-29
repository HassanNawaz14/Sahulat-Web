# Sahulat (سہولت)

**Urdu:** "Ease / Convenience" — A comprehensive domestic utility companion for Pakistani households.

Aggregates electricity, gas, water, internet, and solar utility data into a single dashboard — enabling users to track bills, monitor consumption, get outage alerts, file complaints, manage budgets, and monitor solar systems without visiting multiple utility portals.

---

## Project Structure

```
Sahulat/
├── frontend/          # Next.js 14+ PWA (App Router)
│   ├── app/           # Route pages
│   ├── components/    # Shared UI components
│   ├── lib/           # Utilities, constants, API clients
│   ├── public/        # Static assets
│   └── styles/        # Global styles (Tailwind CSS)
├── backend/           # FastAPI (Python 3.11+)
│   ├── app/
│   │   ├── api/       # Route handlers (v1)
│   │   ├── core/      # Config, auth middleware, env
│   │   ├── scrapers/  # Utility portal scrapers
│   │   ├── jobs/      # Cron jobs (APScheduler)
│   │   └── schemas/   # Pydantic v2 schemas
│   ├── migrations/    # Database migrations
│   └── scripts/       # Utility scripts
├── docs/              # 22-part specification documents (P01–P22)
├── AGENTS.md          # AI development rules & conventions
└── README.md
```

---

## Tech Stack

| Layer    | Technology                         |
| -------- | ---------------------------------- |
| Frontend | Next.js 14+ (SSR), Tailwind CSS v3 |
| Backend  | FastAPI, Python 3.11+, Uvicorn     |
| Database | Supabase (PostgreSQL 15)           |
| Auth     | Supabase Auth (OTP, Google OAuth)  |
| Charts   | Recharts                           |
| Scraping | httpx, BeautifulSoup4, pdfplumber  |
| Notifs   | Web Push API (VAPID)               |

---

## Quick Start

```bash
# Frontend
cd frontend
npm install          # already done
npm run dev          # http://localhost:3000

# Backend
cd backend
pip install -r requirements.txt   # already done
python -m uvicorn app.main:app --reload   # http://localhost:8000
```

---

## Developer Log

| Part | Developer  | Status  | Testing            | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ---- | ---------- | ------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P01  | hassan-dev | ✅ Done | ✅ Done            | Project overview & scope defined                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| P02  | hassan-dev | ✅ Done | ✅ Done            | Stack initialized, deps installed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| P03  | hassan-dev | ✅ Done | ✅ Done            | 22 tables, RLS, triggers, seed data                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| P04  | hassan-dev | ✅ Done | ✅ Done            | Auth routes, login/verify/onboarding/settings                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| P05  | hassan-dev | ✅ Done | ✅ Done            | 16 scrapers (9 PITC DISCOs + KE + 2 gas + 2 water + 2 internet) + cron jobs. PITC discovery: `bill.pitc.com.pk` hosts ALL 9 Punjab DISCO bill portals on shared ASP.NET backend. Old LESCO portal dead (400).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| P06  | hassan-dev | ✅ Done | PTCL ❌ / LESCO ✅ | Bill Tracker: CRUD + fetch/dispatch + history + status + summary. PTCL scraper blocks non-Pakistan IPs (captcha). LESCO works end-to-end.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| P07  | hassan-dev | ✅ Done | ✅ Done            | Consumption Monitor: tariff engine, 5 API endpoints, React Query hooks, detail page (reading entry, summary, projection, split charts, appliance estimator), reading auto-fill, NEPRA tariff rates, reading delete/auto-prune, stabilization fixes, cumulative consumption rate per reading matching projection card. **Bug fixes (Jun 24):** Gas/water accounts now return `current_slab: null` and `estimated_bill: 0` instead of electricity slab data. Unit labels dynamically show kWh/MMBtu/Units per utility type. ApplianceEstimator only renders for electricity. `from-consumption` endpoint now works for gas accounts. Seasonal comparison (`same_month_last_year_units`) added to summary. |
| P08  | hassan-dev | ✅ Done | ✅ Done            | Bill Estimator: electricity/gas/water engines in `backend/app/services/estimators/`, public SEO calculator at `/estimate` with 3 sub-routes, auth estimate from consumption readings at `/consumption/[id]/estimate`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| P09 | hassan-dev | ✅ Done | ✅ Done            | Outage Tracker: migration (004_outage_schema), PDF parser with feeder→area mapping, 6 API endpoints (/schedule, /community, /reports, /feeders), frontend components (Card, Timeline, Feed, Report, FeederSelector) + React Query hooks, runner jobs (loadshedding fetch weekly, community expire 15min, confidence compute 5min). Fixed: `types/lucide-react.d.ts` needed new icon declarations for CircleAlert/CircleCheck/Search.                                                                                                                                    |
| P10 | hassan-dev | ✅ Done | 21/21 pass | Budget Manager: migration (006_budget_schema) creates `budget_categories` + `budget_expenses`; renames legacy tables to *_old. Backend: 7 endpoints + calculator service (seed, summary, category spend, budget status). Frontend: 8 React Query hooks, 5 components, /budget page. Tests: 21/21 pass. **Bug fixes (Jun 28):** Fixed undefined `month_start`, hardcoded `{month}-31` for non-31-day months, missing RLS policies & `updated_at` triggers, naive `datetime.utcnow()`. |
| P19 | hassan-dev | ✅ Done | 16/16 pass | Notifications & Alerts: migration (006_notifications_schema) creates `notification_preferences`, `push_subscriptions`, `notification_events` with RLS + trigger to seed defaults. Backend: Web Push service (VAPID, auto-cleanup on 404/410), 10 notification templates (incl. reading_reminder, complaint_followup), preference management with rate limits per category, generic scheduler + 5 API endpoints. Cron jobs for bill due, budget alerts, slab boundary. Frontend: push hooks, PermissionPrompt, PushInit, NotificationToggle settings page. PWA: manifest.json, sw.js, next-pwa config. Tests: 16/16 pass. **Bug fixes (Jun 28):** Fixed SyntaxError in cron_definitions.py, NotificationResult missing endpoint attr, broken bill/outage queries, string literal "now()" in upsert, PushInit not in layout.tsx, missing back button. **Gaps closed (Jun 29):** Added reading_reminder + complaint_followup templates, community(3/day)/solar(1/day) rate limits, mask_ref_number sanitizer. Fixed test count (8→10). |

---

## Docs Index

Full 22-part specification in `/docs/`:

| Doc | Title                           | Layer          |
| --- | ------------------------------- | -------------- |
| P01 | Project Overview                | Planning       |
| P02 | Tech Stack & Architecture       | Infrastructure |
| P03 | Database Schema                 | Data           |
| P04 | Auth & User System              | Backend        |
| P05 | Scraper System                  | Backend        |
| P06 | Bill Tracker Module (M1)        | Feature        |
| P07 | Consumption Monitor Module (M2) | Feature        |
| P08 | Bill Estimator Module (M4)      | Feature        |
| P09 | Outage Tracker Module (M3)      | Feature        |
| P10 | Budget Manager Module (M5)      | Feature        |
| P11 | Solar Dashboard Module (M6)     | Feature        |
| P12 | Community Reports Module (M10)  | Feature        |
| P13 | Complaint Assistant Module (M7) | Feature        |
| P14 | ISP Comparison Module (M9)      | Feature        |
| P15 | Pay Gateway Lite Module (M8)    | Feature        |
| P16 | Solar Sizing Tool Module (M11)  | Feature        |
| P17 | Usage Insights Module (M12)     | Feature        |
| P18 | Monetization & Affiliate System | Business       |
| P19 | Notifications & Alerts System   | Backend        |
| P20 | Frontend Architecture & PWA     | Frontend       |
| P21 | API Spec (Backend)              | Backend        |
| P22 | Deployment & DevOps             | Infrastructure |
