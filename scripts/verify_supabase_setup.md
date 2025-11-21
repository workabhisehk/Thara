# Supabase Connection Troubleshooting

## Current Issue: Hostname Cannot Be Resolved

The error "could not translate host name" means your Supabase project is likely **PAUSED**.

## Quick Fix Steps:

### 1. Check Supabase Dashboard
- Go to: https://supabase.com/dashboard
- Sign in
- Look for your project

### 2. Restore Paused Project
- If you see "Paused" or the project is grayed out:
  - Click on the project
  - Click "Restore" or "Resume" button
  - Wait 1-2 minutes

### 3. Get Correct Connection String
After restoring, get the fresh connection string:
- Go to: **Settings** → **Database**
- Scroll to **Connection string** section
- Select **URI** format (not Connection pooling)
- Copy the entire connection string

### 4. Update Your .env File
```bash
DATABASE_URL=postgresql://postgres.YOUR_PROJECT_REF:YOUR_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**Important:** If your password has special characters like `[`, `]`, `!`, `$`, they need to be URL-encoded:
- `[` → `%5B`
- `]` → `%5D`
- `!` → `%21`
- `$` → `%24`

Example:
- Password: `[Abh!$h5k]`
- URL-encoded: `%5BAbh%21%24h5k%5D`

### 5. Test Connection
```bash
source venv/bin/activate
python scripts/test_db_connection.py
```

### 6. Run Migration (Once Connection Works)
```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

## Alternative: Use Connection Pooling URL

If the direct connection doesn't work, try the pooler URL:
- Settings → Database → Connection pooling
- Use **Transaction** mode
- Port will be **6543** instead of **5432**

Format: `postgresql://postgres.YOUR_PROJECT_REF:YOUR_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres`

## Still Not Working?

1. **Verify Project Reference ID**
   - Make sure the hostname matches your project
   - Format: `db.YOUR_PROJECT_REF.supabase.co`

2. **Check Network/Firewall**
   - Try from a different network
   - Check if corporate firewall is blocking

3. **Verify Credentials**
   - Reset database password in Supabase if needed
   - Make sure you're using the correct password

4. **Check Supabase Status**
   - Visit: https://status.supabase.com/
   - See if there are any ongoing issues

