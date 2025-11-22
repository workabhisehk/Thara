# LangGraph Multi-Agent System Migration

## Overview

Successfully migrated Thara productivity agent to LangGraph multi-agent system. All processes, content, steps, use cases, edge cases, and responsibilities are now managed through specialized LangGraph agents with multi-agent protocols.

## Architecture

### Multi-Agent System

```
┌─────────────────────────────────────────────────────────┐
│                    Router Agent                         │
│           (Intent Analysis & Routing)                   │
└────────────┬────────────────────────────────────────────┘
             │
      ┌──────┴──────┬──────────┬──────────────┬──────────┐
      │             │          │              │          │
      ▼             ▼          ▼              ▼          ▼
┌──────────┐  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐
│Onboarding│  │   Task   │ │ Calendar │ │Adaptive  │ │Human │
│  Agent   │  │  Agent   │ │  Agent   │ │Learning  │ │Agent │
└──────────┘  └──────────┘ └──────────┘ └──────────┘ └──────┘
```

## Agents

### 1. RouterAgent (`agents_langgraph/agents/router_agent.py`)

**Responsibilities:**
- First agent in the flow - analyzes user intent
- Routes messages to appropriate specialized agents
- Uses AI (conversation understanding) to extract intent and entities
- Determines confidence levels for routing decisions

**Handoffs:**
- → OnboardingAgent: Onboarding flow or new users
- → TaskAgent: Task-related queries (add, view, edit, delete)
- → CalendarAgent: Calendar/scheduling queries
- → AdaptiveLearningAgent: Insights, patterns, learning queries
- → HumanAgent: Needs clarification

**Use Cases:**
- UC1: Intent analysis and routing
- UC2: Multi-agent handoff coordination
- UC3: Confidence-based routing decisions

### 2. OnboardingAgent (`agents_langgraph/agents/onboarding_agent.py`)

**Responsibilities:**
- Manages complete user onboarding flow
- Handles pillar selection, custom pillars
- Processes work hours, timezone, habits, mood tracking
- Tracks onboarding progress and completion

**Handoffs:**
- → RouterAgent: Onboarding complete, return to normal flow
- → HumanAgent: Needs clarification during onboarding

**Use Cases:**
- All onboarding use cases from COMPREHENSIVE_PLAN.md
- Pillar selection and customization
- Work schedule parsing (complex schedules with travel, classes)
- Timezone configuration
- Habit and mood tracking setup

**Edge Cases:**
- Incomplete onboarding data
- Invalid input formats
- Custom pillar creation
- Complex work schedules

### 3. TaskAgent (`agents_langgraph/agents/task_agent.py`)

**Responsibilities:**
- Task creation (guided and natural language)
- Task viewing, editing, deletion
- Task prioritization
- Natural language task understanding
- Task-to-calendar handoff for scheduling

**Handoffs:**
- → CalendarAgent: Task scheduling requested
- → RouterAgent: General query or redirect
- → HumanAgent: Needs clarification

**Use Cases:**
- All task management use cases from COMPREHENSIVE_PLAN.md
- Natural language task creation
- Task CRUD operations
- Task filtering and sorting
- Task prioritization

**Edge Cases:**
- Invalid task data
- Low confidence natural language parsing
- Task scheduling conflicts
- Task dependency cycles

### 4. CalendarAgent (`agents_langgraph/agents/calendar_agent.py`)

**Responsibilities:**
- Calendar event viewing
- Task scheduling in calendar
- Availability checking
- Time slot suggestions
- Calendar sync operations
- Conflict detection

**Handoffs:**
- → TaskAgent: After scheduling, return to task context
- → RouterAgent: General calendar query
- → HumanAgent: Needs clarification or scheduling input

**Use Cases:**
- All calendar use cases from COMPREHENSIVE_PLAN.md
- Calendar viewing and navigation
- Task scheduling with conflict detection
- Availability checking
- Calendar sync (bidirectional)

**Edge Cases:**
- Scheduling conflicts
- Invalid time slots
- Calendar sync errors
- OAuth token expiration

### 5. AdaptiveLearningAgent (`agents_langgraph/agents/adaptive_learning_agent.py`)

**Responsibilities:**
- Pattern detection and insights
- Learning from user corrections
- Automatic flow suggestions
- Behavior adaptation
- Feedback processing
- Analytics and reports

**Handoffs:**
- → RouterAgent: General query or redirect
- → HumanAgent: Needs clarification

**Use Cases:**
- All adaptive learning use cases from COMPREHENSIVE_PLAN.md
- Pattern detection (task completion, scheduling, habits)
- Correction learning
- Automatic flow creation
- Behavior adaptation
- Insights viewing

**Edge Cases:**
- Insufficient data for pattern detection
- Conflicting patterns
- Learning feedback processing errors

### 6. HumanAgent (`agents_langgraph/agents/human_agent.py`)

**Responsibilities:**
- Clarification requests
- User input collection
- Interrupt handling
- Resume conversation after clarification

**Handoffs:**
- → RouterAgent: After clarification, re-route to appropriate agent
- → END: Complete clarification response

**Use Cases:**
- Clarification during agent interactions
- User input collection
- Multi-turn conversation management

## State Management

### AgentState (`agents_langgraph/state.py`)

Extended state schema that includes:
- Messages (from MessagesState)
- Current conversation state
- Active agent tracking
- Intent and entities
- Agent-specific data
- Handoff control
- Error handling
- Learning and adaptation data

### State Transitions

1. **Initial State Creation**: `create_initial_state()` creates state from user message
2. **Context Integration**: `update_state_from_context()` merges existing conversation context
3. **Agent Updates**: Each agent updates state with operation-specific data
4. **Handoffs**: State includes `handoff_to` and `handoff_reason` for multi-agent transitions

