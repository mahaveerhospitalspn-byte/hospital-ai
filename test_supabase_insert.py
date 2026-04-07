import requests

SUPABASE_URL = "https://ptkdegqftfcaqrvsbihk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB0a2RlZ3FmdGZjYXFydnNiaWhrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxMjYzODUsImV4cCI6MjA5MDcwMjM4NX0.jI2mcxJ86uPaCExOmLEdN8XdEzctEul3-33Qc7Ug_dI"

data = {
"token":"1",
"uhid":"TEST123",
"name":"TEST PATIENT",
"doctor":"DR TEST",
"visit_type":"Normal",
"arrival_time":"10:30",
"status":"Waiting",
"date":"2026-04-07"
}

response = requests.post(

f"{SUPABASE_URL}/rest/v1/opd_live",

headers={
"apikey": SUPABASE_KEY,
"Authorization": f"Bearer {SUPABASE_KEY}",
"Content-Type": "application/json",
"Prefer":"return=representation"
},

json=data
)

print(response.status_code)
print(response.text)