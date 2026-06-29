-- ============================================================
-- P10 — Budget Manager Schema
-- Renames old abandoned tables (*_old), creates correct schema
-- ============================================================

-- Rename old tables aside (preserving data)
ALTER TABLE IF EXISTS public.budget_categories RENAME TO budget_categories_old;
ALTER TABLE IF EXISTS public.budget_limits RENAME TO budget_limits_old;
ALTER TABLE IF EXISTS public.expense_entries RENAME TO expense_entries_old;

-- Drop old view (will be recreated later if needed)
DROP VIEW IF EXISTS public.monthly_utility_summary;

-- Drop budget_expenses if created by a prior run of this migration
DROP TABLE IF EXISTS public.budget_expenses;

-- Budget categories (user-scoped)
CREATE TABLE public.budget_categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  code TEXT NOT NULL,
  label TEXT NOT NULL,
  monthly_limit NUMERIC(10,2),
  is_custom BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, code)
);

-- Manual expense entries
CREATE TABLE public.budget_expenses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  home_id UUID REFERENCES homes(id) ON DELETE SET NULL,
  category_id UUID NOT NULL REFERENCES budget_categories(id) ON DELETE CASCADE,
  amount NUMERIC(10,2) NOT NULL,
  expense_date DATE NOT NULL,
  description TEXT,
  is_recurring BOOLEAN DEFAULT FALSE,
  recurrence_day INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast month queries
CREATE INDEX IF NOT EXISTS idx_budget_expenses_user_date ON budget_expenses(user_id, expense_date);
CREATE INDEX IF NOT EXISTS idx_budget_categories_user ON budget_categories(user_id);
