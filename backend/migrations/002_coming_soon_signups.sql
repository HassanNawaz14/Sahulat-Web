-- Coming Soon Signups (P06 §6.3)
CREATE TABLE public.coming_soon_signups (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  provider_code   TEXT NOT NULL,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, provider_code)
);

CREATE INDEX idx_coming_soon_signups_provider ON coming_soon_signups(provider_code);

ALTER TABLE coming_soon_signups ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own signups" ON coming_soon_signups FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "System reads signups" ON coming_soon_signups FOR SELECT USING (TRUE);
