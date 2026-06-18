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
└── docs/              # 22-part specification documents (P01–P22)
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

## Developer Log

| Part | Developer      | Status      | Notes                              |
|------|----------------|-------------|------------------------------------|
| P01  | hassan-dev     | ✅ Complete | Project overview & scope defined   |
| P02  | hassan-dev     | 🔄 In Progress | Tech stack, architecture, setup  |

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

---

*Initialized by hassan-dev — moving from P01 to P02.*
