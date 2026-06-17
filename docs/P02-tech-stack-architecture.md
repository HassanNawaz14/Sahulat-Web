# P02 — Tech Stack & Architecture

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P01 (Project Overview)  
**Required By:** P03, P04, P05, P20, P21, P22

---

## 1. Architecture Overview

Sahulat follows a **three-tier architecture**:

```
┌─────────────────────────────────────────────────────┐
│                   CLIENT LAYER                      │
│  Next.js PWA (Vercel) — SSR + Static + Client-side  │
│  Tailwind CSS — Mobile-first responsive UI          │
└─────────────────────────┬───────────────────────────┘
                          │ HTTPS / REST + WebSocket
┌─────────────────────────▼───────────────────────────┐
│                  APPLICATION LAYER                  │
│  FastAPI (Python) — Railway.app                     │
│  All business logic, data orchestration, scraping   │
│  Cron jobs for scheduled scraping + notifications   │
└──────────┬──────────────────────────┬───────────────┘
           │                          │
┌──────────▼──────────┐   ┌──────────▼──────────────┐
│    DATA LAYER       │   │   EXTERNAL SERVICES      │
│  Supabase           │   │  DISCO portals (scrape)  │
│  PostgreSQL + Auth  │   │  SNGPL/SSGC (scrape)     │
│  Realtime           │   │  WASA portals (scrape)   │
│  Storage            │   │  Growatt ShineMonitor API│
└─────────────────────┘   │  Solis SolisCloud API    │
                          │  Huawei FusionSolar API  │
                          │  NEPRA PDF download      │
                          │  Google AdSense          │
                          └──────────────────────────┘
```

---

## 2. Technology Decisions

### 2.1 Frontend — Next.js 14+ (App Router)

| Property | Value |
|----------|-------|
| Framework | Next.js 14+ with App Router |
| Rendering | SSR for SEO-critical pages (bill estimator, ISP comparison) |
| Rendering | Static generation for tariff/content pages |
| Rendering | Client-side for dashboard, real-time data |
| Styling | Tailwind CSS v3 |
| PWA | `next-pwa` with Workbox |
| State | Zustand (global) + React Query (server state) |
| Charts | Recharts |
| Icons | Lucide React |
| Forms | React Hook Form + Zod |
| HTTP | Axios with interceptors |

**Why Next.js:** Server-side rendering is critical for SEO. Pages like "LESCO bill estimator", "load shedding schedule Lahore" have high search volume. SSR ensures Google indexes real content, not a blank React shell. PWA capability allows home screen install and push notifications without an app store.

### 2.2 Backend — FastAPI (Python 3.11+)

| Property | Value |
|----------|-------|
| Framework | FastAPI 0.110+ |
| Runtime | Python 3.11+ |
| ASGI Server | Uvicorn with Gunicorn |
| Task Queue | APScheduler (cron jobs within FastAPI process) |
| HTTP Client | httpx (async) |
| HTML Parsing | BeautifulSoup4 + lxml |
| PDF Parsing | pdfplumber |
| Browser Automation | Playwright (complaint auto-fill only) |
| Validation | Pydantic v2 |
| Auth middleware | Supabase JWT verification |

**Why FastAPI:** Async-native, Python ecosystem for scrapers, auto-generates OpenAPI docs, Pydantic for validation. The developer already has Python knowledge from BDS coursework.

### 2.3 Database — Supabase (PostgreSQL 15)

| Property | Value |
|----------|-------|
| Provider | Supabase (hosted PostgreSQL) |
| Version | PostgreSQL 15 |
| Auth | Supabase Auth (built-in) |
| Realtime | Supabase Realtime (for community reports feed) |
| Storage | Supabase Storage (for exported PDFs, cached DISCO PDFs) |
| Free Tier | 500 MB DB + 1 GB storage + 50,000 MAU |

**Row Level Security (RLS):** Enabled on all user-data tables. Users can only read/write their own records. Community reports table uses RLS policies to allow read-all but write-only-own.

### 2.4 Scraping Infrastructure — Python Scripts on Railway

