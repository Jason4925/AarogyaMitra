-- Allow users to omit age.
ALTER TABLE public.users
ALTER COLUMN age DROP NOT NULL;
ALTER TABLE public.users
ALTER COLUMN age DROP DEFAULT;
