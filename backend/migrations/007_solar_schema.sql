-- ============================================================
-- P11 Solar Dashboard Schema Additions
-- ============================================================

-- Add missing columns to solar_installations per P11 spec
ALTER TABLE public.solar_installations
  ADD COLUMN IF NOT EXISTS api_username_encrypted TEXT,
  ADD COLUMN IF NOT EXISTS api_password_encrypted TEXT,
  ADD COLUMN IF NOT EXISTS api_token_encrypted TEXT,
  ADD COLUMN IF NOT EXISTS commissioning_date DATE;

-- Rename existing columns to match P11 spec (system_cost_pkr -> installation_cost)
-- Note: system_cost_pkr already exists, keep both for compatibility
-- Add installation_cost as alias/duplicate if needed

-- Create solar_alerts table for panel health alerts (P11 §8)
CREATE TABLE IF NOT EXISTS public.solar_alerts (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  solar_installation_id UUID NOT NULL REFERENCES solar_installations(id) ON DELETE CASCADE,
  user_id               UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  alert_type            TEXT NOT NULL,  -- 'baseline_drop', 'zero_production', 'inverter_disconnected', 'cleaning_due'
  severity              TEXT NOT NULL DEFAULT 'warning',  -- 'info', 'warning', 'critical'
  title                 TEXT NOT NULL,
  message               TEXT NOT NULL,
  production_kwh        NUMERIC(10,3),
  baseline_kwh          NUMERIC(10,3),
  is_read               BOOLEAN DEFAULT FALSE,
  is_dismissed          BOOLEAN DEFAULT FALSE,
  created_at            TIMESTAMPTZ DEFAULT NOW(),
  resolved_at           TIMESTAMPTZ
);

CREATE INDEX idx_solar_alerts_installation ON solar_alerts(solar_installation_id, created_at DESC);
CREATE INDEX idx_solar_alerts_user ON solar_alerts(user_id, created_at DESC);
CREATE INDEX idx_solar_alerts_unread ON solar_alerts(user_id, is_read, is_dismissed) WHERE is_read = FALSE AND is_dismissed = FALSE;

ALTER TABLE solar_alerts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own solar alerts" ON solar_alerts FOR ALL USING (auth.uid() = user_id);

-- Add updated_at trigger for solar_alerts
CREATE TRIGGER set_updated_at_solar_alerts BEFORE UPDATE ON solar_alerts FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Rename solar_production_readings to solar_daily_production per P11 spec (alias via view for compatibility)
-- Keep existing table, create view with new name
CREATE OR REPLACE VIEW public.solar_daily_production AS
SELECT
  id,
  solar_installation_id,
  reading_date AS date,
  energy_produced_kwh AS production_kwh,
  energy_consumed_kwh AS self_consumed_kwh,
  energy_exported_kwh AS exported_kwh,
  energy_imported_kwh AS imported_kwh,
  peak_power_kw,
  created_at
FROM solar_production_readings;

-- Add net_metering_export_rate to electricity_tariffs if not exists (for NEPRA buyback rate)
-- This can be added in a separate tariff migration if needed

-- Seed: No new seed data required for P11