| Property | Value |
|----------|-------|
| Hosting | Railway.app (free tier: 500 hours/month) |
| Scheduler | APScheduler within FastAPI OR standalone Python cron service |
| Bill scrapers | httpx + BeautifulSoup4 |
| PDF scrapers | httpx (download) + pdfplumber (parse) |
| JS-rendered portals | Playwright (headless Chromium) |
| Retry logic | tenacity library (exponential backoff) |
| Rate limiting | Respect portal rate limits; sleep 2–5s between requests |

### 2.5 Hosting

| Service | Provider | Tier | Cost |
|---------|----------|------|------|
| Frontend | Vercel | Hobby (free) | $0 |
| Backend + Scrapers | Railway.app | Starter (free) | $0 |
| Database | Supabase | Free | $0 |
| Storage | Supabase | Free (1 GB) | $0 |
| Push Notifications | Web Push API (self-hosted VAPID) | — | $0 |
| Domain | sahulat.pk or sahulat.app | — | ~$10/year |

**Total infrastructure cost at launch: ~$10/year (domain only)**

---

## 3. System Components Map

### 3.1 Frontend Pages & Route Structure

```
/                          → Landing page (SEO, install CTA)
/dashboard                 → Main dashboard (auth required)
/bills                     → Bill Tracker (M1)
/bills/[utilityType]       → Per-utility bill view
/consumption               → Consumption Monitor (M2)
/outages                   → Outage Tracker (M3)
/estimate                  → Bill Estimator (M4) [public, SEO]
/budget                    → Budget Manager (M5)
/solar                     → Solar Dashboard (M6)
/community                 → Community Reports (M10)
/complaints                → Complaint Assistant (M7)
/isp                       → ISP Comparison (M9) [public, SEO]
/solar/sizing              → Solar Sizing Tool (M11)
/settings                  → User settings, consumer numbers
/settings/profile          → Profile, city, homes
/settings/notifications    → Push notification preferences
/auth/login                → Login page
/auth/signup               → Signup page
/auth/verify               → OTP verification
/admin                     → Admin panel (internal, not public)
```

### 3.2 Backend API Structure

```
/api/v1/
  auth/           → Token validation helpers
  bills/          → Bill fetch, history
  consumption/    → Meter readings, projections
  outages/        → Schedule data, crowd reports
  estimates/      → Tariff calculator
  budget/         → Budget entries, summaries
  solar/          → Inverter data, net metering
  community/      → Report submission, feed
  complaints/     → Complaint auto-fill
  isp/            → ISP packages, comparison
  notifications/  → VAPID push, subscriptions
  admin/          → Admin-only endpoints
  webhooks/       → External service webhooks (future)
```

Full endpoint specification in **P21 — API Spec**.

### 3.3 Background Jobs (Cron Schedule)

| Job | Schedule | Description |
|-----|----------|-------------|
| `fetch_loadshedding_pdfs` | Monday 08:00 PKT | Download + parse DISCO PDFs |
| `fetch_nepra_tariffs` | 1st of month 06:00 | Check for NEPRA tariff updates |
| `fetch_ogra_tariffs` | 1st of month 06:00 | Check for OGRA tariff updates |
| `refresh_isp_packages` | Weekly Sunday | Refresh ISP package data |
| `solar_data_sync` | Every 30 min | Pull inverter data from Growatt/Solis APIs |
| `send_outage_notifications` | Every 15 min | Check upcoming outages, push alerts |
| `cleanup_old_reports` | Daily 02:00 | Remove community reports older than 24h |
| `bill_due_date_alerts` | Daily 09:00 | Alert users 3 days before bill due date |
| `slab_boundary_check` | Daily 08:00 | Check if users are near slab boundary |

---

## 4. Data Flow Diagrams

### 4.1 Bill Fetch Flow

```
User adds consumer number
        ↓
Frontend → POST /api/v1/bills/fetch
        ↓
Backend: Identify DISCO/utility from consumer number format
        ↓
Scraper: HTTP request to DISCO portal (httpx)
        ↓
Parser: BeautifulSoup4 extracts bill fields
        ↓
Store: Insert into `bills` table (Supabase)
        ↓
Return: Bill data + trend comparison to frontend
        ↓
Frontend: Display bill card + 6-month trend graph
```

### 4.2 Load Shedding Schedule Flow