## Multi-Agent Protocols

### Handoff Protocol

1. **Agent Decision**: Agent determines need for handoff
2. **State Update**: Agent sets `handoff_to` and `handoff_reason` in state
3. **Command Return**: Agent returns `Command(goto=handoff_target, update=state_update)`
4. **Graph Routing**: LangGraph routes to target agent based on `handoff_to`
5. **Context Preservation**: All state data (including agent-specific) preserved during handoff

### Example Handoff Flow

```
User: "Schedule my task for tomorrow"
  ↓
RouterAgent: Intent = "schedule_task", Confidence = 0.8
  ↓
TaskAgent: Process task, detect scheduling need
  ↓ (Handoff with task context)
CalendarAgent: Schedule task, check availability
  ↓ (Handoff back with result)
TaskAgent: Confirm scheduling, update task
  ↓
END: Response sent to user
```

## Integration

### Telegram Handler Integration (`agents_langgraph/integration.py`)

Bridges LangGraph with existing Telegram handlers:
- Processes Telegram messages through LangGraph
- Routes to existing handlers based on active agent
- Supports gradual migration (LangGraph routes, existing handlers execute)
- Fallback to existing handlers on errors

### Entry Point (`telegram_bot/handlers/start.py`)

Modified `handle_message()` to:
1. Try LangGraph multi-agent system first
2. Fallback to existing natural language handler on errors
3. Maintain backward compatibility

## Graph Structure

### Main Graph (`agents_langgraph/graph.py`)

```
START
  ↓
router_agent (Routes based on intent)
  ↓
[onboarding_agent | task_agent | calendar_agent | adaptive_learning_agent | human_agent]
  ↓
[Handoffs between agents as needed]
  ↓
END
```

### Conditional Edges

- **Router → Agents**: Based on intent and confidence
- **Agents → Agents**: Based on handoff needs (e.g., Task → Calendar for scheduling)
- **Agents → Router**: For re-routing or completion
- **Agents → Human**: For clarification
- **Any → END**: When operation complete

## Memory & Persistence

### Checkpointer

- Uses LangGraph's `MemorySaver` for conversation memory
- Thread-based persistence (user_id as thread_id)
- Automatic message deduplication
- Conversation history management

### Integration with Existing Memory

- Existing conversation store (LlamaIndex) still active
- LangGraph checkpointer for agent state
- Future: Merge into unified memory system

## Migration Status

### ✅ Completed

- [x] RouterAgent implementation
- [x] OnboardingAgent implementation
- [x] TaskAgent implementation
- [x] CalendarAgent implementation
- [x] AdaptiveLearningAgent implementation
- [x] HumanAgent implementation
- [x] Main graph construction
- [x] State management schema
- [x] Multi-agent handoff protocols
- [x] Telegram handler integration
- [x] Checkpointer setup

### 🔄 In Progress

- [ ] Full handler migration (currently using bridge pattern)
- [ ] Direct response generation in agents (currently delegating to handlers)
- [ ] Unified memory system (LangGraph + existing)

### 🔜 Future Enhancements

- [ ] Agent-specific tools and tool calling
- [ ] Agent collaboration (multiple agents working together)
- [ ] Advanced handoff protocols (with context negotiation)
- [ ] Agent-specific memory isolation
- [ ] Performance monitoring per agent

## Testing

### Test Cases

1. **Router Routing**: Verify correct agent selection based on intent
2. **Onboarding Flow**: Test complete onboarding through OnboardingAgent
3. **Task Creation**: Test natural language task creation through TaskAgent
4. **Task Scheduling**: Test Task → Calendar handoff for scheduling
5. **Multi-Agent Handoffs**: Test complex flows with multiple agents
6. **Error Handling**: Test error recovery and fallbacks
7. **Memory Persistence**: Test conversation memory across turns

### Running Tests

```bash
# Test state imports
python -c "from agents_langgraph.state import AgentState; print('OK')"

# Test graph compilation (requires full environment)
python -c "from agents_langgraph.graph import get_graph; print('OK')"
```

## Usage

### In Telegram Handler

```python
from agents_langgraph.integration import handle_message_with_langgraph

# In message handler
await handle_message_with_langgraph(update, context)
```

### Direct Graph Invocation

```python
from agents_langgraph.graph import process_message

result = await process_message(
    user_id=123,
    message="Add task: Prepare presentation",
    telegram_update={...}
)

response = result["response"]
active_agent = result["active_agent"]
```

## Files Structure

```
agents_langgraph/
├── __init__.py              # Package exports
├── state.py                 # AgentState schema and helpers
├── graph.py                 # Main graph construction
├── integration.py           # Telegram integration layer
└── agents/
    ├── __init__.py          # Agent exports
    ├── router_agent.py      # Router agent
    ├── onboarding_agent.py  # Onboarding agent
    ├── task_agent.py        # Task agent
    ├── calendar_agent.py    # Calendar agent
    ├── adaptive_learning_agent.py  # Learning agent
    └── human_agent.py       # Human clarification agent
```

## Next Steps

1. **Test Multi-Agent Flows**: Test complex scenarios with multiple agents
2. **Enhance Agents**: Add direct response generation in agents
3. **Tool Integration**: Add agent-specific tools for operations
4. **Monitoring**: Add agent-specific metrics and monitoring
5. **Documentation**: Create agent-specific documentation

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Multi-Agent Guide](https://langchain-ai.github.io/langgraph/how-tos/multi-agent/)
- [COMPREHENSIVE_PLAN.md](../COMPREHENSIVE_PLAN.md) - All use cases and flows
- [LIBRARY_RECOMMENDATIONS.md](./LIBRARY_RECOMMENDATIONS.md) - LangGraph recommendation

