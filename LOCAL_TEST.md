# Local Deployment & Testing Guide

## Quick Start

### 1. Check Prerequisites

```bash
# Check Python version (3.11+ required)
python --version

# Check if virtual environment is active
which python  # Should show venv path

# If not in venv, activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

### 2. Install/Update Dependencies

```bash
# Install all dependencies including LangGraph
pip install -r requirements.txt

# Verify LangGraph is installed
pip show langgraph
```

### 3. Test LangGraph Setup

```bash
# Run test script to validate LangGraph setup
python scripts/test_langgraph_local.py
```

**Expected Output:**
```
============================================================
LangGraph Multi-Agent System - Local Test
============================================================
🔍 Testing imports...
  ✅ State imports OK
  ✅ Agent imports OK
  ✅ Graph imports OK
  ✅ Integration imports OK
...
✅ All core tests passed!
```

### 4. Configure Environment

Create/update `.env` file:

```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
OPENAI_API_KEY=your_openai_key
DATABASE_URL=postgresql://user:password@host:port/dbname

# Google Calendar (required for scheduling)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Optional
GEMINI_API_KEY=your_gemini_key  # Fallback LLM
SENTRY_DSN=your_sentry_dsn      # Error tracking
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 5. Setup Database

```bash
# Run migrations
alembic upgrade head

# Verify database connection
python -c "from database.connection import AsyncSessionLocal; print('✅ DB OK')"
```

### 6. Start the Bot

```bash
# Start bot (will use polling)
python bot_main.py
```

**Expected Output:**
```
============================================================
Starting AI Productivity Agent Bot
============================================================
✅ Environment validation passed
Creating Telegram application...
Setting up handlers...
✅ Bot ready to start polling
============================================================
👋 Hi! Starting bot...
```

## Testing LangGraph Agents

### Test 1: Basic Message Handling

1. **Open Telegram** and find your bot
2. **Send**: `/start`
3. **Expected**: Bot responds with onboarding flow
4. **Check logs**: Should see `Router: Analyzing intent...`

### Test 2: Onboarding Flow

1. **Send**: `/start`
2. **Follow onboarding**:
   - Select pillars (Work, Education, etc.)
   - Set work hours: `9 AM to 5 PM`
   - Set timezone: `PST` or select from list
3. **Expected**: OnboardingAgent handles all steps
4. **Check logs**: Should see `OnboardingAgent: Processing...`

### Test 3: Task Creation

1. **Send**: `Add task: Prepare presentation for meeting`
2. **Expected**: TaskAgent processes the message
3. **Check logs**: Should see `TaskAgent: Processing...` and `Intent=add_task`

### Test 4: Task Scheduling

1. **Send**: `Schedule my task for tomorrow at 2 PM`
2. **Expected**: TaskAgent hands off to CalendarAgent
3. **Check logs**: Should see `TaskAgent: Task scheduling requested, handing off to calendar_agent`

### Test 5: Calendar Operations

1. **Send**: `/calendar`
2. **Expected**: CalendarAgent handles calendar viewing
3. **Check logs**: Should see `CalendarAgent: Processing...`

### Test 6: Natural Language Understanding

1. **Send**: `Show me my tasks`
2. **Expected**: RouterAgent routes to TaskAgent
3. **Check logs**: Should see `Router: Intent=show_tasks, Confidence=...`

### Test 7: Multi-Agent Handoff

1. **Send**: `Add task: Review code and schedule it for tomorrow`
2. **Expected**: 
   - TaskAgent creates task
   - CalendarAgent schedules it
   - Response confirms both actions
3. **Check logs**: Should see handoff between agents

## Monitoring Agent Behavior

### Check Logs

Watch the logs for agent activity:

```bash
# Tail logs (if using file logging)
tail -f logs/bot.log

# Or watch console output for:
# - "Router: Analyzing intent..."
# - "TaskAgent: Processing..."
# - "CalendarAgent: Processing..."
# - "Handoff to: calendar_agent"
```

### Verify Agent Routing

Look for these log patterns:

```
Router: Analyzing intent for user 123, state: normal, message: ...
Router: Intent=add_task, Action=create_task, Confidence=0.85
Router: Routing to task_agent
TaskAgent: Processing for user 123, intent: add_task
```

### Verify Handoffs

Look for handoff patterns:

```
TaskAgent: Task scheduling requested, handing off to calendar_agent
CalendarAgent: Task scheduling handoff from task_agent
```

## Troubleshooting

### Issue: Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check if LangGraph is installed
pip show langgraph
```

### Issue: Graph Compilation Fails

```bash
# Check if all dependencies are installed
pip list | grep langgraph

# Try reinstalling
pip install langgraph>=0.2.0 --upgrade
```

### Issue: Agent Not Routing Correctly

1. **Check logs** for RouterAgent output
2. **Verify intent extraction** is working
3. **Check confidence scores** - low confidence may cause wrong routing

### Issue: Handoff Not Working

1. **Check state updates** in logs
2. **Verify handoff_to** field is set correctly
3. **Check graph edges** are configured properly

### Issue: Memory/Checkpointer Not Working

1. **Check thread_id** is set correctly (should be user_id)
2. **Verify checkpointer** is initialized in graph
3. **Check state persistence** in logs

## Quick Validation Commands

```bash
# Test imports
python -c "from agents_langgraph.state import AgentState; print('✅ OK')"

# Test graph compilation
python -c "from agents_langgraph.graph import get_graph; g = get_graph(); print('✅ Graph OK')"

# Test agent imports
python -c "from agents_langgraph.agents import router_agent; print('✅ Agents OK')"

# Test integration
python -c "from agents_langgraph.integration import handle_message_with_langgraph; print('✅ Integration OK')"
```

## Testing Checklist

- [ ] All imports work (`test_langgraph_local.py` passes)
- [ ] Graph compiles successfully
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Bot starts without errors
- [ ] `/start` command works
- [ ] Onboarding flow completes
- [ ] Task creation works (natural language)
- [ ] Task scheduling hands off to CalendarAgent
- [ ] Calendar operations work
- [ ] Multi-agent handoffs work
- [ ] Logs show agent activity

## Next Steps

Once local testing passes:

1. **Test all use cases** from COMPREHENSIVE_PLAN.md
2. **Monitor agent performance** and routing accuracy
3. **Test edge cases** (errors, low confidence, etc.)
4. **Optimize agent prompts** based on behavior
5. **Deploy to production** when ready

## Support

If you encounter issues:

1. Check logs for detailed error messages
2. Verify environment variables are set correctly
3. Ensure all dependencies are installed
4. Check database connection
5. Review agent-specific logs for routing issues

