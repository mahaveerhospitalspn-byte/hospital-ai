import os
from supabase import create_client

# Reads from Render environment variables (set in Render dashboard)
# Falls back to hardcoded values for local development
SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "https://ptkdegqftfcaqrvsbihk.supabase.co"
)
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB0a2RlZ3FmdGZjYXFydnNiaWhrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxMjYzODUsImV4cCI6MjA5MDcwMjM4NX0.jI2mcxJ86uPaCExOmLEdN8XdEzctEul3-33Qc7Ug_dI"
)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
