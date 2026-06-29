-- P19 Notifications & Alerts System
-- Renames old P03 placeholder tables to *_old, creates correct schema

-- Rename old tables aside (preserving data)
ALTER TABLE IF EXISTS public.notification_preferences RENAME TO notification_preferences_old;
ALTER TABLE IF EXISTS public.push_subscriptions RENAME TO push_subscriptions_old;
ALTER TABLE IF EXISTS public.notification_log RENAME TO notification_log_old;

-- Drop old trigger to avoid conflicts
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Recreate handle_new_user: creates profile + seeds notification preferences
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name)
  VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name');

  INSERT INTO public.notification_preferences (user_id, category, enabled, channels)
  VALUES
    (NEW.id, 'bill_due', TRUE, '{"push": true, "sms": false}'),
    (NEW.id, 'outage', TRUE, '{"push": true, "sms": false}'),
    (NEW.id, 'slab', TRUE, '{"push": true, "sms": false}'),
    (NEW.id, 'budget', TRUE, '{"push": true, "sms": false}'),
    (NEW.id, 'solar', TRUE, '{"push": true, "sms": false}'),
    (NEW.id, 'community', TRUE, '{"push": true, "sms": false}')
  ON CONFLICT (user_id, category) DO NOTHING;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Notification preferences per user (category-based rows)
CREATE TABLE IF NOT EXISTS public.notification_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  category TEXT NOT NULL, -- 'bill_due', 'outage', 'slab', 'budget', 'solar', etc.
  enabled BOOLEAN DEFAULT TRUE,
  channels JSONB DEFAULT '{"push": true, "sms": false}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, category)
);

-- Push subscriptions (Web Push API)
CREATE TABLE IF NOT EXISTS public.push_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  endpoint TEXT NOT NULL UNIQUE,
  p256dh TEXT NOT NULL,
  auth TEXT NOT NULL,
  user_agent TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  last_used_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Notification event log (for deduplication and debugging)
CREATE TABLE IF NOT EXISTS public.notification_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  category TEXT NOT NULL,
  event_type TEXT NOT NULL, -- 'sent', 'failed', 'clicked'
  title TEXT,
  body TEXT,
  url TEXT,
  error_message TEXT,
  push_subscription_id UUID REFERENCES push_subscriptions(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_notification_events_user_created ON notification_events(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user ON push_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_preferences_user ON notification_preferences(user_id);

-- RLS
ALTER TABLE public.notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.push_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own notification preferences" ON public.notification_preferences
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users manage own push subscriptions" ON public.push_subscriptions
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users view own notification events" ON public.notification_events
  FOR SELECT USING (auth.uid() = user_id);

-- Updated-at trigger for notification_preferences (replaces old one lost during rename)
CREATE TRIGGER set_updated_at_notification_preferences BEFORE UPDATE ON public.notification_preferences
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


