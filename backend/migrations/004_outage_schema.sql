-- ============================================================
-- P09 — Outage Tracker Schema Additions
-- Based on: plan.md Phase 1 + P09 §4
-- ============================================================

-- Add additional fields to outage_schedules
ALTER TABLE public.outage_schedules
  ADD COLUMN IF NOT EXISTS confidence_score NUMERIC DEFAULT 0.0,
  ADD COLUMN IF NOT EXISTS source_url TEXT,
  ADD COLUMN IF NOT EXISTS raw_text TEXT;

-- Add additional fields to community_outage_reports
ALTER TABLE public.community_outage_reports
  ADD COLUMN IF NOT EXISTS home_id UUID REFERENCES homes(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS severity TEXT DEFAULT 'medium',
  ADD COLUMN IF NOT EXISTS report_type TEXT DEFAULT 'electricity_outage';

-- Add feeder_name to homes table
ALTER TABLE public.homes
  ADD COLUMN IF NOT EXISTS feeder_name TEXT;

-- Create index for feeder-based queries on outage_schedules
CREATE INDEX IF NOT EXISTS idx_outage_schedules_feeder
  ON public.outage_schedules(provider_code, feeder_code);
