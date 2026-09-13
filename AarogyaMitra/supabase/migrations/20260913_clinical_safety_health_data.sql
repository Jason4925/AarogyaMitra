CREATE TABLE IF NOT EXISTS public.safety_rules (
  id text PRIMARY KEY,
  name text NOT NULL,
  description text NOT NULL DEFAULT '',
  version text NOT NULL DEFAULT '1.0',
  status text NOT NULL DEFAULT 'draft',
  evidence_source text NOT NULL DEFAULT '',
  evidence_url text NOT NULL DEFAULT '',
  review_date text NOT NULL DEFAULT '',
  reviewer text NOT NULL DEFAULT '',
  applicable_population jsonb NOT NULL DEFAULT '[]'::jsonb,
  contraindications jsonb NOT NULL DEFAULT '[]'::jsonb,
  human_review_required boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS public.health_measurements (
  id text PRIMARY KEY, user_id text NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
  metric text NOT NULL, value text NOT NULL, unit text NOT NULL DEFAULT '', measured_at timestamptz NOT NULL DEFAULT now(),
  source text NOT NULL DEFAULT 'user', note text NOT NULL DEFAULT '', verified boolean NOT NULL DEFAULT false, provenance jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS public.health_documents (
  id text PRIMARY KEY, user_id text NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
  filename text NOT NULL, content_type text NOT NULL DEFAULT '', storage_path text NOT NULL DEFAULT '', extracted jsonb NOT NULL DEFAULT '{}'::jsonb,
  confirmed boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS public.handoff_shares (
  id text PRIMARY KEY, user_id text NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
  handoff_id text NOT NULL, access_code_hash text NOT NULL, token_hash text NOT NULL UNIQUE,
  expires_at timestamptz NOT NULL, revoked boolean NOT NULL DEFAULT false, accessed_at timestamptz,
  included jsonb NOT NULL DEFAULT '[]'::jsonb, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS public.caregiver_access (
  id text PRIMARY KEY, patient_user_id text NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
  caregiver_name text NOT NULL, caregiver_contact text NOT NULL DEFAULT '', permissions jsonb NOT NULL DEFAULT '[]'::jsonb,
  expires_at timestamptz, active boolean NOT NULL DEFAULT true, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS public.feedback_tickets (
  id text PRIMARY KEY, user_id text REFERENCES public.users(user_id) ON DELETE SET NULL,
  category text NOT NULL, severity text NOT NULL DEFAULT 'normal', description text NOT NULL, status text NOT NULL DEFAULT 'open',
  created_at timestamptz NOT NULL DEFAULT now(), resolved_at timestamptz
);
CREATE TABLE IF NOT EXISTS public.recommendation_records (
  id text PRIMARY KEY, user_id text NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
  text text NOT NULL, evidence_source text NOT NULL DEFAULT '', evidence_url text NOT NULL DEFAULT '',
  rule_version text NOT NULL DEFAULT '', model_version text NOT NULL DEFAULT '', confidence text NOT NULL DEFAULT 'medium',
  applicable_population jsonb NOT NULL DEFAULT '[]'::jsonb, contraindications jsonb NOT NULL DEFAULT '[]'::jsonb,
  human_review_required boolean NOT NULL DEFAULT true, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS public.emergency_acknowledgements (
  id text PRIMARY KEY, user_id text NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
  emergency_event_id bigint REFERENCES public.emergency_events(id) ON DELETE CASCADE,
  acknowledged boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS public.care_pathway_decisions (
  id text PRIMARY KEY, user_id text NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
  risk_level text NOT NULL, pathway text NOT NULL, rule_version text NOT NULL DEFAULT '', reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  human_review_required boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS public.clinical_labels (
  id text PRIMARY KEY, case_id text NOT NULL, reviewer text NOT NULL, reviewed_status text NOT NULL DEFAULT 'pending',
  expected_urgency text NOT NULL DEFAULT '', notes text NOT NULL DEFAULT '', rule_version text NOT NULL DEFAULT '', created_at timestamptz NOT NULL DEFAULT now()
);
