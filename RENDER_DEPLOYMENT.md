# Mahaveer Hospital AI — Render Deployment Guide

## Why files weren't saving
Render (and all cloud platforms) have an **ephemeral filesystem** — 
every redeploy wipes all files. The app has been updated to store 
everything in **Supabase** instead of local files.

---

## Step 1 — Set up Supabase Tables (ONE TIME ONLY)

1. Go to your Supabase dashboard → **SQL Editor**
2. Open and run the file: **`create_supabase_tables.sql`**
3. This creates all required tables: patients, vitals, medications,
   nursing_notes, ot_notes, ot_register, daycare_register, 
   blood_products, audit_trail, notifications, summary_approvals

---

## Step 2 — Set Environment Variables on Render

In your Render dashboard → your service → **Environment**:

| Key | Value |
|-----|-------|
| `SUPABASE_URL` | `https://ptkdegqftfcaqrvsbihk.supabase.co` |
| `SUPABASE_KEY` | your anon key from Supabase |

Then update `supabase_client.py` to read from env vars:
```python
import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
```

---

## Step 3 — PDFs (Certificates, Summaries)

PDFs are generated in memory fine — but cannot be saved to disk.
Two options:
- **Download directly** via `st.download_button` (already works)
- **Upload to Supabase Storage bucket** (ask if you need this)

---

## What now saves to Supabase (permanent)
✅ Patient admissions & discharges  
✅ Vitals logs  
✅ Medication logs  
✅ Nursing notes  
✅ OT notes  
✅ OT register  
✅ DayCare register  
✅ Blood product records  
✅ Audit trail  
✅ Notifications  
✅ User accounts  

## What still uses local disk (temporary — lost on redeploy)
⚠️ PDF files in `Records/` and `Certificates/` — offer download button instead
⚠️ `hospital.db` SQLite — OPD live data is already in Supabase `opd_live` table
