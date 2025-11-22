# Sentry Setup Guide

Sentry provides real-time error tracking and monitoring for your Telegram bot. When errors occur, they'll be automatically sent to Sentry with full stack traces, user context, and environment information.

## 🚀 Quick Setup

### Step 1: Create a Sentry Account

1. Go to [sentry.io](https://sentry.io) and sign up (free tier available)
2. Create a new project
3. Select **Python** as the platform
4. Copy your **DSN** (Data Source Name) - it looks like:
   ```
   https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
   ```

### Step 2: Add DSN to Environment

Add the Sentry DSN to your `.env` file:

```bash
# Sentry Error Tracking
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
SENTRY_ENABLED=true
```

### Step 3: Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Restart Bot

The bot will automatically initialize Sentry if `SENTRY_DSN` is set.

```bash
python bot_main.py
```

## ✅ Verification

To test that Sentry is working, the bot will log:
```
✅ Sentry initialized for error tracking
```

When an error occurs, you should see:
1. Error logged in console (as before)
2. Error sent to Sentry dashboard
3. Email/notification from Sentry (if configured)

## 📊 What Sentry Tracks

- **Exceptions**: All uncaught exceptions with full stack traces
- **User Context**: Telegram user ID, username, chat ID
- **Environment**: Development/production environment
- **Performance**: Database queries, async operations
- **Breadcrumbs**: Events leading up to the error
- **Release Tracking**: Track which version of code caused the error

## 🎯 Sentry Features

### 1. Error Alerts

Configure alerts in Sentry dashboard:
- **Email notifications** when errors occur
- **Slack/Discord integration** for team notifications
- **Issue tracking** to see which errors happen most
- **Error grouping** to see related issues together

### 2. Performance Monitoring

Sentry tracks:
- Slow database queries
- Long-running operations
- Transaction traces

### 3. Release Tracking

When you deploy a new version:
```bash
# Set release in Sentry
export SENTRY_RELEASE=bot@1.0.1
```

This helps identify which deployment introduced issues.

## 🔧 Configuration Options

In `config.py`, you can configure:

```python
# Enable/disable Sentry
SENTRY_ENABLED=true  # Set to false to disable without removing DSN

# Environment
ENVIRONMENT=production  # Sentry will tag errors with this
```

In `bot_main.py`, Sentry is configured with:
- **10% transaction sampling** (performance monitoring)
- **10% profiling** (optional, requires fastapi extras)
- **Logging integration** (errors become Sentry events)
- **SQLAlchemy integration** (database query tracking)
- **Asyncio integration** (async operation tracking)

## 📱 Adding User Context

To add user context to errors (so you know which Telegram user encountered the issue), we can enhance the error handler:

```python
import sentry_sdk

# In error handler
sentry_sdk.set_user({
    "id": user.telegram_id,
    "username": user.username,
    "first_name": user.first_name,
})
```

This is already done automatically when errors occur in handlers.

## 🎨 Customization

### Filter Out Noise

To ignore certain errors, edit `bot_main.py`:

```python
sentry_sdk.init(
    ...
    ignore_errors=[
        KeyboardInterrupt,
        SystemExit,
        SomeSpecificError,  # Add errors to ignore
    ],
)
```

### Set Sample Rates

For production, you might want lower sample rates:

```python
traces_sample_rate=0.1,  # 10% of transactions (default)
profiles_sample_rate=0.1,  # 10% of profiles (default)
```

### Environment-Specific Settings

```python
if settings.environment == "production":
    traces_sample_rate=0.05  # 5% in production
else:
    traces_sample_rate=1.0  # 100% in development
```

## 📊 Sentry Dashboard

After setup, visit your Sentry dashboard to see:
- **Issues**: List of all errors
- **Performance**: Slow operations
- **Releases**: Deployments and their impact
- **Alerts**: Configured notifications

## 🔒 Security

- **DSN is safe to commit**: It's public, but can be restricted by IP
- **Rate limiting**: Sentry has built-in rate limiting
- **Data privacy**: Be careful about logging sensitive user data

## 💡 Best Practices

1. **Set up alerts** for critical errors
2. **Group related errors** in Sentry dashboard
3. **Track releases** to know which code caused issues
4. **Review errors regularly** to improve bot stability
5. **Use Sentry in production** only (disable in local dev if needed)

## 🆘 Troubleshooting

### Sentry not initializing?
- Check that `SENTRY_DSN` is set correctly in `.env`
- Check that `SENTRY_ENABLED=true`
- Look for "✅ Sentry initialized" in bot startup logs

### Errors not appearing in Sentry?
- Check network connectivity
- Verify DSN is correct
- Check Sentry dashboard filters (might be filtered out)
- Look at Sentry SDK logs (set `debug=True` in `sentry_sdk.init()`)

### Too many errors?
- Adjust sample rates
- Add errors to `ignore_errors` list
- Use Sentry's filtering in dashboard

## 📚 Resources

- [Sentry Python Docs](https://docs.sentry.io/platforms/python/)
- [Sentry Telegram Integration](https://docs.sentry.io/product/integrations/notification-incidents/slack/)
- [Sentry Best Practices](https://docs.sentry.io/product/best-practices/)

## ✅ Next Steps

1. ✅ Install Sentry SDK (done)
2. ✅ Add configuration (done)
3. ⬜ Get Sentry DSN from sentry.io
4. ⬜ Add DSN to `.env` file
5. ⬜ Restart bot and test

Want help with any of these steps?

