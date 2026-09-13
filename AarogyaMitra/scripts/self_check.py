"""AarogyaMitra deployment self-check.
Does not print secret environment variables.
"""
import os, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    print("AarogyaMitra self-check")
    print("="*28)
    required = [
        ROOT/"backend"/"main.py",
        ROOT/"backend"/"db.py",
        ROOT/"backend"/"auth.py",
        ROOT/"backend"/"risk_engine.py",
        ROOT/"backend"/"assessment.py",
        ROOT/"backend"/"handoff.py",
        ROOT/"web"/"dashboard.html",
        ROOT/"web"/"assessment.html",
        ROOT/"web"/"report.html",
        ROOT/"web"/"handoff.html",
        ROOT/"supabase"/"schema.sql",
        ROOT/".env.example",
    ]
    missing=[str(p.relative_to(ROOT)) for p in required if not p.exists()]
    print("Required files:", "OK" if not missing else "MISSING")
    if missing:
        print("\n".join(missing))
        return 1

    db_url=os.getenv("DATABASE_URL","").strip()
    print("DATABASE_URL:", "configured" if db_url else "not configured (local SQLite fallback)")
    print("GROQ_API_KEY:", "configured" if os.getenv("GROQ_API_KEY") else "not configured (assessment uses safe fallback)")
    print("GOOGLE_MAPS_API_KEY:", "configured" if os.getenv("GOOGLE_MAPS_API_KEY") else "not configured")
    print("TWILIO_ACCOUNT_SID:", "configured" if os.getenv("TWILIO_ACCOUNT_SID") else "not configured")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
