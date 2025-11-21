# How to Get Supabase Credentials

## For Database Connection (Required)

You only need **DATABASE_URL** which you already have in your `.env` file.

The Supabase URL and Key are **optional** and only needed if you want to use Supabase REST API.

## For Supabase REST API (Optional)

If you want to use Supabase REST API as an alternative to direct database connection:

### Step 1: Get Supabase URL
1. Go to: https://supabase.com/dashboard
2. Select your project
3. Go to: **Settings → API**
4. Copy the **"Project URL"** (looks like: `https://xvdfxjujaotozyjflxcb.supabase.co`)
5. Add to `.env` as: `SUPABASE_URL=https://xvdfxjujaotozyjflxcb.supabase.co`

### Step 2: Get Supabase Key
1. In the same page (Settings → API)
2. Copy the **"anon public"** key
3. Add to `.env` as: `SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### Step 3: Update .env File

Add these lines to your `.env` file:
```bash
SUPABASE_URL=https://xvdfxjujaotozyjflxcb.supabase.co
SUPABASE_KEY=your_anon_key_here
```

**Note:** These are optional. The database connection uses `DATABASE_URL` only.

