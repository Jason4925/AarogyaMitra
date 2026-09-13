-- Profile compatibility: age is optional in the UI, so keep a non-null empty-string sentinel.
-- Existing rows are normalized before enforcing the default.
ALTER TABLE public.users ALTER COLUMN age SET DEFAULT '';
UPDATE public.users SET age = '' WHERE age IS NULL;
ALTER TABLE public.users ALTER COLUMN age SET NOT NULL;
