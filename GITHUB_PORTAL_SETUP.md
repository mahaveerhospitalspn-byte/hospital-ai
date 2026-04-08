# GitHub Push Portal — Setup Guide

## What It Does
Watches your `Hospital_AI` folder on your Desktop.
When you save any `.py` file, it automatically:
1. Stages the changes (`git add .`)
2. Commits with a timestamp
3. Pushes to GitHub
4. Render sees the push → auto-redeploys your app in ~60 seconds

---

## One-Time Setup

### Step 1 — Install Git
Download from: https://git-scm.com/download/win  
(tick "Add git to PATH" during install)

### Step 2 — Install Python packages
Open Command Prompt and run:
```
pip install watchdog gitpython
```

### Step 3 — Get a GitHub Token
1. Go to github.com → Login
2. Click your profile picture → **Settings**
3. Scroll down → **Developer settings**
4. **Personal access tokens** → **Tokens (classic)**
5. **Generate new token** → tick **repo** (full control)
6. Copy the token (starts with `ghp_...`)
7. Paste it into the portal's **GitHub Token** field

### Step 4 — Set your Repo URL
In the portal, set:
```
https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```
Example:
```
https://github.com/siddharth-rastogi/hospital-ai.git
```

### Step 5 — First push (if repo is new)
If you haven't pushed before:
1. Create a repo on github.com (name it `hospital-ai` or similar)
2. Don't tick "Add README"
3. Paste the `.git` URL into the portal
4. Click **Push Now**

---

## Daily Use
1. Double-click `Start_GitHub_Portal.bat`
2. Click **▶ Start Watching**
3. Edit and save any `.py` file as normal
4. Portal auto-pushes after 8 seconds of inactivity
5. Check Render dashboard — redeploy starts in ~60 seconds

---

## What Gets Pushed (Safe)
✅ All `.py` files  
✅ `requirements.txt`, `runtime.txt`  
✅ `render.yaml`, `Procfile`  
✅ `.sql` migration files  

## What is BLOCKED by .gitignore (Never Pushed)
🚫 `Patients_Data.csv` — patient data  
🚫 `users.csv` — login credentials  
🚫 `hospital.db` — local database  
🚫 `Records/` folder — patient files  
🚫 `Certificates/` — PDFs  
🚫 `Audit_Trail.csv` — sensitive logs  
