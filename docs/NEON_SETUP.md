# Neon DB Setup Guide

This project uses **Neon DB** (serverless PostgreSQL) for the database and vector storage.

## Why Neon DB?

✅ Serverless PostgreSQL - scales automatically  
✅ Built-in pgvector support for vector embeddings  
✅ Generous free tier  
✅ No connection pooling issues  
✅ Standard PostgreSQL connection strings  

## Setup Instructions

### Step 1: Create Neon DB Account

1. Go to [Neon DB](https://neon.tech)
2. Sign up for a free account
3. Create a new project

### Step 2: Get Connection String

1. In your Neon project dashboard, click **"Connect"**
2. You'll see a connection string like:
   ```
   postgresql://username:password@ep-xxx-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
3. Copy this connection string

### Step 3: Enable pgvector Extension

1. Go to Neon Console → SQL Editor
2. Run this command:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Verify it's installed:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

### Step 4: Update .env File

Add or update your `.env` file:

```bash
# Neon DB Connection String
DATABASE_URL=postgresql://username:password@ep-xxx-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**Important Notes:**
- Use the **direct connection string** (not connection pooling)
- The connection string should include `?sslmode=require` for secure connections
- If your password has special characters, make sure they're URL-encoded

### Step 5: Test Connection

Run the test script:

```bash
source venv/bin/activate
python scripts/test_neon_connection.py
```

This will:
- Test DNS resolution
- Test database connection
- Verify pgvector extension is installed

### Step 6: Run Database Migrations

Once the connection works, run migrations:

```bash
# Create initial migration (if not already done)
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

## Connection String Format

Neon uses standard PostgreSQL connection strings:

```
postgresql://[user]:[password]@[host]:[port]/[database]?sslmode=require
```

Example:
```
postgresql://myuser:mypassword@ep-cool-darkness-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

## Features

### Database Branching

Neon supports database branching (like Git branches):
- Create branches for development/testing
- Useful for testing migrations
- See [Neon Branching Docs](https://neon.com/docs/guides/branching)

### Connection Pooling (Optional)

For high-traffic applications, Neon offers connection pooling:
- Go to Project Settings → Connection Pooling
- Use the pooled connection string for production
- Default direct connection is fine for most use cases

## Troubleshooting

### Connection Timeout

If connections timeout:
1. Check your network/firewall settings
2. Try using `?sslmode=require` in connection string
3. Verify project is active (not paused)

### DNS Resolution Failed

If DNS fails:
1. Double-check the hostname in connection string
2. Get a fresh connection string from Neon Console
3. Make sure project isn't deleted/paused

### pgvector Extension Not Found

If you get pgvector errors:
1. Go to SQL Editor in Neon Console
2. Run: `CREATE EXTENSION IF NOT EXISTS vector;`
3. Verify with: `SELECT * FROM pg_extension WHERE extname = 'vector';`

## Migration from Supabase

If migrating from Supabase:

1. **Export data** (if needed):
   ```bash
   pg_dump old_supabase_url > backup.sql
   ```

2. **Import to Neon**:
   ```bash
   psql your_neon_url < backup.sql
   ```

3. **Update .env** with Neon connection string

4. **Test connection** with test script

5. **Run migrations** if schema changed

## Resources

- [Neon Documentation](https://neon.com/docs)
- [Neon Console](https://console.neon.tech)
- [pgvector Documentation](https://github.com/pgvector/pgvector)

## Next Steps

After setting up Neon:

1. ✅ Test connection: `python scripts/test_neon_connection.py`
2. ✅ Run migrations: `alembic upgrade head`
3. ✅ Verify tables: Check in Neon Console SQL Editor
4. ✅ Test vector store: Run your application

