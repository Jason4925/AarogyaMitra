# AarogyaMitra

AarogyaMitra is an AI-assisted health information and personal health intelligence platform with a separate web frontend and Python/FastAPI backend.

> **Medical safety:** AarogyaMitra provides informational and workflow support. It is not a diagnostic service and does not replace professional medical care. Risk scores communicate **urgency**, not probability of disease.

## Core capabilities

### Patient
- AI health chat and user-specific conversation memory
- 5-step health assessment
- Dynamic urgency/risk engine
- Explainable risk factors
- Health reports
- Care plans and care pathways
- Longitudinal health record and timeline
- Intelligent follow-ups
- Healthcare facility routing
- Public-health awareness
- Vaccination guidance
- AI-to-doctor handoff
- Emergency escalation and caregiver/family calling
- Security and privacy controls
- Accessibility and regional-language support

### AI safety and governance
- Deterministic safety layer outside the LLM
- AI safety validation and red-team testing
- Benchmark/evaluation history
- Evidence/source governance
- Recommendation provenance
- Clinical-safety rule metadata
- Human-review requirements for high-risk or uncertain situations

### Admin
- User/patient operations
- AI performance and safety analytics
- AI benchmark and red-team evaluation
- Population-health analytics
- Early-warning symptom signals
- Knowledge governance
- Audit logging
- Database health monitoring

### Infrastructure
- PostgreSQL/Supabase persistence
- Supabase Storage and Realtime support
- FHIR bundle export prototype
- Vercel-ready frontend
- Render-ready FastAPI backend
- Environment-based configuration
- Database migrations

## Architecture

```text
Browser
  |
  v
Web Frontend
(HTML + CSS + JavaScript)
  |
  v
FastAPI Backend
  |
  +--> AI / Safety / Risk / Retrieval
  |
  +--> PostgreSQL (Supabase)
  |
  +--> Supabase Storage / Realtime
  |
  +--> Google Places / Maps
  |
  +--> Twilio
  |
  +--> Groq
```

## Project structure

```text
AarogyaMitra/
├── backend/
├── web/
├── knowledge/
├── scripts/
├── tests/
├── supabase/
├── .env.example
├── .gitignore
├── Dockerfile
├── pyproject.toml
├── requirements.txt
├── render.yaml
├── vercel.json
├── README.md
├── DEPLOYMENT.md
├── DEPLOYMENT_SECURITY.md
├── PROFESSIONAL_ROADMAP.md
└── CHANGELOG.md
```

## Local development

### Requirements

- Python 3.12+
- `uv` (recommended) or `pip`
- PostgreSQL/Supabase for production
- API credentials only for integrations you use

### Install with uv

```powershell
uv venv
.\.venv\Scripts\Activate.ps1
uv sync
```

### Install with pip

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Configuration

Copy:

```text
.env.example
```

to:

```text
.env
```

Never commit `.env`.

### Start backend

```powershell
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Start frontend

In another terminal:

```powershell
cd web
python -m http.server 5500
```

Open:

```text
http://localhost:5500
```

## Testing

Run:

```powershell
uv run pytest -q
```

Run the stability checks:

```powershell
uv run python scripts/stability_check.py
```

## Production data

Production persistence should use PostgreSQL/Supabase. Primary production records should not depend on JSON files.

Common database areas include:

- users
- conversations
- health_states
- reports
- health_timeline
- followups
- handoffs
- emergency_events
- ai_events / evaluations
- audit_logs
- consents
- safety_rules
- health_measurements
- health_documents
- handoff_shares
- caregiver_access
- feedback_tickets

## Secrets

Keep database passwords, Supabase secret/service-role keys, Twilio tokens, Groq private keys, and server-side Google credentials on the backend/platform secret manager.

## Medical disclaimer

Medical decisions must be made by appropriately qualified healthcare professionals.

## Author
### Jeetesh Nehete

##  Support

If you found this project useful, consider giving it a ⭐ on GitHub!