# Agent Framework Comparison: Parlant vs LangGraph

## Current Configuration

**Status**: Currently using **LangGraph** (Parlant is disabled by default)

To check your current setting:
```bash
grep -E "USE_PARLANT|USE_HYBRID_MODE" .env
```

### Configuration Options

- `USE_PARLANT=False` and `USE_HYBRID_MODE=False` → Using **LangGraph** (current default)
- `USE_PARLANT=True` and `USE_HYBRID_MODE=False` → Using **Parlant** only
- `USE_HYBRID_MODE=True` → Using **both Parlant and LangGraph** intelligently (recommended)

### Hybrid Mode (Recommended)

**Hybrid Mode** intelligently routes messages to the best framework:
- **Parlant** handles: Simple operations (task CRUD, calendar queries, direct tool calls)
- **LangGraph** handles: Complex workflows (onboarding, multi-step planning, multi-agent coordination)

To enable hybrid mode:
```env
USE_HYBRID_MODE=True
USE_PARLANT=False  # Can be either True/False when hybrid is enabled
```

## Architecture Comparison

### Without Parlant (LangGraph - Current Default)

```
User Message
    │
    ▼
[Telegram Handler] (telegram_bot/handlers/start.py)
    │
    ├─→ Check conversation state
    │
    ├─→ If in specific state (onboarding, task creation):
    │   └─→ Route to state-specific handler
    │
    └─→ If IDLE/NORMAL:
        │
        ▼
[LangGraph Multi-Agent System] (agents_langgraph/)
    │
    ├─→ Router Agent
    │   ├─→ Analyzes message
    │   └─→ Routes to appropriate agent:
    │       │
    │       ├─→ Task Agent
    │       │   ├─→ Handles task operations
    │       │   └─→ Uses task tools
    │       │
    │       ├─→ Calendar Agent
    │       │   ├─→ Handles calendar operations
    │       │   └─→ Uses calendar tools
    │       │
    │       ├─→ Onboarding Agent
    │       │   └─→ Guides new users
    │       │
    │       └─→ Human Agent
    │           └─→ Handles general conversation
    │
    └─→ State Machine
        ├─→ Maintains conversation state
        ├─→ Tracks agent transitions
        └─→ Stores context
        │
        ▼
[Business Logic] (tasks/, google_calendar/, etc.)
    │
    └─→ Execute actions
        │
        ▼
[Response Generation]
    │
    └─→ Send to user
```

**Characteristics:**
- ✅ Multi-agent system with specialized agents
- ✅ State machine for complex flows
- ✅ Explicit routing between agents
- ✅ More structured, predictable behavior
- ⚠️ More complex setup
- ⚠️ Requires more configuration

### With Parlant (Alternative)

```
User Message
    │
    ▼
[Telegram Handler] (telegram_bot/handlers/start.py)
    │
    ├─→ Check conversation state
    │
    ├─→ If in specific state (onboarding, task creation):
    │   └─→ Route to state-specific handler
    │
    └─→ If IDLE/NORMAL:
        │
        ▼
[Parlant Agent] (agents_parlant/)
    │
    ├─→ Single unified agent
    │   ├─→ Processes all messages
    │   ├─→ Uses rule-following framework
    │   └─→ Accesses tools directly
    │
    ├─→ Tool Selection
    │   ├─→ create_task
    │   ├─→ get_tasks
    │   ├─→ update_task
    │   ├─→ get_calendar_events
    │   └─→ schedule_event
    │
    └─→ Direct Tool Execution
        │
        ▼
[Business Logic] (tasks/, google_calendar/, etc.)
    │
    └─→ Execute actions
        │
        ▼
[Response Generation]
    │
    └─→ Send to user
```

**Characteristics:**
- ✅ Simpler, single-agent approach
- ✅ Rule-following framework
- ✅ Direct tool access
- ✅ Easier to understand and debug
- ⚠️ Less structured routing
- ⚠️ All logic in one agent

## Detailed Flow Comparison

### Example: "Add task: Write LOR tomorrow"

#### LangGraph Flow (Current)

```
1. User: "Add task: Write LOR tomorrow"
   │
   ▼
2. Telegram Handler → LangGraph Integration
   │
   ▼
3. Router Agent
   ├─→ Analyzes: intent="create_task"
   └─→ Routes to: Task Agent
   │
   ▼
4. Task Agent
   ├─→ Extracts entities:
   │   ├─→ title: "Write LOR"
   │   ├─→ due_date: "tomorrow"
   │   └─→ pillar: (AI categorization)
   ├─→ Uses tools:
   │   └─→ Calls task creation handler
   └─→ Generates confirmation
   │
   ▼
5. Natural Language Task Handler
   ├─→ Shows confirmation card
   └─→ "Is this correct?" with buttons
   │
   ▼
6. User: "category: other"
   │
   ▼
7. Telegram Handler
   ├─→ Detects pending task in context
   ├─→ Parses correction: category="other"
   ├─→ Updates context
   └─→ Re-shows confirmation
   │
   ▼
8. User: Clicks "Yes, Create"
   │
   ▼
9. Task Service → Database
   │
   ▼
10. Response: "✅ Task created!"
```

