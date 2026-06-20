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

| Layer      | Technology                           |
|------------|--------------------------------------|
| Frontend   | Next.js 14+ (SSR), Tailwind CSS v3   |
| Backend    | FastAPI, Python 3.11+, Uvicorn       |
| Database   | Supabase (PostgreSQL 15)             |
| Auth       | Supabase Auth (OTP, Google OAuth)    |
| Charts     | Recharts                             |
| Scraping   | httpx, BeautifulSoup4, pdfplumber    |
| Notifs     | Web Push API (VAPID)                 |

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

| Part | Developer      | Status      | Notes                              |
|------|----------------|-------------|------------------------------------|
| P01  | hassan-dev     | ✅ Complete | Project overview & scope defined   |
| P02  | hassan-dev     | ✅ Complete | Stack initialized, deps installed  |
| P03  | hassan-dev     | ✅ Complete | 22 tables, RLS, triggers, seed data verified |
| P04  | opencode       | ✅ Complete | Auth routes, login/verify/onboarding/settings pages |
| P05  | opencode       | ✅ Complete | 16 scrapers (9 PITC DISCOs + KE + 2 gas + 2 water + 2 internet) + registry + cron jobs. **Key discovery:** PITC (bill.pitc.com.pk) hosts ALL 9 Punjab DISCO bill portals on same ASP.NET backend — refactored all into shared `PitcBillScraper`. Old LESCO portal (lesco.gov.pk:36269) is dead (always 400). |
| P06  | opencode       | ✅ Complete | 13 endpoints: consumer accounts CRUD + bill fetch/dispatch + history + status update + summary. Fixed: `.single()` APIError crash (returned 500 instead of 404), `KeyError: 'sub'` when JWT lacks subject claim (anon key caused crash), PITC scraper letter stripping (`13-11262-1101009-U` → `13112621101009`), wired up APScheduler on startup, frontend `/auth/verify` Suspense boundary for SSR build, cleaned imports/type hints. |

---

## Docs Index

Full 22-part specification in `/docs/`:

| Doc | Title | Layer |
|-----|-------|-------|
| P01 | Project Overview | Planning |
| P02 | Tech Stack & Architecture | Infrastructure |
| P03 | Database Schema | Data |
| P04 | Auth & User System | Backend |
| P05 | Scraper System | Backend |
| P06 | Bill Tracker Module (M1) | Feature |
| P07 | Consumption Monitor Module (M2) | Feature |
| P08 | Bill Estimator Module (M4) | Feature |
| P09 | Outage Tracker Module (M3) | Feature |
| P10 | Budget Manager Module (M5) | Feature |
| P11 | Solar Dashboard Module (M6) | Feature |
| P12 | Community Reports Module (M10) | Feature |
| P13 | Complaint Assistant Module (M7) | Feature |
| P14 | ISP Comparison Module (M9) | Feature |
| P15 | Pay Gateway Lite Module (M8) | Feature |
| P16 | Solar Sizing Tool Module (M11) | Feature |
| P17 | Usage Insights Module (M12) | Feature |
| P18 | Monetization & Affiliate System | Business |
| P19 | Notifications & Alerts System | Backend |
| P20 | Frontend Architecture & PWA | Frontend |
| P21 | API Spec (Backend) | Backend |
| P22 | Deployment & DevOps | Infrastructure |
