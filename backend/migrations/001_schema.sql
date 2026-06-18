-- ============================================================
-- Sahulat Database Schema v0.1.0
-- Based on: P03 Database Schema + P05 Scraper Run Log
-- ============================================================

-- 2. Users & Auth
-- ------------------------------------------------------------

CREATE TABLE public.profiles (
  id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name       TEXT,
  phone           TEXT UNIQUE,
  city            TEXT,
  area            TEXT,
  preferred_lang  TEXT DEFAULT 'en',
  premium         BOOLEAN DEFAULT FALSE,
  premium_until   TIMESTAMPTZ,
  avatar_url      TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);

CREATE TABLE public.homes (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
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

-- 3. Consumer Numbers & Utilities
-- ------------------------------------------------------------

CREATE TABLE public.consumer_accounts (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  home_id             UUID REFERENCES homes(id) ON DELETE SET NULL,
  utility_type        TEXT NOT NULL,
  provider_code       TEXT NOT NULL,
  consumer_number     TEXT NOT NULL,
  account_label       TEXT,
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

-- 4. Bills
-- ------------------------------------------------------------

CREATE TABLE public.bills (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  consumer_account_id   UUID NOT NULL REFERENCES consumer_accounts(id) ON DELETE CASCADE,
  user_id               UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  billing_month         DATE NOT NULL,
  issue_date            DATE,
  due_date              DATE,
  amount_payable        NUMERIC(10,2) NOT NULL,
  units_consumed        NUMERIC(10,2),
  previous_reading      NUMERIC(10,2),
  current_reading       NUMERIC(10,2),
  arrears               NUMERIC(10,2) DEFAULT 0,
  taxes                 NUMERIC(10,2) DEFAULT 0,
  surcharges            NUMERIC(10,2) DEFAULT 0,
  meter_rent            NUMERIC(10,2) DEFAULT 0,
  fc_surcharge          NUMERIC(10,2) DEFAULT 0,
  tariff_slab           TEXT,
  status                TEXT DEFAULT 'unpaid',
  raw_data              JSONB,
  fetch_source          TEXT DEFAULT 'scraper',
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

-- 5. Consumption (Meter Readings)
-- ------------------------------------------------------------

CREATE TABLE public.meter_readings (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  consumer_account_id   UUID NOT NULL REFERENCES consumer_accounts(id) ON DELETE CASCADE,
  user_id               UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  reading_date          DATE NOT NULL,
  reading_value         NUMERIC(10,2) NOT NULL,
  units_since_last      NUMERIC(10,2),
  estimated_bill        NUMERIC(10,2),
  notes                 TEXT,
  created_at            TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(consumer_account_id, reading_date)
);

CREATE INDEX idx_meter_readings_consumer ON meter_readings(consumer_account_id, reading_date DESC);
CREATE INDEX idx_meter_readings_user ON meter_readings(user_id);

ALTER TABLE meter_readings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own readings" ON meter_readings FOR ALL USING (auth.uid() = user_id);

CREATE TABLE public.slab_alerts (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  consumer_account_id   UUID NOT NULL REFERENCES consumer_accounts(id) ON DELETE CASCADE,
  user_id               UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  billing_period        DATE NOT NULL,
  slab_threshold        INTEGER NOT NULL,
  units_at_alert        NUMERIC(10,2) NOT NULL,
  cost_if_crossed       NUMERIC(10,2),
  alerted_at            TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(consumer_account_id, billing_period, slab_threshold)
);

ALTER TABLE slab_alerts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users view own slab alerts" ON slab_alerts FOR SELECT USING (auth.uid() = user_id);

-- 6. Outage Data
-- ------------------------------------------------------------

CREATE TABLE public.outage_schedules (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_code   TEXT NOT NULL,
  feeder_code     TEXT NOT NULL,
  feeder_name     TEXT NOT NULL,
  area_tags       TEXT[],
  city            TEXT NOT NULL,
  schedule_date   DATE NOT NULL,
  slots           JSONB NOT NULL,
  week_start      DATE NOT NULL,
  source_pdf_url  TEXT,
  parsed_at       TIMESTAMPTZ DEFAULT NOW(),
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(provider_code, feeder_code, schedule_date)
);

CREATE INDEX idx_outage_schedules_city_date ON outage_schedules(city, schedule_date);
CREATE INDEX idx_outage_schedules_provider ON outage_schedules(provider_code, schedule_date);
CREATE INDEX idx_outage_schedules_area ON outage_schedules USING GIN(area_tags);

CREATE TABLE public.community_outage_reports (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES profiles(id) ON DELETE SET NULL,
  utility_type    TEXT NOT NULL,
  provider_code   TEXT,
  city            TEXT NOT NULL,
  area            TEXT NOT NULL,
  area_slug       TEXT NOT NULL,
  latitude        NUMERIC(10,7),
  longitude       NUMERIC(10,7),
  description     TEXT,
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

-- 7. Tariffs
-- ------------------------------------------------------------

CREATE TABLE public.electricity_tariffs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  effective_date  DATE NOT NULL,
  category        TEXT NOT NULL DEFAULT 'residential',
  slab_min        INTEGER NOT NULL,
  slab_max        INTEGER,
  rate_per_unit   NUMERIC(8,4) NOT NULL,
  fixed_charges   NUMERIC(8,2) DEFAULT 0,
  notes           TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_elec_tariffs_date ON electricity_tariffs(effective_date DESC);

CREATE TABLE public.gas_tariffs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  effective_date  DATE NOT NULL,
  provider_code   TEXT NOT NULL,
  category        TEXT NOT NULL DEFAULT 'residential',
  slab_min        NUMERIC(8,4) NOT NULL,
  slab_max        NUMERIC(8,4),
  rate_per_mmbtu  NUMERIC(8,4) NOT NULL,
  fixed_charges   NUMERIC(8,2) DEFAULT 0,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_gas_tariffs_date ON gas_tariffs(effective_date DESC);

CREATE TABLE public.water_tariffs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  effective_date  DATE NOT NULL,
  provider_code   TEXT NOT NULL,
  meter_size      TEXT DEFAULT 'standard',
  slab_min        NUMERIC(10,2) NOT NULL,
  slab_max        NUMERIC(10,2),
  rate_per_unit   NUMERIC(8,4) NOT NULL,
  fixed_charges   NUMERIC(8,2) DEFAULT 0,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Budget
-- ------------------------------------------------------------

CREATE TABLE public.budget_categories (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES profiles(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  icon        TEXT,
  color       TEXT,
  is_system   BOOLEAN DEFAULT FALSE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE budget_categories ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Read system and own categories" ON budget_categories FOR SELECT USING (is_system = TRUE OR auth.uid() = user_id);
CREATE POLICY "Manage own categories" ON budget_categories FOR ALL USING (auth.uid() = user_id AND is_system = FALSE);

CREATE TABLE public.budget_limits (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  home_id         UUID REFERENCES homes(id) ON DELETE CASCADE,
  category_id     UUID NOT NULL REFERENCES budget_categories(id),
  month           DATE NOT NULL,
  limit_amount    NUMERIC(10,2) NOT NULL,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, home_id, category_id, month)
);

ALTER TABLE budget_limits ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own limits" ON budget_limits FOR ALL USING (auth.uid() = user_id);

CREATE TABLE public.expense_entries (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  home_id         UUID REFERENCES homes(id) ON DELETE SET NULL,
  category_id     UUID NOT NULL REFERENCES budget_categories(id),
  bill_id         UUID REFERENCES bills(id) ON DELETE SET NULL,
  amount          NUMERIC(10,2) NOT NULL,
  entry_date      DATE NOT NULL,
  description     TEXT,
  source          TEXT DEFAULT 'manual',
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_expense_entries_user_date ON expense_entries(user_id, entry_date DESC);
CREATE INDEX idx_expense_entries_category ON expense_entries(category_id, user_id);

ALTER TABLE expense_entries ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own expenses" ON expense_entries FOR ALL USING (auth.uid() = user_id);

-- 9. Solar
-- ------------------------------------------------------------

CREATE TABLE public.solar_installations (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  home_id               UUID REFERENCES homes(id) ON DELETE SET NULL,
  inverter_brand        TEXT NOT NULL,
  inverter_model        TEXT,
  system_size_kw        NUMERIC(6,2) NOT NULL,
  panel_count           INTEGER,
  panel_wattage         INTEGER,
  installation_date     DATE,
  system_cost_pkr       NUMERIC(12,2),
  net_metering_enabled  BOOLEAN DEFAULT FALSE,
  net_metering_ref      TEXT,
  inverter_api_user     TEXT,
  inverter_api_pass     TEXT,
  inverter_plant_id     TEXT,
  last_synced_at        TIMESTAMPTZ,
  created_at            TIMESTAMPTZ DEFAULT NOW(),
  updated_at            TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE solar_installations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own solar" ON solar_installations FOR ALL USING (auth.uid() = user_id);

CREATE TABLE public.solar_production_readings (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  solar_installation_id   UUID NOT NULL REFERENCES solar_installations(id) ON DELETE CASCADE,
  reading_date            DATE NOT NULL,
  energy_produced_kwh     NUMERIC(10,3) NOT NULL,
  energy_consumed_kwh     NUMERIC(10,3),
  energy_exported_kwh     NUMERIC(10,3),
  energy_imported_kwh     NUMERIC(10,3),
  peak_power_kw           NUMERIC(8,3),
  created_at              TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(solar_installation_id, reading_date)
);

CREATE INDEX idx_solar_readings_install_date ON solar_production_readings(solar_installation_id, reading_date DESC);

-- 10. Notifications
-- ------------------------------------------------------------

CREATE TABLE public.push_subscriptions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  endpoint        TEXT NOT NULL UNIQUE,
  p256dh_key      TEXT NOT NULL,
  auth_key        TEXT NOT NULL,
  device_label    TEXT,
  is_active       BOOLEAN DEFAULT TRUE,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  last_used_at    TIMESTAMPTZ
);

CREATE INDEX idx_push_subs_user ON push_subscriptions(user_id);

ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own subscriptions" ON push_subscriptions FOR ALL USING (auth.uid() = user_id);

CREATE TABLE public.notification_preferences (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                 UUID NOT NULL UNIQUE REFERENCES profiles(id) ON DELETE CASCADE,
  outage_alert_enabled    BOOLEAN DEFAULT TRUE,
  outage_alert_minutes    INTEGER DEFAULT 30,
  bill_due_alert_enabled  BOOLEAN DEFAULT TRUE,
  bill_due_alert_days     INTEGER DEFAULT 3,
  slab_alert_enabled      BOOLEAN DEFAULT TRUE,
  slab_alert_threshold    INTEGER DEFAULT 90,
  solar_alert_enabled     BOOLEAN DEFAULT TRUE,
  community_alerts        BOOLEAN DEFAULT FALSE,
  created_at              TIMESTAMPTZ DEFAULT NOW(),
  updated_at              TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own prefs" ON notification_preferences FOR ALL USING (auth.uid() = user_id);

CREATE TABLE public.notification_log (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  type            TEXT NOT NULL,
  reference_id    UUID,
  title           TEXT NOT NULL,
  body            TEXT NOT NULL,
  sent_at         TIMESTAMPTZ DEFAULT NOW(),
  delivery_status TEXT DEFAULT 'sent',
  UNIQUE(user_id, type, reference_id)
);

CREATE INDEX idx_notif_log_user ON notification_log(user_id, sent_at DESC);

-- 11. ISP Comparison
-- ------------------------------------------------------------

CREATE TABLE public.isp_packages (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_code       TEXT NOT NULL,
  package_name        TEXT NOT NULL,
  speed_mbps_down     INTEGER NOT NULL,
  speed_mbps_up       INTEGER,
  monthly_price_pkr   NUMERIC(8,2) NOT NULL,
  data_cap_gb         INTEGER,
  cities_available    TEXT[],
  is_fiber            BOOLEAN DEFAULT FALSE,
  is_active           BOOLEAN DEFAULT TRUE,
  affiliate_link      TEXT,
  last_verified       DATE,
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_isp_packages_provider ON isp_packages(provider_code);
CREATE INDEX idx_isp_packages_cities ON isp_packages USING GIN(cities_available);

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

-- 12. Complaints
-- ------------------------------------------------------------

CREATE TABLE public.complaint_submissions (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  consumer_account_id UUID REFERENCES consumer_accounts(id) ON DELETE SET NULL,
  authority           TEXT NOT NULL,
  complaint_type      TEXT NOT NULL,
  description         TEXT NOT NULL,
  reference_number    TEXT,
  status              TEXT DEFAULT 'submitted',
  submitted_at        TIMESTAMPTZ,
  resolved_at         TIMESTAMPTZ,
  notes               TEXT,
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE complaint_submissions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own complaints" ON complaint_submissions FOR ALL USING (auth.uid() = user_id);

-- 13. Scraper Run Log (from P05)
-- ------------------------------------------------------------

CREATE TABLE public.scraper_run_log (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_code   TEXT NOT NULL,
  job_type        TEXT NOT NULL,
  status          TEXT NOT NULL,
  target_id       TEXT,
  error_message   TEXT,
  duration_ms     INTEGER,
  run_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scraper_log_provider_time ON scraper_run_log(provider_code, run_at DESC);

-- ============================================================
-- Triggers & Functions
-- ============================================================

-- 13.1 Auto-create profile + notification_prefs on signup

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

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 13.2 Auto-update updated_at

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_profiles BEFORE UPDATE ON profiles FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at_homes BEFORE UPDATE ON homes FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at_consumer_accounts BEFORE UPDATE ON consumer_accounts FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at_bills BEFORE UPDATE ON bills FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at_expense_entries BEFORE UPDATE ON expense_entries FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at_solar_installations BEFORE UPDATE ON solar_installations FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at_isp_packages BEFORE UPDATE ON isp_packages FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at_complaint_submissions BEFORE UPDATE ON complaint_submissions FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER set_updated_at_notification_preferences BEFORE UPDATE ON notification_preferences FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 13.3 Auto-import bill to expense_entries

CREATE OR REPLACE FUNCTION public.import_bill_to_expenses()
RETURNS TRIGGER AS $$
DECLARE
  cat_id UUID;
  util_name TEXT;
BEGIN
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

-- ============================================================
-- Views
-- ============================================================

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

CREATE VIEW public.active_outage_summary AS
SELECT
  city, area_slug, utility_type, provider_code,
  COUNT(*) AS report_count,
  MIN(created_at) AS first_report,
  MAX(created_at) AS last_report
FROM community_outage_reports
WHERE expires_at > NOW() AND is_restored = FALSE
GROUP BY city, area_slug, utility_type, provider_code;

-- ============================================================
-- Seed Data
-- ============================================================

-- Budget system categories

INSERT INTO public.budget_categories (name, icon, color, is_system) VALUES
  ('Electricity', 'zap', '#F59E0B', TRUE),
  ('Gas', 'flame', '#3B82F6', TRUE),
  ('Water', 'droplet', '#06B6D4', TRUE),
  ('Internet', 'wifi', '#8B5CF6', TRUE),
  ('Cable TV', 'tv', '#EC4899', TRUE),
  ('Mobile Data', 'smartphone', '#14B8A6', TRUE),
  ('Solar Maintenance', 'sun', '#EAB308', TRUE),
  ('Grocery', 'shopping-cart', '#10B981', TRUE),
  ('Education', 'book-open', '#6366F1', TRUE),
  ('Rent', 'home', '#F97316', TRUE),
  ('Other', 'more-horizontal', '#6B7280', TRUE)
ON CONFLICT DO NOTHING;

-- Electricity tariff seed data (NEPRA residential rates as of 2025)

INSERT INTO public.electricity_tariffs (effective_date, category, slab_min, slab_max, rate_per_unit, fixed_charges) VALUES
  ('2025-01-01', 'residential', 0,   100, 7.74,  0),
  ('2025-01-01', 'residential', 101, 200, 10.06, 0),
  ('2025-01-01', 'residential', 201, 300, 12.15, 0),
  ('2025-01-01', 'residential', 301, 400, 17.64, 0),
  ('2025-01-01', 'residential', 401, 500, 20.47, 0),
  ('2025-01-01', 'residential', 501, 600, 22.65, 0),
  ('2025-01-01', 'residential', 601, 700, 23.93, 0),
  ('2025-01-01', 'residential', 701, NULL, 26.84, 0)
ON CONFLICT DO NOTHING;
