# How to Get Correct Supabase Connection String

If your project is healthy but connection still fails, the connection string format might be wrong.

## Step 1: Get Connection String from Supabase Dashboard

1. Go to: **https://supabase.com/dashboard**
2. Select your project
3. Go to: **Settings → Database**
4. Scroll down to **"Connection string"** section
5. **IMPORTANT:** Click the **"URI"** tab (NOT "JDBC" or others)
6. Copy the entire connection string

## Expected Format

The connection string should look like one of these:

### Direct Connection (Port 5432):
```
postgresql://postgres.PROJECT_REF:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
```

### Connection Pooling (Port 6543):
```
postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres
```

## Key Things to Check:

1. **Username format:** Should be `postgres.PROJECT_REF` (NOT just `postgres`)
2. **Hostname format:** 
   - Direct: `db.PROJECT_REF.supabase.co`
   - Pooler: `aws-0-REGION.pooler.supabase.com`
3. **Port:** 
   - Direct: `5432`
   - Pooler: `6543`
4. **Password:** If it has special characters, URL-encode them

## Special Characters in Password

If your password has special characters, encode them:

| Character | Encoded |
|-----------|---------|
| `[` | `%5B` |
| `]` | `%5D` |
| `!` | `%21` |
| `$` | `%24` |
| `@` | `%40` |
| `#` | `%23` |
| `%` | `%25` |
| `&` | `%26` |
| `*` | `%2A` |
| `+` | `%2B` |
| `=` | `%3D` |
| `?` | `%3F` |

### How to encode:
```python
python3
from urllib.parse import quote
password = "[Abh!$h5k]"  # Your password
encoded = quote(password, safe='')
print(encoded)  # %5BAbh%21%24h5k%5D
```

## Try Connection Pooling Instead

If direct connection doesn't work:

1. Go to: **Settings → Database → Connection pooling**
2. Select **"Transaction"** mode
3. Copy the pooler connection string
4. Update your `.env` file with it

Pooler URLs are often more reliable and work better with certain network configurations.

## Verify Your .env File

Your `.env` file should have:
```bash
DATABASE_URL=postgresql://postgres.PROJECT_REF:ENCODED_PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
```

**Important:**
- No quotes around the URL
- No spaces around `=`
- Password should be URL-encoded if it has special characters
- Copy EXACTLY what Supabase shows (don't modify manually)

