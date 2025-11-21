# Quick Fix: Connection String Format

## The Problem

Your `.env` file has the **wrong username format** in the DATABASE_URL.

## Current (WRONG):
```
DATABASE_URL=postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
```

## Should Be (CORRECT):
```
DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
```

**Notice:** Username is `postgres.PROJECT_REF` not just `postgres`

## How to Fix (2 Steps)

### Step 1: Get Correct Connection String from Supabase

1. Go to: https://supabase.com/dashboard
2. Select your project
3. Go to: **Settings → Database**
4. Scroll to **"Connection string"** section
5. **Click the "URI" tab** (NOT "JDBC" or "Connection pooling")
6. **Copy the entire connection string** shown

It will look like:
```
postgresql://postgres.xvdfxjujaotozyjflxcb:YOUR_PASSWORD@db.xvdfxjujaotozyjflxcb.supabase.co:5432/postgres
```

### Step 2: Update Your .env File

1. Open `.env` file in your project
2. Find the line: `DATABASE_URL=`
3. **Replace everything after `=`** with the connection string you copied
4. Make sure there are **NO quotes** around it
5. Make sure there are **NO spaces** around `=`
6. Save the file

**Example:**
```bash
# Before (WRONG):
DATABASE_URL=postgresql://postgres:PASSWORD@db.xvdfxjujaotozyjflxcb.supabase.co:5432/postgres

# After (CORRECT):
DATABASE_URL=postgresql://postgres.xvdfxjujaotozyjflxcb:PASSWORD@db.xvdfxjujaotozyjflxcb.supabase.co:5432/postgres
```

### Step 3: Test

```bash
source venv/bin/activate
python scripts/fix_connection_string.py
```

This will show you if the format is correct now.

Then test connection:
```bash
python scripts/test_connection_string.py
```

## Alternative: Use Connection Pooling

If direct connection doesn't work, try connection pooling:

1. Go to: **Settings → Database → Connection pooling**
2. Select **"Transaction"** mode
3. Copy the pooler connection string
4. Update `.env` with it

Pooler URL format:
```
postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres
```

## Still Not Working?

Run this diagnostic:
```bash
python scripts/debug_env_file.py
```

This will show exactly what's in your `.env` file and how it's being read.

