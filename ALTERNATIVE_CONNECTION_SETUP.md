# Alternative Database Connection Setup

Since direct PostgreSQL connection is failing (likely due to paused Supabase project), we've set up an alternative connection method using **Supabase REST API**.

## Benefits of Supabase REST API

✅ Works even if direct PostgreSQL connection fails  
✅ No DNS issues (uses HTTPS)  
✅ Works when Supabase project is paused or having network issues  
✅ Easier to use (no connection pooling needed)  
✅ Built-in security with Row Level Security (RLS)

## Setup Instructions

### Step 1: Get Supabase Credentials

1. Go to: https://supabase.com/dashboard
2. Select your project
3. Go to: **Settings → API**

You'll need:
- **Project URL** (looks like: `https://xvdfxjujaotozyjflxcb.supabase.co`)
- **anon public** key (long JWT token)

### Step 2: Update .env File

Add these lines to your `.env` file:

```bash
SUPABASE_URL=https://xvdfxjujaotozyjflxcb.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Replace:
- `xvdfxjujaotozyjflxcb` with your actual project reference
- The JWT token with your actual `anon public` key

### Step 3: Test Alternative Connection

Run the setup script:

```bash
source venv/bin/activate
python scripts/setup_alternative_connection.py
```

This will:
- Check if Supabase credentials are configured
- Test the REST API connection
- Show which connection methods are available

## Usage

Once configured, you can use the alternative connection:

```python
from database.alternative_connection import get_supabase_client, SupabaseDatabaseAdapter

# Get client
client = get_supabase_client()

# Use adapter for database operations
adapter = SupabaseDatabaseAdapter()

# Example: Select data
result = adapter.select('users', columns='*', filters={'id': 1})

# Example: Insert data
adapter.insert('tasks', {'title': 'Test task', 'status': 'pending'})

# Example: Update data
adapter.update('tasks', {'id': 1}, {'status': 'completed'})

# Example: Delete data
adapter.delete('tasks', {'id': 1})
```

## Connection Methods Available

1. **Direct PostgreSQL** (Current: ❌ DNS failing)
   - Uses `DATABASE_URL` with `psycopg2`
   - Requires active Supabase project
   - Works for Alembic migrations

2. **Supabase REST API** (Alternative: ✅ Works when configured)
   - Uses `SUPABASE_URL` and `SUPABASE_KEY`
   - Works even if direct connection fails
   - Good for application queries

3. **Connection Pooling** (Alternative)
   - Uses pooler hostname (`pooler.supabase.com`)
   - Different port (6543)
   - Often more reliable than direct connection

## When to Use Which Method

- **Direct PostgreSQL**: For migrations, complex queries, admin tasks
- **Supabase REST API**: For application queries, when direct connection fails
- **Connection Pooling**: Alternative to direct connection, more reliable

## Next Steps

1. Get Supabase credentials from dashboard
2. Add `SUPABASE_URL` and `SUPABASE_KEY` to `.env`
3. Test with `python scripts/setup_alternative_connection.py`
4. Update your application code to use alternative connection if needed

