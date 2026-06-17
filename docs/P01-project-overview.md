# P01 — Project Overview

**Document Type:** Rigid Plan  
**Status:** Authoritative — do not deviate without versioning this document  
**Depends On:** None  
**Required By:** All other documents

---

## 1. Project Identity

| Field | Value |
|-------|-------|
| **Name** | Sahulat (سہولت) |
| **Meaning** | Urdu — "ease / convenience" |
| **Target Domain** | `sahulat.pk` (primary) or `sahulat.app` (fallback) |
| **Type** | Progressive Web Application (PWA) |
| **Primary Market** | Pakistan — all major cities |
| **Language** | English UI (Urdu labels where culturally necessary) |

---

## 2. Mission Statement

Sahulat is a comprehensive domestic utility companion for Pakistani households. It aggregates electricity, gas, water, and internet utility data into a single dashboard — enabling users to track bills, monitor consumption, get outage alerts, file complaints, manage budgets, and monitor solar systems — without needing to visit multiple utility portals.

The product is designed for **maximum daily stickiness**: users should open Sahulat 3–5 times per day (bill check, outage alert, budget update, solar check), creating a high-impression, high-retention base that directly monetizes through advertising and affiliate revenue.

---

## 3. Core Problem Being Solved

Pakistani households deal with:
- Multiple utility portals with poor UX to check bills
- No consolidated view of total utility spending
- No warning before crossing electricity tariff slab boundaries (costs hundreds of rupees)
- Unpredictable load shedding with no advance notification
- No unified complaint system across NEPRA, OGRA, PTA, WASA
- No tool that aggregates solar production with grid consumption
- Fragmented ISP package information across cities

Sahulat solves all of the above in one installable web app.

---

## 4. Target Users

### Primary User Persona
- **Age:** 22–45
- **Location:** Urban Pakistan (Lahore, Karachi, Islamabad, Faisalabad, Rawalpindi, Multan, Peshawar)
- **Device:** Android smartphone (primary), desktop (secondary)
- **Tech literacy:** Moderate — uses WhatsApp, can install a PWA
- **Utility situation:** Pays electricity + gas bills, likely has load shedding, may have solar

### Secondary User Persona
- **Solar owners** — growing rapidly; 17,000+ MW installed in homes in 2023–24
- **Multi-property owners** — track bills for home + rental property
- **Small business owners** — track utility costs as business expense

---

## 5. Product Scope — V1 (Core Modules)

These modules must be complete before public launch:

| Module ID | Name | Priority |
|-----------|------|----------|
| M1 | Bill Tracker | P0 |
| M2 | Consumption Monitor | P0 |
| M3 | Outage Tracker | P0 |
| M4 | Bill Estimator | P0 |
| M5 | Budget Manager | P1 |
| M6 | Solar Dashboard | P1 |

See individual module documents (P06–P11) for full specifications.

---

## 6. Product Scope — V2 (Secondary Modules)

Build after first public users are acquired:

| Module ID | Name | Priority |
|-----------|------|----------|
| M7 | Complaint Assistant | P2 |
| M8 | Pay Gateway Lite | P2 |
| M9 | ISP Comparison | P2 |
| M10 | Community Reports | P2 |
| M11 | Solar Sizing Tool | P3 |
| M12 | Usage Insights | P3 |

---

## 7. Utility Coverage

### Electricity
- **Providers:** LESCO, GEPCO, FESCO, MEPCO, IESCO, PESCO, QESCO, HESCO, SEPCO, K-Electric (all 10 DISCOs)
- **V1 Priority:** LESCO (Lahore) first — most consistent data; K-Electric (Karachi) second
- **Bill fetch:** Public URL scraping by consumer reference number. No login required.
- **Tariff authority:** NEPRA (nepra.org.pk) — updated quarterly
- **Load shedding:** Weekly PDF published by each DISCO every Monday — parsed automatically

### Gas
- **Providers:** SNGPL (North Pakistan), SSGC (South/Sindh)
- **Bill fetch:** sngpl.com.pk and ssgc.com.pk — public lookup by consumer number
- **Tariff authority:** OGRA (ogra.org.pk) — updated quarterly
- **Supply schedule:** Scraped from SNGPL/SSGC announcements + crowd-sourced