```
Monday cron job triggers
        ↓
Scraper downloads PDF from DISCO website
        ↓
pdfplumber extracts feeder-wise schedule table
        ↓
Parser maps feeder names → area names (lookup table)
        ↓
Store: Upsert into `outage_schedules` table
        ↓
Notification job: Check users whose feeder has outage in next 30 min
        ↓
Web Push: Send push notification to subscribed users
```

### 4.3 Crowd-sourced Outage Report Flow

```
User taps "Report Outage" button
        ↓
Frontend: Gets user's city/area from profile
        ↓
POST /api/v1/community/report
        ↓
Backend: Insert report with timestamp, area, utility type
        ↓
Supabase Realtime: Broadcasts to all subscribers in same area
        ↓
Frontend: Live counter updates on Community Reports feed
        ↓
Cron (every 15 min): Aggregate reports → if N reports in same area in 30 min → push notification to nearby users
```

---

## 5. Security Architecture

### 5.1 Authentication Flow
- Supabase Auth handles all authentication
- Supported methods: Email + OTP, Google OAuth, Phone (OTP via SMS — Supabase built-in)
- JWT tokens issued by Supabase, validated by FastAPI middleware on every protected request
- Token expiry: 1 hour (access) + 7 days (refresh)

### 5.2 Data Security
- All user data tables have RLS enabled — no user can query another user's data
- Consumer numbers stored encrypted in DB (AES-256 via Supabase Vault or application-level encryption)
- ISP credentials (if stored for bill fetch) stored encrypted, never logged
- HTTPS enforced everywhere (Vercel + Railway both enforce SSL)

### 5.3 Scraper Ethics
- Scrapers only hit public bill-check endpoints (no login bypass)
- Rate limiting: max 1 request per 3 seconds per DISCO portal
- User-Agent set to a real browser string
- No caching bypass, no CAPTCHA bypass — if portal adds CAPTCHA, fall back to manual entry

### 5.4 Input Validation
- All API inputs validated via Pydantic v2 schemas
- Consumer number formats validated before scraping (regex per DISCO)
- SQL injection: Not possible — Supabase uses parameterized queries via PostgREST
- XSS: Next.js escapes all rendered content by default; additional sanitization on community report text

---

## 6. Environment Variables

### Frontend (Vercel)
```env
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_BASE_URL=
NEXT_PUBLIC_VAPID_PUBLIC_KEY=
NEXT_PUBLIC_GA_MEASUREMENT_ID=
NEXT_PUBLIC_ADSENSE_CLIENT_ID=
```

### Backend (Railway)
```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
VAPID_PRIVATE_KEY=
VAPID_PUBLIC_KEY=
VAPID_EMAIL=
GROWATT_API_KEY=
SOLIS_API_KEY=
SOLIS_API_SECRET=
HUAWEI_API_KEY=
ENCRYPTION_KEY=
ADMIN_SECRET_KEY=
RAILWAY_ENVIRONMENT=production
```

---

## 7. Scalability Plan

The free tier infrastructure supports approximately 10,000 MAU. When traffic exceeds this:

| Threshold | Action |
|-----------|--------|
| 500 MB DB | Upgrade Supabase to Pro ($25/mo) — adds 8 GB |
| 500 hrs/mo Railway | Upgrade Railway to Starter ($5/mo) |
| Vercel bandwidth | Upgrade to Vercel Pro ($20/mo) if needed |
| Scraper rate limits | Add proxy rotation (Bright Data or Oxylabs) |

Revenue from AdSense should cover infrastructure upgrades before limits are hit.

---

## 8. Third-Party API Summary

| API | Purpose | Auth Method | Rate Limit | Cost |
|-----|---------|-------------|------------|------|
| Growatt ShineMonitor | Solar inverter data | API Key | 100 req/min | Free |
| Solis SolisCloud | Solar inverter data | API Key + HMAC | 100 req/min | Free |
| Huawei FusionSolar | Solar inverter data | OAuth2 | 100 req/min | Free |
| Supabase Auth | Authentication | JWT | — | Free |
| Supabase Realtime | Live community feed | WebSocket | — | Free |
| Google AdSense | Monetization | Script embed | — | Free |
| Web Push (VAPID) | Notifications | VAPID keys | — | Free |
| Google Analytics | Usage analytics | Script embed | — | Free |
