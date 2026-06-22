# P03 — Database Schema

**Document Type:** Rigid Plan  
**Status:** Authoritative  
**Depends On:** P01 (Project Overview), P02 (Tech Stack)  
**Required By:** P04, P05, P06, P07, P08, P09, P10, P11, P12, P13, P14, P21

---

## 1. Overview

All data is stored in **Supabase (PostgreSQL 15)**. Row Level Security (RLS) is enabled on every table that contains user data. All timestamps are stored in UTC; conversion to PKT (UTC+5) happens at the application layer.

**Naming conventions:**
- Table names: `snake_case`, plural
- Column names: `snake_case`
- Foreign keys: `{referenced_table_singular}_id`
- Timestamps: `created_at`, `updated_at` (auto-managed)
- Soft deletes: `deleted_at TIMESTAMPTZ NULL` where applicable

---

## 2. Schema: Users & Auth

### 2.1 `profiles`
Extends Supabase Auth `auth.users`. Created automatically via trigger on signup.

```sql
CREATE TABLE public.profiles (
  id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name       TEXT,
  phone           TEXT UNIQUE,
  city            TEXT,                        -- e.g. 'lahore', 'karachi'
  area            TEXT,                        -- e.g. 'dha-phase-5', 'gulberg'
  preferred_lang  TEXT DEFAULT 'en',           -- 'en' | 'ur'
  premium         BOOLEAN DEFAULT FALSE,
  premium_until   TIMESTAMPTZ,
  avatar_url      TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
```

### 2.2 `homes`
Supports multi-property tracking (user can have home + rental unit).

```sql
CREATE TABLE public.homes (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,                   -- e.g. 'Home', 'Office', 'Rental'
  address     TEXT,
  city        TEXT NOT NULL,
  area        TEXT,
  is_default  BOOLEAN DEFAULT FALSE,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_homes_user_id ON homes(user_id);

ALTER TABLE homes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own homes" ON homes FOR ALL USING (auth.uid() = user_id);
```

---

## 3. Schema: Consumer Numbers & Utilities

### 3.1 `consumer_accounts`
Maps a user's home to one or more utility consumer accounts.

```sql
CREATE TABLE public.consumer_accounts (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  home_id             UUID REFERENCES homes(id) ON DELETE SET NULL,
  utility_type        TEXT NOT NULL,           -- 'electricity' | 'gas' | 'water' | 'internet'
  provider_code       TEXT NOT NULL,           -- 'lesco' | 'gepco' | 'sngpl' | 'wasa_lhr' | 'ptcl' | etc.
  consumer_number     TEXT NOT NULL,           -- Encrypted at application layer before storage
  provider_reference  TEXT,                    -- Encrypted provider-specific reference (e.g. PTCL Account ID)
  account_label       TEXT,                    -- User-defined: 'Main Meter', 'Solar Meter'
  is_active           BOOLEAN DEFAULT TRUE,
  last_fetched_at     TIMESTAMPTZ,
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, utility_type, provider_code, consumer_number)
);

CREATE INDEX idx_consumer_accounts_user ON consumer_accounts(user_id);
CREATE INDEX idx_consumer_accounts_provider ON consumer_accounts(provider_code);

ALTER TABLE consumer_accounts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own consumer accounts" ON consumer_accounts FOR ALL USING (auth.uid() = user_id);
```

**Provider codes reference:**

| Code | Utility | Region |
|------|---------|--------|
| `lesco` | Electricity | Lahore |
| `gepco` | Electricity | Gujranwala |
| `fesco` | Electricity | Faisalabad |
| `mepco` | Electricity | Multan |
| `iesco` | Electricity | Islamabad |
| `pesco` | Electricity | Peshawar |
| `qesco` | Electricity | Quetta |
| `hesco` | Electricity | Hyderabad |
| `sepco` | Electricity | Sukkur |
| `kelectric` | Electricity | Karachi |
| `sngpl` | Gas | North Pakistan |
| `ssgc` | Gas | South/Sindh |
| `wasa_lhr` | Water | Lahore |
| `kwsb` | Water | Karachi |
| `wasa_rwp` | Water | Rawalpindi |
| `ptcl` | Internet | Nationwide |
| `nayatel` | Internet | Islamabad/Rawalpindi |
| `stormfiber` | Internet | Lahore/Karachi |

---

## 4. Schema: Bills

### 4.1 `bills`
Stores fetched bill records. One row per bill per consumer account per month.