### Water
- **Providers V1:** WASA Lahore (wasa.punjab.gov.pk), KW&SB Karachi (kwsb.org.pk)
- **Providers V2:** WASA Rawalpindi, WASA Faisalabad, WASA Multan
- **Bill fetch:** Public portal scraping by consumer number
- **Supply schedule:** Manual admin entry + crowd-sourced (no machine-readable public source)
- **Meter reading:** Manual entry by user; app calculates consumption and projects bill

### Internet
- **Providers:** PTCL, Nayatel, StormFiber, Jazz Home, Zong Home
- **Bill fetch:** PTCL and Nayatel via public portals; others via stored user credentials (secured)
- **Package comparison:** Static, regularly-updated dataset — admin-maintained
- **Outage tracking:** Crowd-sourced only (no ISP publishes outage data)

### Solar
- **Inverter brands supported:** Growatt (priority — most common in Pakistan), Solis, Huawei FusionSolar
- **API:** Each brand has a free API (ShineMonitor, SolisCloud, FusionSolar)
- **Net metering:** NEPRA policy — Rs. 27/unit exported back to grid
- **ROI tracking:** User-entered system cost vs accumulated monthly savings

### Cable TV
- **Scope:** Manual expense entry only — included in Budget Manager (M5) as a category
- **No dedicated module** — 90% of Pakistani cable TV is informal with no digital presence

### Mobile Data
- **Scope:** Manual expense entry only — no public API exists for Jazz/Zong/Telenor
- **Future:** USSD-based balance check automation (V3 consideration)

---

## 8. Key Differentiating Features

1. **Slab Boundary Alert** — "You've used 290 units. 10 more units will push you into the next slab and cost Rs. 800 extra." No existing Pakistani app has this.
2. **Unified Bill Dashboard** — All utilities in one view with monthly trend graphs
3. **Crowd-sourced Outage Map** — Real-time unscheduled outages reported by users, mapped hyperlocally
4. **Solar + Grid Integration** — See production vs consumption side-by-side with savings calculation
5. **One-Tap Complaint Filing** — User profile pre-fills NEPRA/OGRA/PTA complaint forms automatically
6. **Budget Projection** — Project end-of-month utility cost before the bill arrives
7. **Panel Health Alerts** — Detect underperforming solar panels via production baseline comparison
8. **ISP Package Comparison** — Only tool that compares ISP packages by area with real-world crowd ratings

---

## 9. Monetization Strategy (Summary)

Full detail in **P18 — Monetization & Affiliate System**.

| Stream | Timeline | Notes |
|--------|----------|-------|
| Google AdSense | Day 1 (post-approval) | Primary revenue. High session frequency = high impressions. |
| Daraz Affiliate | V1 | Link UPS, inverter, battery, solar product recommendations |
| Solar Vendor Leads | V2 | Rs. 3,000–10,000 per lead to solar installers |
| ISP Referral | V2 | Commission per verified ISP signup via Sahulat |
| Premium Tier | V2–V3 | Rs. 99/month: SMS alerts, bill history export, multi-home |

---

## 10. Build Roadmap (Summary)

Full detail in individual part documents. High-level timeline:

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1 | Week 1–2 | Data layer: scrapers, DB schema, cron jobs |
| Phase 2 | Week 3 | Frontend MVP: Dashboard, Bill View, Outage screen |
| Phase 3 | Week 4 | Engagement: Push notifications, slab alerts, outage reporting |
| Phase 4 | Week 5 | Budget Manager + Bill Estimator |
| Phase 5 | Week 6 | Solar Dashboard + AdSense live |
| Phase 6 | Post-launch | Remaining DISCOs, V2 modules, affiliate onboarding |

---

## 11. Out of Scope (All Versions)

- Actual bill payment processing (requires JazzCash/EasyPaisa merchant account + business registration)
- Water quality monitoring (no public data in Pakistan)
- Mobile data balance via carrier API (no public API)
- Smart meter integration (infrastructure not yet deployed at scale)
- Cable TV dedicated module

---

## 12. Success Metrics (V1)

| Metric | Target (3 months post-launch) |
|--------|-------------------------------|
| Registered users | 5,000 |
| DAU/MAU ratio | ≥ 40% (stickiness) |
| Consumer numbers linked | ≥ 8,000 (avg 1.6 per user) |
| Push notification opt-in rate | ≥ 60% |
| AdSense impressions/day | ≥ 50,000 |
| Monthly AdSense revenue | ≥ PKR 15,000 |

---

## 13. Document Index (All Parts)

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
