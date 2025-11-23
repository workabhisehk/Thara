# Calendar Integration Status

## Current Status: ✅ Code Ready, ⚠️ Needs OAuth Connection

The calendar integration code is **fully implemented** and ready to use, but users need to **connect their Google Calendar** via OAuth first.

## What Works

✅ **Calendar Handler** (`telegram_bot/handlers/calendar_handler.py`)
- Checks if calendar is connected
- Provides OAuth authorization URL
- Fetches and displays events when connected

✅ **Calendar Client** (`google_calendar/client.py`)
- List events
- Create events
- Update events
- Delete events

✅ **OAuth Authentication** (`google_calendar/auth.py`)
- Generate authorization URLs
- Handle OAuth callbacks
- Store and refresh credentials

✅ **Parlant Agent Integration** (`agents_parlant/tools.py`)
- `get_calendar_events` tool
- `create_calendar_event` tool
- Connection status checking
- Helpful error messages

## What Users Need to Do

### Step 1: Connect Google Calendar

1. **Send `/calendar` command** to the bot
2. **Click the authorization link** provided
3. **Authorize the bot** in Google
4. **Complete OAuth callback** (see below)

### Step 2: Handle OAuth Callback

The OAuth callback needs to be handled. There are two options:

#### Option A: FastAPI Server (Recommended)

If you have the FastAPI server running (`main.py`), it should handle the callback automatically at:
```
http://your-domain/auth/callback?code=...&state=...
```

#### Option B: Manual Connection Script

For local testing, you can use a script to complete the connection:

```python
# scripts/connect_calendar.py
import asyncio
from database.connection import AsyncSessionLocal
from google_calendar.auth import handle_oauth_callback

async def connect_calendar(telegram_id: int, auth_code: str):
    async with AsyncSessionLocal() as session:
        # Get user
        from database.models import User
        from sqlalchemy import select
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User {telegram_id} not found")
            return
        
        # Handle callback
        success = await handle_oauth_callback(session, auth_code, user.id)
        if success:
            print(f"✅ Calendar connected for user {user.id}")
        else:
            print("❌ Failed to connect calendar")

# Usage:
# asyncio.run(connect_calendar(8230716061, "AUTHORIZATION_CODE"))
```

## How It Works

### Flow Diagram

```
User: "can you access my calendar"
    │
    ▼
[Parlant Agent]
    │
    ├─→ Uses get_calendar_events tool
    │
    ▼
[Tool Checks Connection]
    │
    ├─→ Connected? → Fetch events → Display
    │
    └─→ Not Connected? → Provide OAuth link
        │
        ▼
User: Clicks link → Authorizes → OAuth callback
    │
    ▼
[Store Credentials]
    │
    ▼
User: "show my calendar" → Events displayed ✅
```

### Database Schema

The `users` table has these calendar fields:
- `google_calendar_connected` (Boolean) - Connection status
- `google_access_token` (Text) - OAuth access token
- `google_refresh_token` (Text) - OAuth refresh token
- `google_token_expires_at` (DateTime) - Token expiration

### OAuth Configuration

Required environment variables:
```env
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://your-domain/auth/callback
```

## Troubleshooting

### Issue: "I can't access your calendar directly"

**Cause**: Calendar not connected via OAuth

**Fix**: 
1. Use `/calendar` command to get OAuth link
2. Complete authorization
3. Handle OAuth callback

### Issue: "Calendar not connected" error

**Cause**: `google_calendar_connected = False` in database

**Fix**: Complete OAuth flow

### Issue: "Error getting events"

**Cause**: 
- Token expired (should auto-refresh)
- API not enabled
- Invalid credentials

**Fix**: 
1. Check Google Cloud Console - Calendar API enabled
2. Re-authorize if needed
3. Check logs for specific error

## Testing Calendar Integration

### 1. Check Connection Status

```python
# Check if user's calendar is connected
async with AsyncSessionLocal() as session:
    from database.models import User
    from sqlalchemy import select
    stmt = select(User).where(User.telegram_id == YOUR_TELEGRAM_ID)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    print(f"Connected: {user.google_calendar_connected}")
```

### 2. Test Event Listing

```python
from google_calendar.client import list_events

async with AsyncSessionLocal() as session:
    events = await list_events(session, user_id, max_results=10)
    print(f"Found {len(events)} events")
```

### 3. Test OAuth URL Generation

```python
from google_calendar.auth import get_authorization_url

auth_url = get_authorization_url(user_id)
print(f"Auth URL: {auth_url}")
```

## Next Steps

1. ✅ Code is ready
2. ⚠️ Users need to connect via OAuth
3. ⚠️ OAuth callback handler needs to be accessible
4. ✅ Parlant agent will guide users through connection

## Quick Fix for Testing

If you want to test calendar features without OAuth:

1. Manually set `google_calendar_connected = True` in database (not recommended for production)
2. Or complete the OAuth flow properly

The recommended approach is to complete the OAuth flow as designed.