```sql
CREATE TABLE public.bills (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  consumer_account_id   UUID NOT NULL REFERENCES consumer_accounts(id) ON DELETE CASCADE,
  user_id               UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  billing_month         DATE NOT NULL,         -- First day of billing month: 2025-06-01
  issue_date            DATE,
  due_date              DATE,
  amount_payable        NUMERIC(10,2) NOT NULL,
  units_consumed        NUMERIC(10,2),         -- kWh for electricity, MMBtu for gas, gallons for water
  previous_reading      NUMERIC(10,2),
  current_reading       NUMERIC(10,2),
  arrears               NUMERIC(10,2) DEFAULT 0,
  taxes                 NUMERIC(10,2) DEFAULT 0,
  surcharges            NUMERIC(10,2) DEFAULT 0,
  meter_rent            NUMERIC(10,2) DEFAULT 0,
  fc_surcharge          NUMERIC(10,2) DEFAULT 0,   -- Electricity: fuel cost adjustment
  tariff_slab           TEXT,                   -- e.g. '201-300' for electricity
  status                TEXT DEFAULT 'unpaid',  -- 'unpaid' | 'paid' | 'overdue'
  raw_data              JSONB,                  -- Full scraped response for debugging
  fetch_source          TEXT DEFAULT 'scraper', -- 'scraper' | 'manual'
  created_at            TIMESTAMPTZ DEFAULT NOW(),
  updated_at            TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(consumer_account_id, billing_month)
);

CREATE INDEX idx_bills_user_id ON bills(user_id);
CREATE INDEX idx_bills_consumer_account ON bills(consumer_account_id);
CREATE INDEX idx_bills_billing_month ON bills(billing_month);
CREATE INDEX idx_bills_due_date ON bills(due_date);

ALTER TABLE bills ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users view own bills" ON bills FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "System inserts bills" ON bills FOR INSERT WITH CHECK (auth.uid() = user_id);
```

---

## 5. Schema: Consumption (Meter Readings)

### 5.1 `meter_readings`
Manual meter reading entries by user.

```sql
CREATE TABLE public.meter_readings (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  consumer_account_id   UUID NOT NULL REFERENCES consumer_accounts(id) ON DELETE CASCADE,
  user_id               UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  reading_date          DATE NOT NULL,
  reading_value         NUMERIC(10,2) NOT NULL,
  units_since_last      NUMERIC(10,2),         -- Computed: current - previous reading
  estimated_bill        NUMERIC(10,2),         -- Computed using current tariff slabs
  notes                 TEXT,
  created_at            TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(consumer_account_id, reading_date)
);

CREATE INDEX idx_meter_readings_consumer ON meter_readings(consumer_account_id, reading_date DESC);
CREATE INDEX idx_meter_readings_user ON meter_readings(user_id);

ALTER TABLE meter_readings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own readings" ON meter_readings FOR ALL USING (auth.uid() = user_id);
```

### 5.2 `slab_alerts`
Tracks when users have been alerted about approaching slab boundaries (prevents duplicate alerts).

```sql
CREATE TABLE public.slab_alerts (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  consumer_account_id   UUID NOT NULL REFERENCES consumer_accounts(id) ON DELETE CASCADE,
  user_id               UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  billing_period        DATE NOT NULL,         -- Start of current billing month
  slab_threshold        INTEGER NOT NULL,      -- e.g. 300 (next slab starts at 300 units)
  units_at_alert        NUMERIC(10,2) NOT NULL,
  cost_if_crossed       NUMERIC(10,2),         -- Estimated extra cost if slab crossed
  alerted_at            TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(consumer_account_id, billing_period, slab_threshold)
);

ALTER TABLE slab_alerts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users view own slab alerts" ON slab_alerts FOR SELECT USING (auth.uid() = user_id);
```

---

## 6. Schema: Outage Data

### 6.1 `outage_schedules`
Scheduled load shedding parsed from DISCO PDFs. Admin/system-written, public-readable.

