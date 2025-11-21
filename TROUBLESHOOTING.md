# Supabase Connection Troubleshooting Guide

## Current Error: "could not translate host name"

This error means your Supabase hostname cannot be resolved by DNS. Here are all possible causes and fixes:

---

## Solution 1: Restore Paused Project (Most Common)

**Supabase free tier projects pause after 7 days of inactivity.**

### Steps:
1. **Go to Supabase Dashboard**
   - Visit: https://supabase.com/dashboard
   - Sign in with your account

2. **Check Project Status**
   - Look at your project list
   - If you see "Paused" badge or grayed-out project → it's inactive

3. **Restore Project**
   - Click on the paused project
   - Click **"Restore"** or **"Resume"** button
   - Wait **1-2 minutes** for it to fully wake up

4. **Verify Project is Active**
   - The project should show as "Active" (green badge)
   - Dashboard should be accessible

5. **Get Fresh Connection String**
   - Go to: **Settings → Database**
   - Scroll to **"Connection string"** section
   - Select **"URI"** tab (not "JDBC" or others)
   - Click **"Copy"** button
   - Format should be: `postgresql://postgres.PROJECT_REF:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres`

6. **Update Your .env File**
   ```bash
   # Edit .env file
   nano .env  # or use your preferred editor
   
   # Update DATABASE_URL line with the new connection string
   DATABASE_URL=postgresql://postgres.YOUR_PROJECT_REF:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres
   ```
   
   **Important:** If password has special characters, URL-encode them:
   - `[` → `%5B`
   - `]` → `%5D`
   - `!` → `%21`
   - `$` → `%24`
   - Space → `%20`

7. **Test Connection**
   ```bash
   source venv/bin/activate
   python scripts/test_db_connection.py
   ```

---

## Solution 2: Verify Connection String Format

Make sure your connection string matches Supabase's format exactly.

### Correct Format:
```
postgresql://postgres.PROJECT_REF:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
```

### Common Issues:
- ❌ Wrong hostname format
- ❌ Missing `postgres.` prefix before PROJECT_REF
- ❌ Wrong port (should be `5432` for direct connection)
- ❌ Password not URL-encoded (if it has special characters)

### How to Get Correct Format:
1. Go to Supabase Dashboard
2. Select your project
3. Go to **Settings → Database**
4. Scroll to **"Connection string"**
5. Click **"URI"** tab
6. Copy the entire string

---

## Solution 3: Use Connection Pooling (Alternative)

If direct connection doesn't work, try connection pooling:

### Steps:
1. Go to Supabase Dashboard → **Settings → Database**
2. Scroll to **"Connection pooling"** section
3. Select **"Transaction"** mode
4. Copy the **pooler connection string**
5. Format will be: `postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres`
   - Notice: Different hostname (`pooler.supabase.com`)
   - Different port (`6543` instead of `5432`)

### Update .env:
```bash
DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres
```

---

## Solution 4: Verify Project Reference ID

Make sure you're using the correct project reference ID.

### How to Find It:
1. Go to Supabase Dashboard
2. Select your project
3. Go to **Settings → General**
4. Look for **"Reference ID"** (should be something like `xvdfxjujaotozyjflxcb`)

### Check Your Connection String:
The hostname should be: `db.YOUR_REFERENCE_ID.supabase.co`

Example: `db.xvdfxjujaotozyjflxcb.supabase.co`

---

## Solution 5: Check Network/Firewall

If DNS resolution still fails after restoring:

1. **Try Different Network**
   - Try from home network vs work network
   - Check if corporate firewall blocks Supabase

2. **Test DNS Manually**
   ```bash
   nslookup db.YOUR_PROJECT_REF.supabase.co
   ```
   - Should return an IP address
   - If it doesn't, project is likely paused

3. **Check Supabase Status**
   - Visit: https://status.supabase.com/
   - See if there are any ongoing issues

---

## Solution 6: Reset Database Password

If connection string is correct but still failing:

1. Go to Supabase Dashboard → **Settings → Database**
2. Scroll to **"Database password"**
3. Click **"Reset database password"**
4. Save the new password
5. Update your `.env` file with the new password (URL-encoded if needed)

---

## Solution 7: Verify Your Supabase Account

Make sure:
- You're signed into the correct Supabase account
- The project belongs to your account
- You have access to the project

---

## Quick Diagnostic Commands

Run these to diagnose:

```bash
# 1. Check if .env file exists and has DATABASE_URL
cat .env | grep DATABASE_URL

# 2. Test DNS resolution
nslookup db.YOUR_PROJECT_REF.supabase.co

# 3. Run connection test
source venv/bin/activate
python scripts/test_db_connection.py

# 4. Run diagnostic script
bash scripts/fix_supabase_connection.sh
```

---

## Still Not Working?

If none of the above work:

1. **Create a New Supabase Project** (as last resort)
   - Create a fresh project
   - Get the new connection string
   - Update your `.env` file

2. **Contact Supabase Support**
   - Check if there's an account issue
   - Verify project status

3. **Try Alternative Database**
   - Temporarily use local PostgreSQL for development
   - Or use another hosting service

---

## Next Steps After Connection Works

Once connection is successful:

1. **Run Database Migrations**
   ```bash
   alembic revision --autogenerate -m "Initial schema"
   alembic upgrade head
   ```

2. **Verify Tables Created**
   ```bash
   python scripts/test_db_connection.py
   ```

3. **Continue with Setup**
   - Follow `docs/TODO.md` for next steps

