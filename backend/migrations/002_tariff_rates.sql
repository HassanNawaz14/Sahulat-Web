-- Migration 002: Correct NEPRA residential tariff rates with protected/unprotected categories
-- Applied: 2026-06-22
-- Replaces the placeholder rates from migration 001 with actual NEPRA rates for <=5kW load

-- Step 1: Update existing residential (unprotected) slabs with correct rates
UPDATE public.electricity_tariffs SET rate_per_unit = 22.44 WHERE category = 'residential' AND slab_min = 0   AND slab_max = 100;
UPDATE public.electricity_tariffs SET rate_per_unit = 28.91 WHERE category = 'residential' AND slab_min = 101 AND slab_max = 200;
UPDATE public.electricity_tariffs SET rate_per_unit = 33.10 WHERE category = 'residential' AND slab_min = 201 AND slab_max = 300;
UPDATE public.electricity_tariffs SET rate_per_unit = 36.46 WHERE category = 'residential' AND slab_min = 301 AND slab_max = 400;
UPDATE public.electricity_tariffs SET rate_per_unit = 38.95 WHERE category = 'residential' AND slab_min = 401 AND slab_max = 500;
UPDATE public.electricity_tariffs SET rate_per_unit = 40.22 WHERE category = 'residential' AND slab_min = 501 AND slab_max = 600;
UPDATE public.electricity_tariffs SET rate_per_unit = 41.85 WHERE category = 'residential' AND slab_min = 601 AND slab_max = 700;
UPDATE public.electricity_tariffs SET rate_per_unit = 47.20 WHERE category = 'residential' AND slab_min = 701 AND slab_max IS NULL;

-- Step 2: Insert protected category slabs (only up to 200 units — beyond that, consumer loses protected status)
INSERT INTO public.electricity_tariffs (effective_date, category, slab_min, slab_max, rate_per_unit, fixed_charges) VALUES
  ('2025-01-01', 'protected', 0,   100, 7.74,  0),
  ('2025-01-01', 'protected', 101, 200, 13.01, 0)
ON CONFLICT DO NOTHING;
