-- ============================================================
-- P09 — Store feeder_name directly on consumer_accounts
-- Removes the requirement for a home_id link to set a feeder.
-- ============================================================

ALTER TABLE public.consumer_accounts
  ADD COLUMN IF NOT EXISTS feeder_name TEXT;
