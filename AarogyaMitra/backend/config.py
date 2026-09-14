import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

TWILIO_ACCOUNT_SID=os.getenv('TWILIO_ACCOUNT_SID','')
TWILIO_AUTH_TOKEN=os.getenv('TWILIO_AUTH_TOKEN','')
TWILIO_VOICE_FROM=os.getenv('TWILIO_VOICE_FROM','')
TWILIO_EMERGENCY_CONTACT=os.getenv('TWILIO_EMERGENCY_CONTACT','')
GOOGLE_MAPS_API_KEY=os.getenv('GOOGLE_MAPS_API_KEY','')
GROQ_API_KEY=os.getenv('GROQ_API_KEY','')
ADMIN_EMAIL=os.getenv('ADMIN_EMAIL','admin@aarogyamitra.local')
ADMIN_PASSWORD=os.getenv('ADMIN_PASSWORD','change-this-admin-password')
JWT_SECRET=os.getenv('JWT_SECRET','change-this-jwt-secret-in-production')
JWT_ALGORITHM='HS256'
SESSION_HOURS=int(os.getenv('SESSION_HOURS','12'))
RATE_LIMIT_MAX=int(os.getenv('RATE_LIMIT_MAX','120'))
RATE_LIMIT_WINDOW=int(os.getenv('RATE_LIMIT_WINDOW','60'))
MAX_REQUEST_BYTES=int(os.getenv('MAX_REQUEST_BYTES','1000000'))
FRONTEND_ORIGINS=[x.strip() for x in os.getenv('FRONTEND_ORIGINS','https://aarogya-mitra-ten.vercel.app,http://localhost:5500,http://127.0.0.1:5500').split(',') if x.strip()]
DATABASE_URL=os.getenv('DATABASE_URL','').strip()
DATABASE_POOLING=os.getenv('DATABASE_POOLING','true').lower()=='true'
SUPABASE_URL=os.getenv('SUPABASE_URL','')
SUPABASE_PUBLISHABLE_KEY=os.getenv('SUPABASE_PUBLISHABLE_KEY','')
SUPABASE_SERVICE_KEY=os.getenv('SUPABASE_SERVICE_KEY','')
SUPABASE_STORAGE_BUCKET=os.getenv('SUPABASE_STORAGE_BUCKET','aarogyamitra-reports')
