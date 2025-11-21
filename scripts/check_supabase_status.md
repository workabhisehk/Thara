# How to Check Supabase Project Status

If you're getting "could not translate host name" errors, your Supabase project might be **paused**.

## Steps to Check and Restore:

1. **Go to Supabase Dashboard**
   - Visit: https://supabase.com/dashboard
   - Sign in to your account

2. **Check Project Status**
   - Look at your project list
   - If you see a "Paused" badge or grayed-out project, it's inactive
   - Free tier projects pause after 1 week of inactivity

3. **Restore the Project**
   - Click on your paused project
   - Click the "Restore" or "Resume" button
   - Wait 1-2 minutes for the project to wake up

4. **Verify Connection String**
   - Go to: Settings → Database
   - Scroll to "Connection string"
   - Select "URI" format
   - Copy the connection string
   - Update your `.env` file with the new connection string (if it changed)

5. **Test Connection Again**
   ```bash
   source venv/bin/activate
   python scripts/test_db_connection.py
   ```

## Alternative: Check Connection Pooling

If your project uses connection pooling, try using the pooler URL:
- Go to: Settings → Database → Connection pooling
- Use the "Transaction" pooler mode URL
- It will have a different port (usually 6543 instead of 5432)

## Still Not Working?

- Verify you're using the correct project reference ID
- Check if you have the correct Supabase account
- Try connecting from Supabase's SQL Editor to verify the database is accessible