```sql
CREATE TABLE public.outage_schedules (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_code   TEXT NOT NULL,               -- 'lesco', 'gepco', etc.
  feeder_code     TEXT NOT NULL,               -- e.g. 'F-201'
  feeder_name     TEXT NOT NULL,               -- e.g. 'Model Town Feeder'
  area_tags       TEXT[],                      -- e.g. ['model-town', 'gulberg']
  city            TEXT NOT NULL,
  schedule_date   DATE NOT NULL,
  slots           JSONB NOT NULL,              -- [{"start": "06:00", "end": "08:00", "duration_hrs": 2}, ...]
  week_start      DATE NOT NULL,               -- Monday of the week this schedule covers
  source_pdf_url  TEXT,
  parsed_at       TIMESTAMPTZ DEFAULT NOW(),
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(provider_code, feeder_code, schedule_date)
);

CREATE INDEX idx_outage_schedules_city_date ON outage_schedules(city, schedule_date);
CREATE INDEX idx_outage_schedules_provider ON outage_schedules(provider_code, schedule_date);
CREATE INDEX idx_outage_schedules_area ON outage_schedules USING GIN(area_tags);

-- No RLS needed — public data
```

### 6.2 `community_outage_reports`
Crowd-sourced real-time outage reports by users.

```sql
CREATE TABLE public.community_outage_reports (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES profiles(id) ON DELETE SET NULL,  -- Nullable for anonymous
  utility_type    TEXT NOT NULL,               -- 'electricity' | 'gas' | 'water' | 'internet'
  provider_code   TEXT,
  city            TEXT NOT NULL,
  area            TEXT NOT NULL,
  area_slug       TEXT NOT NULL,               -- URL-safe: 'dha-phase-5'
  latitude        NUMERIC(10,7),               -- Optional GPS
  longitude       NUMERIC(10,7),
  description     TEXT,                        -- Optional user note
  is_restored     BOOLEAN DEFAULT FALSE,
  restored_at     TIMESTAMPTZ,
  upvotes         INTEGER DEFAULT 0,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  expires_at      TIMESTAMPTZ DEFAULT NOW() + INTERVAL '6 hours'
);

CREATE INDEX idx_outage_reports_area ON community_outage_reports(city, area_slug, created_at DESC);
CREATE INDEX idx_outage_reports_utility ON community_outage_reports(utility_type, city);
CREATE INDEX idx_outage_reports_expires ON community_outage_reports(expires_at);

ALTER TABLE community_outage_reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read reports" ON community_outage_reports FOR SELECT USING (TRUE);
CREATE POLICY "Auth users can insert" ON community_outage_reports FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "Users update own reports" ON community_outage_reports FOR UPDATE USING (auth.uid() = user_id);
```

---

## 7. Schema: Tariffs

### 7.1 `electricity_tariffs`
NEPRA-published tariff slabs. Admin-maintained, updated quarterly.

```sql
CREATE TABLE public.electricity_tariffs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  effective_date  DATE NOT NULL,
  category        TEXT NOT NULL DEFAULT 'residential', -- 'residential' | 'commercial'
  slab_min        INTEGER NOT NULL,            -- Minimum units (inclusive), 0-based
  slab_max        INTEGER,                     -- NULL = unlimited (last slab)
  rate_per_unit   NUMERIC(8,4) NOT NULL,       -- PKR per kWh
  fixed_charges   NUMERIC(8,2) DEFAULT 0,      -- Fixed monthly charge for this slab
  notes           TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_elec_tariffs_date ON electricity_tariffs(effective_date DESC);

-- Seed data (NEPRA rates as of 2025):
-- (0,100) = 7.74, (101,200) = 10.06, (201,300) = 12.15, (301,400) = 17.64,
-- (401,500) = 20.47, (501,600) = 22.65, (601,700) = 23.93, (701,NULL) = 26.84
```

### 7.2 `gas_tariffs`
OGRA-published tariff slabs. Admin-maintained.

```sql
CREATE TABLE public.gas_tariffs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  effective_date  DATE NOT NULL,
  provider_code   TEXT NOT NULL,               -- 'sngpl' | 'ssgc'
  category        TEXT NOT NULL DEFAULT 'residential',
  slab_min        NUMERIC(8,4) NOT NULL,       -- MMBtu
  slab_max        NUMERIC(8,4),                -- NULL = unlimited
  rate_per_mmbtu  NUMERIC(8,4) NOT NULL,       -- PKR per MMBtu
  fixed_charges   NUMERIC(8,2) DEFAULT 0,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_gas_tariffs_date ON gas_tariffs(effective_date DESC);
```

### 7.3 `water_tariffs`
WASA tariff slabs per city. Admin-maintained.

