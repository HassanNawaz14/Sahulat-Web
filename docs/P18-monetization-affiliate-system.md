# P18 — Monetization & Affiliate System

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P01 (Project Overview), P10 (Budget Manager), P11 (Solar Dashboard), P14 (ISP Comparison), P16 (Solar Sizing Tool), P17 (Usage Insights)  
**Required By:** P20 (Frontend), P21 (API Spec), P22 (Deployment & DevOps)

---

## 1. Scope

This document defines how Sahulat earns money without damaging user trust. Monetization starts with ads and affiliate links, then expands into solar vendor leads, ISP referrals, and optional premium features. The product goal is high daily utility, not one-time traffic.

Monetization must be contextual. A user checking an urgent outage must not be blocked by ads or popups.

---

## 2. Revenue Streams

| Stream | Timeline | Priority | Notes |
|--------|----------|----------|-------|
| Google AdSense | Launch | P0 | Primary early revenue |
| Daraz Affiliate | V1 | P1 | UPS, batteries, appliances, solar accessories |
| Solar vendor leads | V2 | P1 | Highest-value lead stream |
| ISP referrals | V2 | P2 | From ISP Comparison |
| Premium tier | V2/V3 | P2 | Rs. 99/month target |
| Sponsored placements | V3 | P3 | Must be labelled |

---

## 3. Ad Placement Rules

Allowed placements:

- below bill detail breakdown
- below estimator result
- between community feed items after item 3
- bottom of budget dashboard
- ISP comparison sidebar/below results

Forbidden placements:

- above critical form inputs
- inside payment flow
- inside complaint submission confirmation
- over outage status/countdown
- as intrusive interstitials on PWA launch

---

## 4. Affiliate Triggers

| Trigger | Module | Offer Type |
|---------|--------|------------|
| High electricity bill | P06/P10/P17 | UPS, inverter, energy saver |
| Slab risk | P07/P08 | Energy-saving tips/products |
| Solar sizing result | P16 | Solar vendor lead |
| Solar maintenance alert | P11 | Cleaning/vendor lead |
| Internet package comparison | P14 | ISP referral |
| Budget overspend | P10 | Relevant module deep link, not random ads |

---

## 5. Tracking Model

Add tables if absent:

```sql
CREATE TABLE public.affiliate_clicks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
  source_module TEXT NOT NULL,
  offer_code TEXT NOT NULL,
  destination_url TEXT NOT NULL,
  context JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.vendor_leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
  lead_type TEXT NOT NULL,
  city TEXT NOT NULL,
  area TEXT,
  phone TEXT NOT NULL,
  status TEXT DEFAULT 'new',
  estimated_value NUMERIC(10,2),
  context JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 6. Premium Tier

Target price: Rs. 99/month.

Premium features candidates:

| Feature | Module |
|---------|--------|
| PDF/CSV bill history export | P06/P10 |
| More than 10 consumer accounts | P04/P06 |
| Multi-home advanced reports | P04/P10 |
| SMS outage alerts | P19 |
| Ad-light experience | P20 |
| Long-term history retention | P03/P22 |

Do not build premium payment until actual payment partnerships are feasible. Premium can be feature-flagged first.

---

## 7. Consent and Trust Rules

- Label affiliate links where required.
- Solar/ISP leads require explicit consent.
- Never sell user consumer numbers.
- Never expose exact address to vendors unless user confirms.
- Ads must not imply endorsement by DISCO, NEPRA, OGRA, PTA, or WASA.

---

## 8. Metrics

| Metric | Target |
|--------|--------|
| Ad impressions per DAU | 5-10 |
| Affiliate CTR | 1.5%+ |
| Solar lead conversion from sizing tool | 3%+ |
| ISP lead conversion from comparison | 2%+ |
| Premium conversion | 1%+ of active users |

---

## 9. Acceptance Criteria

- Ad slots are defined and feature-flagged.
- Affiliate clicks are tracked.
- Lead forms require consent.
- Monetization never blocks critical utility information.
- Premium feature list is enforced by backend flags, not frontend only.
