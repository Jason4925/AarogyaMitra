create table if not exists public.doctor_notes (
  id text primary key,
  patient_user_id text not null references public.users(user_id) on delete cascade,
  doctor_user_id text not null references public.users(user_id) on delete cascade,
  handoff_id text default '', note text not null, status text default 'reviewed',
  created_at timestamp default now()
);
create index if not exists idx_doctor_notes_patient on public.doctor_notes(patient_user_id);
create index if not exists idx_doctor_notes_doctor on public.doctor_notes(doctor_user_id);

create table if not exists public.knowledge_sources (
  id text primary key, title text not null, topic text default '', source text default '', url text default '',
  summary text default '', specific_triggers jsonb default '[]'::jsonb, status text default 'active',
  version text default '1.0', last_reviewed text default '', next_review text default '', created_at timestamp default now(), updated_at timestamp default now()
);
create index if not exists idx_knowledge_sources_status on public.knowledge_sources(status);

create table if not exists public.knowledge_reviews (
  id text primary key, source_id text not null references public.knowledge_sources(id) on delete cascade,
  reviewer_user_id text not null references public.users(user_id) on delete cascade,
  decision text default 'reviewed', notes text default '', created_at timestamp default now()
);
create index if not exists idx_knowledge_reviews_source on public.knowledge_reviews(source_id);

-- Operational security observations are retained in existing audit/login/session tables.