```sql
CREATE TABLE public.water_tariffs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  effective_date  DATE NOT NULL,
  provider_code   TEXT NOT NULL,               -- 'wasa_lhr' | 'kwsb' etc.
  meter_size      TEXT DEFAULT 'standard',     -- '0.5inch' | '0.75inch' | '1inch'
  slab_min        NUMERIC(10,2) NOT NULL,      -- Gallons
  slab_max        NUMERIC(10,2),
  rate_per_unit   NUMERIC(8,4) NOT NULL,
  fixed_charges   NUMERIC(8,2) DEFAULT 0,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 8. Schema: Budget

### 8.1 `budget_categories`
System-defined categories + user-created custom categories.

```sql
CREATE TABLE public.budget_categories (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES profiles(id) ON DELETE CASCADE,  -- NULL = system category
  name        TEXT NOT NULL,
  icon        TEXT,                            -- Lucide icon name
  color       TEXT,                            -- Hex color
  is_system   BOOLEAN DEFAULT FALSE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- System category seeds:
-- 'Electricity', 'Gas', 'Water', 'Internet', 'Cable TV', 'Mobile Data',
-- 'Solar Maintenance', 'Grocery', 'Education', 'Rent', 'Other'

ALTER TABLE budget_categories ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Read system and own categories" ON budget_categories FOR SELECT USING (is_system = TRUE OR auth.uid() = user_id);
CREATE POLICY "Manage own categories" ON budget_categories FOR ALL USING (auth.uid() = user_id AND is_system = FALSE);
```

### 8.2 `budget_limits`
Monthly budget limits set by user per category.

```sql
CREATE TABLE public.budget_limits (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  home_id         UUID REFERENCES homes(id) ON DELETE CASCADE,
  category_id     UUID NOT NULL REFERENCES budget_categories(id),
  month           DATE NOT NULL,               -- First day of month: 2025-06-01
  limit_amount    NUMERIC(10,2) NOT NULL,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, home_id, category_id, month)
);