#### Parlant Flow (If Enabled)

```
1. User: "Add task: Write LOR tomorrow"
   │
   ▼
2. Telegram Handler → Parlant Adapter
   │
   ▼
3. Parlant Agent
   ├─→ Processes message
   ├─→ Identifies action: create_task
   ├─→ Extracts entities
   └─→ Calls tool: create_task()
   │
   ▼
4. Tool Execution
   ├─→ Task Service
   └─→ Database
   │
   ▼
5. Response Generation
   └─→ "✅ Task created: Write LOR"
```

## Key Differences

| Aspect | LangGraph (Current) | Parlant |
|--------|-------------------|---------|
| **Architecture** | Multi-agent system | Single agent |
| **Routing** | Explicit router agent | Direct processing |
| **State Management** | State machine | Conversation context |
| **Complexity** | Higher | Lower |
| **Flexibility** | High (specialized agents) | Medium (unified agent) |
| **Debugging** | More complex | Simpler |
| **Tool Access** | Through agents | Direct |
| **Best For** | Complex workflows | Simple, direct interactions |

## Code Locations

### LangGraph Implementation
- **Integration**: `agents_langgraph/integration.py`
- **Graph**: `agents_langgraph/graph.py`
- **Agents**: `agents_langgraph/agents/`
  - `router_agent.py` - Routes messages
  - `task_agent.py` - Task operations
  - `calendar_agent.py` - Calendar operations
  - `onboarding_agent.py` - Onboarding flow
  - `human_agent.py` - General conversation

### Parlant Implementation
- **Adapter**: `agents_parlant/telegram_adapter.py`
- **Agent**: `agents_parlant/agent.py`
- **Tools**: `agents_parlant/tools.py`

### Hybrid Implementation (Recommended)
- **Router**: `agents_hybrid/router.py`
- **Entry Point**: `agents_hybrid/router.py::handle_message_hybrid()`
- **Routing Logic**: Intelligently routes to Parlant or LangGraph based on:
  - Conversation state (onboarding → LangGraph)
  - Extracted intent (simple operations → Parlant, complex → LangGraph)
  - Keywords and message length heuristics
  - Multi-part request detection

## Switching Between Frameworks

### Enable Hybrid Mode (Recommended)

1. Edit `.env`:
   ```env
   USE_HYBRID_MODE=True
   USE_PARLANT=False  # Can be either True/False
   ```

2. Restart bot:
   ```bash
   ./scripts/restart_bot.sh
   ```

**How it works:**
- Simple operations (task CRUD, calendar queries) → **Parlant** (faster, simpler)
- Complex workflows (onboarding, multi-step planning) → **LangGraph** (better state management)
- Automatic routing based on message analysis

### Enable Parlant

1. Edit `.env`:
   ```env
   USE_PARLANT=True
   ```

2. Restart bot:
   ```bash
   ./scripts/restart_bot.sh
   ```

### Disable Parlant (Use LangGraph)

1. Edit `.env`:
   ```env
   USE_PARLANT=False
   ```

2. Restart bot:
   ```bash
   ./scripts/restart_bot.sh
   ```

## When to Use Each

### Use Hybrid Mode When (Recommended):
- ✅ You want the best of both worlds
- ✅ Simple operations should be fast (Parlant)
- ✅ Complex workflows need state management (LangGraph)
- ✅ Automatic intelligent routing is preferred
- ✅ You want optimal performance for each use case

### Use LangGraph When:
- ✅ You need specialized agents for different domains
- ✅ Complex state transitions are required
- ✅ You want explicit routing logic
- ✅ Multiple agents need to collaborate
- ✅ You need fine-grained control over agent behavior

### Use Parlant When:
- ✅ You want a simpler, unified approach
- ✅ Direct tool access is preferred
- ✅ Rule-following behavior is sufficient
- ✅ Easier debugging is important
- ✅ Single agent can handle all interactions

## Current Recommendation

**Hybrid Mode is recommended** because:
1. ✅ Best performance: Parlant for simple operations, LangGraph for complex workflows
2. ✅ Automatic intelligent routing based on message analysis
3. ✅ Leverages strengths of both frameworks
4. ✅ Fallback between frameworks if one fails
5. ✅ Best user experience with optimized response times

**LangGraph is the default** (when hybrid is disabled) because:
1. Better separation of concerns (specialized agents)
2. More structured for complex workflows
3. Better state management
4. More extensible for future features

**Parlant is available** as an alternative for:
- Simpler deployments
- Easier debugging
- Direct tool access preference

## Performance Comparison

### Single Framework Mode
Both frameworks have similar performance characteristics:
- Response time: Similar (both use same LLM)
- Memory usage: LangGraph slightly higher (state machine)
- Complexity: LangGraph more complex, Parlant simpler

### Hybrid Mode Performance
- **Simple operations** (Parlant): Faster response time, lower overhead
- **Complex workflows** (LangGraph): Better state management, multi-agent coordination
- **Overall**: Optimized for each use case, best user experience

## Migration Notes

The codebase supports both frameworks seamlessly:
- Same tools are used by both
- Same business logic layer
- Same database layer
- Switching is just a config change

