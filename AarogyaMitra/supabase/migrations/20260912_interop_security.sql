create table if not exists public.login_sessions (
  id text primary key,
  user_id text not null references public.users(user_id) on delete cascade,
  jti text unique not null,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null,
  revoked boolean not null default false
);
create index if not exists idx_login_sessions_user on public.login_sessions(user_id);
create index if not exists idx_login_sessions_jti on public.login_sessions(jti);
create table if not exists public.login_attempts (
  id bigserial primary key,
  email text not null,
  user_id text,
  success boolean not null default false,
  ip_address text not null default '',
  created_at timestamptz not null default now()
);
create index if not exists idx_login_attempts_email on public.login_attempts(email);
create index if not exists idx_login_attempts_created on public.login_attempts(created_at);
