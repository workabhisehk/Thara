# Google Calendar Integration Setup

## Current Status

The `/calendar` command now works! It will:

1. ✅ **Check if you're connected** to Google Calendar
2. ✅ **Show OAuth link** if not connected
3. ✅ **Display your events** if connected

## Problem: Calendar Not Connected

If you see "Google Calendar Not Connected" when using `/calendar`, you need to:

### Step 1: Connect Your Google Calendar

1. **Send `/calendar` command** to the bot
2. **Click the authorization link** provided
3. **Authorize the bot** in Google (you'll be redirected)
4. **Copy the authorization code** from the redirect URL
5. **Complete the connection** (see Step 2)

### Step 2: Handle OAuth Callback

The bot needs to receive the OAuth callback. There are two ways:

#### Option A: Use OAuth Callback Handler (FastAPI)

If you have the FastAPI server running, the callback should be handled automatically.

#### Option B: Manual Connection (Temporary)

For testing, you can manually complete the connection:

1. After clicking the OAuth link, you'll be redirected to something like:
   ```
   http://localhost:8000/auth/callback?code=AUTHORIZATION_CODE&state=USER_ID
   ```

2. **Copy the `code` parameter** from the URL

3. **Use the connection script** (if we create one) or manually update the database

## Current Implementation

The calendar handler will:
- ✅ Check if `google_calendar_connected = True` in database
- ✅ If not connected: Show OAuth authorization URL
- ✅ If connected: Fetch events from Google Calendar API
- ✅ Display events grouped by date for next 7 days

## What Might Be Wrong

1. **Not connected yet** - You need to complete OAuth flow
2. **OAuth callback not handled** - Need FastAPI server running or manual connection
3. **Credentials expired** - Token refresh needed
4. **API not enabled** - Google Calendar API might not be enabled

## Quick Fix: Create Connection Script

Let me create a script to help connect your calendar!

