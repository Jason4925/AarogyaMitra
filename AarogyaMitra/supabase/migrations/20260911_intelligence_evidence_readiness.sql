-- AarogyaMitra: intelligence and evidence/scale governance
-- The ORM also creates this table during backend startup.
create table if not exists public.readiness_items (
  id text primary key,
  category text not null,
  name text not null,
  status text not null default 'planned',
  owner text not null default '',
  last_reviewed text not null default '',
  notes text not null default '',
  created_at timestamptz not null default now()
);

create index if not exists readiness_items_category_idx on public.readiness_items(category);
