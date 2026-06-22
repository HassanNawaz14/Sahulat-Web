-- PTCL provider reference support (Account ID for landline inquiry)
ALTER TABLE public.consumer_accounts
ADD COLUMN IF NOT EXISTS provider_reference TEXT;
