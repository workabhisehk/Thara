# Hybrid Mode: Using Both Parlant and LangGraph

## Overview

**Hybrid Mode** intelligently routes messages to the best framework based on message complexity and intent:

- **Parlant**: Handles simple, direct operations (task CRUD, calendar queries)
- **LangGraph**: Handles complex workflows (onboarding, multi-step planning, multi-agent coordination)

## Quick Start

### Enable Hybrid Mode

1. Edit your `.env` file:
   ```env
   USE_HYBRID_MODE=True
   USE_PARLANT=False  # Can be either True/False when hybrid is enabled
   ```

2. Restart the bot:
   ```bash
   ./scripts/restart_bot.sh
   ```

That's it! The system will now automatically route messages to the best framework.

## How It Works

### Routing Logic

The hybrid router analyzes each message using multiple heuristics:

1. **Conversation State**
   - Onboarding state → **LangGraph** (multi-step, stateful)
   - Other states → Continue with analysis

2. **Intent Extraction**
   - Simple intents (task CRUD, calendar queries) → **Parlant**
   - Complex intents (onboarding, planning, insights) → **LangGraph**

3. **Keyword Matching**
   - Simple keywords: "add task", "calendar", "schedule" → **Parlant**
   - Complex keywords: "onboard", "plan", "review", "insights" → **LangGraph**

4. **Message Length**
   - Short messages (<20 chars) → **Parlant** (usually simple queries)
   - Long messages (>200 chars) → **LangGraph** (might be complex requests)

5. **Multi-Part Detection**
   - Contains "and", "then", "also", "next" → **LangGraph** (complex multi-step)

6. **Default**
   - If unsure → **Parlant** (simpler, faster for common operations)

### Examples

**Parlant Routes:**
- "Add task: Buy groceries"
- "Show my tasks"
- "What's on my calendar today?"
- "Schedule a meeting tomorrow at 2pm"

**LangGraph Routes:**
- "Help me plan my week"
- Onboarding messages
- "What should I focus on today?"
- "Give me insights on my productivity"

**Fallback:**
- If Parlant fails → Falls back to LangGraph
- If LangGraph fails → Falls back to natural language handler

## Configuration

### Environment Variables

```env
# Enable hybrid mode
USE_HYBRID_MODE=True

# Parlant setting (can be either True/False when hybrid is enabled)
USE_PARLANT=False
```

### Priority

1. If `USE_HYBRID_MODE=True` → Uses hybrid router
2. Else if `USE_PARLANT=True` → Uses Parlant only
3. Else → Uses LangGraph only (default)

## Benefits

✅ **Best Performance**: Simple operations use Parlant (faster), complex workflows use LangGraph (better state management)

✅ **Automatic Routing**: No manual configuration needed - the system decides

✅ **Resilient**: Automatic fallback if one framework fails

✅ **Optimized UX**: Users get the best experience for each type of operation

## Architecture

```
User Message
    │
    ▼
[Telegram Handler]
    │
    ├─→ Check: USE_HYBRID_MODE?
    │   │
    │   ├─→ Yes: [Hybrid Router]
    │   │        │
    │   │        ├─→ Analyze message
    │   │        │   ├─→ Simple operation? → [Parlant]
    │   │        │   └─→ Complex workflow? → [LangGraph]
    │   │        │
    │   │        └─→ Fallback: If Parlant fails → LangGraph
    │   │
    │   └─→ No: [Default Routing]
    │            ├─→ USE_PARLANT=True? → [Parlant]
    │            └─→ Else → [LangGraph]
```

## Files

- **Router**: `agents_hybrid/router.py`
- **Entry Point**: `agents_hybrid/router.py::handle_message_hybrid()`
- **Configuration**: `config.py` (adds `use_hybrid_mode` setting)
- **Integration**: `telegram_bot/handlers/start.py` (checks for hybrid mode)

## Troubleshooting

### Check Hybrid Mode Status

```bash
# Check configuration
grep -E "USE_HYBRID_MODE|USE_PARLANT" .env

# Check logs
grep "Hybrid Mode" logs/bot.log
```

### Verify Routing

Look for these log messages:
- `"Hybrid Mode: Processing message..."`
- `"Hybrid Router: Routing message..."`
- `"Hybrid Mode: Routing to Parlant"` or `"Hybrid Mode: Routing to LangGraph"`

### Disable Hybrid Mode

If you want to go back to single-framework mode:

```env
USE_HYBRID_MODE=False
USE_PARLANT=False  # or True for Parlant-only
```

## Comparison

| Mode | Simple Operations | Complex Workflows | Routing |
|------|------------------|-------------------|---------|
| **Hybrid** | Parlant (fast) | LangGraph (stateful) | Automatic |
| **Parlant Only** | Parlant | Parlant | All to Parlant |
| **LangGraph Only** | LangGraph | LangGraph | All to LangGraph |

## Recommendation

**Use Hybrid Mode** for production deployments. It provides:
- Best performance for simple operations
- Proper state management for complex workflows
- Automatic intelligent routing
- Resilient fallback mechanisms

