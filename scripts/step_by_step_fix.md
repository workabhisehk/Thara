# Step-by-Step Fix for Supabase Connection

## Current Problem
Your Supabase project is **PAUSED**, so DNS resolution fails.

## Fix Steps (Do These in Order)

### ✅ Step 1: Restore Supabase Project

1. Open your browser
2. Go to: **https://supabase.com/dashboard**
3. Sign in to your Supabase account
4. Look at your projects list
5. Find your project - it will show:
   - A **"Paused"** badge, OR
   - The project will be grayed out
6. Click on the paused project
7. Click the **"Restore"** or **"Resume"** button
8. **Wait 1-2 minutes** for the project to fully wake up
9. You should see the project become active (green, normal color)

### ✅ Step 2: Get Fresh Connection String

**After the project is restored:**

1. In your Supabase project dashboard
2. Click **"Settings"** in the left sidebar
3. Click **"Database"** (under Settings)
4. Scroll down to **"Connection string"** section
5. Click the **"URI"** tab (NOT "JDBC" or other tabs)
6. You should see something like:
   ```
   postgresql://postgres.PROJECT_REF:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
   ```
7. Click the **"Copy"** button to copy the entire string

### ✅ Step 3: Update Your .env File

1. Open your project folder in a terminal/editor
2. Open the `.env` file
3. Find the line that says `DATABASE_URL=`
4. Replace everything after `DATABASE_URL=` with the connection string you copied
5. **Important:** Make sure the line looks like this (with NO spaces around `=`):
   ```
   DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
   ```
6. **If your password has special characters**, you need to URL-encode them:
   - Open a Python terminal:
     ```bash
     python3
     ```
   - Then run:
     ```python
     from urllib.parse import quote
     password = "[Abh!$h5k]"  # Replace with your actual password
     encoded = quote(password, safe='')
     print(encoded)  # This will show: %5BAbh%21%24h5k%5D
     exit()
     ```
   - Replace your password in the connection string with the encoded version
7. Save the `.env` file

### ✅ Step 4: Test Connection

Run this command to test:
```bash
source venv/bin/activate
python scripts/test_db_connection.py
```

**Expected output if successful:**
```
✅ Hostname resolves to: SOME_IP_ADDRESS
✅ Connection successful!
✅ Database version: ...
```

### ✅ Step 5: Run Database Migration (Once Connection Works)

Once the connection test passes:
```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

## Troubleshooting

### If Step 1 fails (Can't find project):
- Make sure you're logged into the correct Supabase account
- Check your email for Supabase project creation email
- You might need to create a new project if you lost access

### If Step 2 fails (Can't find connection string):
- Make sure you're in **Settings → Database** (not General)
- Scroll down past the other settings
- Look for **"Connection string"** section

### If Step 3 fails (Connection string format wrong):
- Make sure it starts with `postgresql://`
- Make sure it has `postgres.` before the PROJECT_REF in the username part
- Make sure the hostname is `db.PROJECT_REF.supabase.co`
- Make sure the port is `5432`
- Make sure special characters in password are URL-encoded

### If Step 4 still fails after all steps:
- Wait 2-3 more minutes (project might still be waking up)
- Try the connection pooling URL (Settings → Database → Connection pooling)
- Double-check the connection string matches exactly what Supabase shows
- Verify your password is correct (you might need to reset it in Supabase)

---

## Alternative: Use Connection Pooling

If direct connection doesn't work, try connection pooling:

1. Go to **Settings → Database → Connection pooling**
2. Select **"Transaction"** mode
3. Copy the pooler connection string
4. It will have a different hostname: `aws-0-REGION.pooler.supabase.com`
5. And a different port: `6543`
6. Use this in your `.env` file instead

---

## Quick Verification Checklist

Before testing, make sure:
- [ ] Project is restored in Supabase dashboard
- [ ] Project shows as "Active" (not "Paused")
- [ ] Connection string copied from Supabase Settings → Database → URI tab
- [ ] `.env` file updated with correct `DATABASE_URL`
- [ ] Password special characters are URL-encoded (if any)
- [ ] No extra spaces or quotes around the connection string
- [ ] Waited 1-2 minutes after restoring project

