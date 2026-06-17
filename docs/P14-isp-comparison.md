# P14 — ISP Comparison Module (M9)

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P02 (Tech Stack), P03 (Database Schema), P04 (Auth), P05 (Scraper System), P12 (Community Reports)  
**Required By:** P18 (Monetization), P20 (Frontend), P21 (API Spec)

---

## 1. Scope

ISP Comparison helps users compare internet packages by city, area, provider, speed, price, reliability, and community outage score. It is a V2 SEO and affiliate module. Public pages should capture searches like "best internet in Lahore DHA" and convert high-intent users into ISP referral leads.

Data is mostly admin-maintained because Pakistani ISPs do not expose clean package APIs.

---

## 2. Providers

| Provider | Coverage | V1/V2 |
|----------|----------|-------|
| PTCL | Nationwide | V2 |
| Nayatel | Islamabad, Rawalpindi, Faisalabad, Peshawar | V2 |
| StormFiber | Lahore, Karachi, Islamabad, Faisalabad, Multan | V2 |
| Transworld | Major cities | V2 |
| Optix | Major cities | V2 |
| Jazz Home | Selected cities | V2 |
| Zong Home | Selected cities | V2 |

---

## 3. User-Facing Features

| Feature | Priority | Description |
|---------|----------|-------------|
| Package comparison | P2 | Compare monthly price, speed, installation cost |
| City/area filtering | P2 | Show only providers available in area |
| Reliability score | P2 | Based on community outage reports and ratings |
| User rating | P2 | Speed, support, uptime, value |
| Lead form | P2 | User requests connection callback |
| Public SEO pages | P2 | Indexable city/provider pages |
| Affiliate tracking | P2 | Track outbound referral and verified lead |

---

## 4. Data Model

Add if absent from P03:

```sql
CREATE TABLE public.isp_packages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_code TEXT NOT NULL,
  city TEXT NOT NULL,
  area TEXT,
  package_name TEXT NOT NULL,
  download_mbps INTEGER NOT NULL,
  upload_mbps INTEGER,
  monthly_price NUMERIC(10,2) NOT NULL,
  installation_fee NUMERIC(10,2),
  data_cap_gb INTEGER,
  is_active BOOLEAN DEFAULT TRUE,
  affiliate_url TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.isp_reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  provider_code TEXT NOT NULL,
  city TEXT NOT NULL,
  area TEXT,
  rating_overall INTEGER CHECK (rating_overall BETWEEN 1 AND 5),
  rating_speed INTEGER CHECK (rating_speed BETWEEN 1 AND 5),
  rating_support INTEGER CHECK (rating_support BETWEEN 1 AND 5),
  note TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.isp_leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
  provider_code TEXT NOT NULL,
  package_id UUID REFERENCES isp_packages(id) ON DELETE SET NULL,
  city TEXT NOT NULL,
  area TEXT,
  phone TEXT NOT NULL,
  status TEXT DEFAULT 'new',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 5. Frontend Routes

| Route | Purpose |
|-------|---------|
| `/isp` | Public comparison landing |
| `/isp/[city]` | City packages |
| `/isp/[city]/[area]` | Area availability |
| `/isp/provider/[provider]` | Provider profile |
| `/isp/lead/[packageId]` | Connection request flow |

---

## 6. Ranking Algorithm

Default sort score:

```text
score = (speed_value_score * 0.35)
      + (price_score * 0.25)
      + (reliability_score * 0.25)
      + (review_score * 0.15)
```

Reliability score uses P12 reports:

```text
reliability_score = 100 - normalized_outage_reports_per_100_users
```

If community data is insufficient, show "Not enough local reports" instead of a fake score.

---

## 7. API Contracts

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/isp/packages` | GET | Filter packages |
| `/api/v1/isp/providers/{code}` | GET | Provider profile |
| `/api/v1/isp/reviews` | POST | Add review |
| `/api/v1/isp/leads` | POST | Create referral lead |
| `/api/v1/isp/admin/packages` | POST/PUT | Admin package management |

---

## 8. Monetization Rules

- Affiliate/referral links must use tracked URLs.
- Lead form requires explicit user consent.
- Provider-sponsored ranking is not allowed in V1; if introduced later, sponsored placement must be labelled.
- Ads can appear after comparison results, not before the first useful package list.

---

## 9. Acceptance Criteria

- Public ISP pages are indexable.
- Packages can be filtered by city and area.
- Users can submit ratings.
- Lead records are created with provider and package attribution.
- Reliability score uses community data only when enough data exists.