ALTER TABLE budget_limits ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own limits" ON budget_limits FOR ALL USING (auth.uid() = user_id);
```

### 8.3 `expense_entries`
Individual expense records (manual + auto-imported from bills).

```sql
CREATE TABLE public.expense_entries (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  home_id         UUID REFERENCES homes(id) ON DELETE SET NULL,
  category_id     UUID NOT NULL REFERENCES budget_categories(id),
  bill_id         UUID REFERENCES bills(id) ON DELETE SET NULL,  -- Link to bill if auto-imported
  amount          NUMERIC(10,2) NOT NULL,
  entry_date      DATE NOT NULL,
  description     TEXT,
  source          TEXT DEFAULT 'manual',       -- 'manual' | 'bill_import'
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_expense_entries_user_date ON expense_entries(user_id, entry_date DESC);
CREATE INDEX idx_expense_entries_category ON expense_entries(category_id, user_id);

ALTER TABLE expense_entries ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own expenses" ON expense_entries FOR ALL USING (auth.uid() = user_id);
```

---

## 9. Schema: Solar

### 9.1 `solar_installations`
User's solar system registration.

```sql
CREATE TABLE public.solar_installations (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  home_id               UUID REFERENCES homes(id) ON DELETE SET NULL,
  inverter_brand        TEXT NOT NULL,         -- 'growatt' | 'solis' | 'huawei'
  inverter_model        TEXT,
  system_size_kw        NUMERIC(6,2) NOT NULL, -- e.g. 10.0 kW
  panel_count           INTEGER,
  panel_wattage         INTEGER,               -- Watts per panel
  installation_date     DATE,
  system_cost_pkr       NUMERIC(12,2),         -- For ROI calculation
  net_metering_enabled  BOOLEAN DEFAULT FALSE,
  net_metering_ref      TEXT,                  -- DISCO net metering reference number
  inverter_api_user     TEXT,                  -- Encrypted: Growatt/Solis username
  inverter_api_pass     TEXT,                  -- Encrypted: password
  inverter_plant_id     TEXT,                  -- Plant ID on inverter platform
  last_synced_at        TIMESTAMPTZ,
  created_at            TIMESTAMPTZ DEFAULT NOW(),
  updated_at            TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE solar_installations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own solar" ON solar_installations FOR ALL USING (auth.uid() = user_id);
```

### 9.2 `solar_production_readings`
Daily solar production data synced from inverter API.

```sql
CREATE TABLE public.solar_production_readings (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  solar_installation_id   UUID NOT NULL REFERENCES solar_installations(id) ON DELETE CASCADE,
  reading_date            DATE NOT NULL,
  energy_produced_kwh     NUMERIC(10,3) NOT NULL,
  energy_consumed_kwh     NUMERIC(10,3),       -- From inverter if available
  energy_exported_kwh     NUMERIC(10,3),       -- Sent to grid
  energy_imported_kwh     NUMERIC(10,3),       -- Pulled from grid
  peak_power_kw           NUMERIC(8,3),        -- Max power output that day
  created_at              TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(solar_installation_id, reading_date)
);

CREATE INDEX idx_solar_readings_install_date ON solar_production_readings(solar_installation_id, reading_date DESC);
```

---

## 10. Schema: Notifications

### 10.1 `push_subscriptions`
Web Push API VAPID subscription objects.

```sql
CREATE TABLE public.push_subscriptions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  endpoint        TEXT NOT NULL UNIQUE,
  p256dh_key      TEXT NOT NULL,
  auth_key        TEXT NOT NULL,
  device_label    TEXT,                        -- e.g. 'Chrome on Android'
  is_active       BOOLEAN DEFAULT TRUE,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  last_used_at    TIMESTAMPTZ
);

CREATE INDEX idx_push_subs_user ON push_subscriptions(user_id);

ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own subscriptions" ON push_subscriptions FOR ALL USING (auth.uid() = user_id);
```

### 10.2 `notification_preferences`
Per-user notification settings.

```sql
CREATE TABLE public.notification_preferences (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                 UUID NOT NULL UNIQUE REFERENCES profiles(id) ON DELETE CASCADE,
  outage_alert_enabled    BOOLEAN DEFAULT TRUE,
  outage_alert_minutes    INTEGER DEFAULT 30,  -- Alert N minutes before scheduled outage
  bill_due_alert_enabled  BOOLEAN DEFAULT TRUE,
  bill_due_alert_days     INTEGER DEFAULT 3,   -- Alert N days before due date
  slab_alert_enabled      BOOLEAN DEFAULT TRUE,
  slab_alert_threshold    INTEGER DEFAULT 90,  -- Alert when N% of slab used
  solar_alert_enabled     BOOLEAN DEFAULT TRUE,
  community_alerts        BOOLEAN DEFAULT FALSE, -- Nearby outage reports
  created_at              TIMESTAMPTZ DEFAULT NOW(),
  updated_at              TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own prefs" ON notification_preferences FOR ALL USING (auth.uid() = user_id);
```

### 10.3 `notification_log`
Audit log of all notifications sent (prevents duplicates, tracks delivery).

```sql
CREATE TABLE public.notification_log (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  type            TEXT NOT NULL,               -- 'outage_warning' | 'bill_due' | 'slab_alert' | 'solar_alert'
  reference_id    UUID,                        -- ID of related record (bill, outage, etc.)
  title           TEXT NOT NULL,
  body            TEXT NOT NULL,
  sent_at         TIMESTAMPTZ DEFAULT NOW(),
  delivery_status TEXT DEFAULT 'sent',         -- 'sent' | 'failed' | 'clicked'
  UNIQUE(user_id, type, reference_id)          -- Prevents duplicate notifications
);

CREATE INDEX idx_notif_log_user ON notification_log(user_id, sent_at DESC);
```

---

## 11. Schema: ISP Comparison

### 11.1 `isp_packages`
Admin-maintained ISP package data.

```sql
CREATE TABLE public.isp_packages (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_code       TEXT NOT NULL,           -- 'ptcl' | 'nayatel' | 'stormfiber' | 'jazz_home'
  package_name        TEXT NOT NULL,
  speed_mbps_down     INTEGER NOT NULL,
  speed_mbps_up       INTEGER,
  monthly_price_pkr   NUMERIC(8,2) NOT NULL,
  data_cap_gb         INTEGER,                 -- NULL = unlimited
  cities_available    TEXT[],                  -- ['lahore', 'karachi', 'islamabad']
  is_fiber            BOOLEAN DEFAULT FALSE,
  is_active           BOOLEAN DEFAULT TRUE,
  affiliate_link      TEXT,
  last_verified       DATE,
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_isp_packages_provider ON isp_packages(provider_code);
CREATE INDEX idx_isp_packages_cities ON isp_packages USING GIN(cities_available);
```

### 11.2 `isp_ratings`
Crowd-sourced ISP ratings by city.

```sql
CREATE TABLE public.isp_ratings (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  provider_code   TEXT NOT NULL,
  city            TEXT NOT NULL,
  speed_rating    INTEGER CHECK (speed_rating BETWEEN 1 AND 5),
  reliability     INTEGER CHECK (reliability BETWEEN 1 AND 5),
  support_rating  INTEGER CHECK (support_rating BETWEEN 1 AND 5),
  comment         TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, provider_code, city)
);

ALTER TABLE isp_ratings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone reads ratings" ON isp_ratings FOR SELECT USING (TRUE);
CREATE POLICY "Auth users rate" ON isp_ratings FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users update own rating" ON isp_ratings FOR UPDATE USING (auth.uid() = user_id);
```

---

## 12. Schema: Complaints

### 12.1 `complaint_submissions`
Tracks complaints filed via the Complaint Assistant.

```sql
CREATE TABLE public.complaint_submissions (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  consumer_account_id UUID REFERENCES consumer_accounts(id) ON DELETE SET NULL,
  authority           TEXT NOT NULL,           -- 'nepra' | 'ogra' | 'pta' | 'wasa'
  complaint_type      TEXT NOT NULL,           -- 'billing' | 'outage' | 'quality' | 'service'
  description         TEXT NOT NULL,
  reference_number    TEXT,                    -- Assigned by authority after submission
  status              TEXT DEFAULT 'submitted', -- 'submitted' | 'pending' | 'resolved' | 'failed'
  submitted_at        TIMESTAMPTZ,
  resolved_at         TIMESTAMPTZ,
  notes               TEXT,
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE complaint_submissions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own complaints" ON complaint_submissions FOR ALL USING (auth.uid() = user_id);
```

---

## 13. Triggers & Functions

### 13.1 Auto-create profile on signup
```sql
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name)
  VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name');
  
  INSERT INTO public.notification_preferences (user_id)
  VALUES (NEW.id);
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

### 13.2 Auto-update `updated_at`
```sql
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at column
CREATE TRIGGER set_updated_at BEFORE UPDATE ON profiles FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at BEFORE UPDATE ON homes FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at BEFORE UPDATE ON consumer_accounts FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at BEFORE UPDATE ON bills FOR EACH ROW EXECUTE FUNCTION set_updated_at();
-- (repeat for all tables with updated_at)
```

### 13.3 Auto-import bill to expense_entries
```sql
CREATE OR REPLACE FUNCTION public.import_bill_to_expenses()
RETURNS TRIGGER AS $$
DECLARE
  cat_id UUID;
  util_name TEXT;
BEGIN
  -- Map utility type to category name
  SELECT ca.utility_type INTO util_name FROM consumer_accounts ca WHERE ca.id = NEW.consumer_account_id;
  
  SELECT id INTO cat_id FROM budget_categories 
  WHERE name = INITCAP(util_name) AND is_system = TRUE LIMIT 1;
  
  IF cat_id IS NOT NULL THEN
    INSERT INTO expense_entries (user_id, category_id, bill_id, amount, entry_date, source, description)
    VALUES (NEW.user_id, cat_id, NEW.id, NEW.amount_payable, NEW.billing_month, 'bill_import', 'Auto-imported from bill')
    ON CONFLICT DO NOTHING;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER auto_import_bill AFTER INSERT ON bills
  FOR EACH ROW EXECUTE FUNCTION import_bill_to_expenses();
```

---

## 14. Views

### 14.1 Monthly utility spending summary
```sql
CREATE VIEW public.monthly_utility_summary AS
SELECT 
  e.user_id,
  DATE_TRUNC('month', e.entry_date) AS month,
  c.name AS category,
  SUM(e.amount) AS total_amount,
  COUNT(*) AS entry_count
FROM expense_entries e
JOIN budget_categories c ON c.id = e.category_id
GROUP BY e.user_id, DATE_TRUNC('month', e.entry_date), c.name;
```

### 14.2 Active outage reports by area
```sql
CREATE VIEW public.active_outage_summary AS
SELECT
  city, area_slug, utility_type, provider_code,
  COUNT(*) AS report_count,
  MIN(created_at) AS first_report,
  MAX(created_at) AS last_report
FROM community_outage_reports
WHERE expires_at > NOW() AND is_restored = FALSE
GROUP BY city, area_slug, utility_type, provider_code;
```

---

## 15. Indexes Summary

All foreign keys have indexes. Additional composite indexes:
- `(user_id, billing_month)` on `bills` — for bill history queries
- `(city, schedule_date)` on `outage_schedules` — for outage lookups
- `(city, area_slug, created_at DESC)` on `community_outage_reports` — for feed queries
- `(user_id, entry_date DESC)` on `expense_entries` — for budget queries
- `(solar_installation_id, reading_date DESC)` on `solar_production_readings`
