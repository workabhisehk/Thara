# User Flow and Agent Flow Architecture

## Overview

This document describes how user messages flow through the system and how the AI agent processes and responds to them.

## High-Level Flow

```
┌─────────────┐
│   User      │
│  (Telegram) │
└──────┬──────┘
       │
       │ 1. User sends message
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Telegram Bot Layer                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Message Handler                                      │   │
│  │  - Receives update                                    │   │
│  │  - Extracts user, message, context                    │   │
│  │  - Routes to appropriate handler                      │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        │ 2. Route based on message type
                        ▼
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌───────────────┐            ┌──────────────────────┐
│   Command     │            │  Natural Language    │
│   Handler     │            │  Message Handler     │
│  (/start,     │            │  (AI Processing)     │
│   /tasks,     │            │                      │
│   /help)      │            │                      │
└───────┬───────┘            └──────────┬───────────┘
        │                               │
        │                               │ 3. Intent Extraction
        │                               ▼
        │                    ┌──────────────────────┐
        │                    │  AI Intent Extraction │
        │                    │  - Extract intent     │
        │                    │  - Extract entities    │
        │                    │  - Determine action    │
        │                    └──────────┬───────────┘
        │                               │
        │                               │ 4. Route to Agent
        │                               ▼
        │                    ┌──────────────────────┐
        │                    │   Agent Framework    │
        │                    │  (Parlant/LangGraph) │
        │                    │  - Process request   │
        │                    │  - Use tools         │
        │                    │  - Generate response │
        │                    └──────────┬───────────┘
        │                               │
        └───────────────┬───────────────┘
                        │
                        │ 5. Execute action
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Business Logic Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Tasks      │  │   Calendar   │  │   Memory    │    │
│  │   Service    │  │   Service      │  │   System    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        │ 6. Store results
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Database Layer                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  PostgreSQL                                           │  │
│  │  - Users, Tasks, Events, Conversations                │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        │ 7. Generate response
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Response Generation                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Format response                                       │  │
│  │  - User-friendly message                               │  │
│  │  - Inline keyboards (if needed)                      │  │
│  │  - Error handling                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        │ 8. Send to user
                        ▼
┌─────────────┐
│   User      │
│  (Telegram) │
└─────────────┘
```

## Detailed User Flow

### 1. Command Flow (e.g., `/start`, `/tasks`)

```
User sends "/start"
    │
    ▼
[Command Handler] (telegram_bot/handlers/start.py)
    │
    ├─→ Check if user exists in database
    │
    ├─→ If new user:
    │   └─→ Start onboarding flow
    │       ├─→ Ask for preferred name
    │       ├─→ Ask for work hours
    │       ├─→ Ask for pillars
    │       └─→ Mark as onboarded
    │
    └─→ If existing user:
        └─→ Send welcome message
            └─→ Show available commands
```

### 2. Natural Language Message Flow

```
User sends "Add task: Review code tomorrow"
    │
    ▼
[Message Handler] (telegram_bot/handlers/start.py::handle_message)
    │
    ├─→ Get conversation state
    │
    ├─→ If in specific state (e.g., ADDING_TASK):
    │   └─→ Handle state-specific input
    │
    └─→ If in IDLE state:
        │
        ▼
[Intent Extraction] (ai/intent_extraction.py)
    │
    ├─→ Extract intent using AI
    │   └─→ Returns: {"intent": "create_task", "entities": {...}}
    │
    ├─→ Extract entities (ai/task_entity_extraction.py)
    │   ├─→ Task title: "Review code"
    │   ├─→ Due date: "tomorrow" → parsed to datetime
    │   └─→ Priority, pillar, etc.
    │
    └─→ Route based on intent
        │
        ▼
[Agent Framework] (agents_parlant/ or agents_langgraph/)
    │
    ├─→ Process request
    │   ├─→ Use tools (create_task, get_calendar, etc.)
    │   ├─→ Generate response
    │   └─→ Return formatted message
    │
    └─→ Execute action
        │
        ▼
[Task Service] (tasks/service.py)
    │
    ├─→ Validate input
    ├─→ Create task in database
    └─→ Return task object
        │
        ▼
[Response Generation] (ai/response_generation.py)
    │
    └─→ Format user-friendly message
        │
        ▼
Send to user via Telegram
```

## Agent Flow Architecture

### Parlant Agent Flow (when USE_PARLANT=true)

```
User Message
    │
    ▼
[Telegram Adapter] (agents_parlant/telegram_adapter.py)
    │
    ├─→ Convert Telegram update to Parlant message
    │
    └─→ Call Parlant Agent
        │
        ▼
[Parlant Agent] (agents_parlant/agent.py)
    │
    ├─→ Load conversation history
    ├─→ Process message with LLM
    │
    ├─→ Tool Selection
    │   ├─→ create_task
    │   ├─→ get_tasks
    │   ├─→ update_task
    │   ├─→ get_calendar_events
    │   └─→ schedule_event
    │
    ├─→ Execute Tools (agents_parlant/tools.py)
    │   ├─→ Call business logic services
    │   └─→ Return results
    │
    └─→ Generate Response
        │
        ▼
[Response Formatting]
    │
    └─→ Send to user
```

### LangGraph Agent Flow (when USE_PARLANT=false)

```
User Message
    │
    ▼
[Router Agent] (agents_langgraph/agents/router_agent.py)
    │
    ├─→ Analyze message
    │
    └─→ Route to appropriate agent:
        │
        ├─→ [Task Agent] (agents_langgraph/agents/task_agent.py)
        │   ├─→ Handle task operations
        │   └─→ Use task tools
        │
        ├─→ [Calendar Agent] (agents_langgraph/agents/calendar_agent.py)
        │   ├─→ Handle calendar operations
        │   └─→ Use calendar tools
        │
        ├─→ [Onboarding Agent] (agents_langgraph/agents/onboarding_agent.py)
        │   └─→ Guide new users
        │
        └─→ [Human Agent] (agents_langgraph/agents/human_agent.py)
            └─→ Handle general conversation
```

## State Management Flow

### Conversation State Machine

```
IDLE
  │
  ├─→ User sends "Add task"
  │   └─→ ADDING_TASK
  │       │
  │       ├─→ User provides title
  │       │   └─→ ADDING_TASK_PILLAR
  │       │       │
  │       │       ├─→ User selects pillar
  │       │       │   └─→ ADDING_TASK_PRIORITY
  │       │       │       │
  │       │       │       ├─→ User selects priority
  │       │       │       │   └─→ ADDING_TASK_DUE_DATE
  │       │       │       │       │
  │       │       │       │       ├─→ User provides date
  │       │       │       │       │   └─→ ADDING_TASK_DURATION
  │       │       │       │       │       │
  │       │       │       │       │       └─→ User provides duration
  │       │       │       │       │           └─→ Show summary → IDLE
  │       │       │       │       │
  │       │       │       │       └─→ User says "none"
  │       │       │       │           └─→ ADDING_TASK_DURATION
  │       │       │       │
  │       │       │       └─→ User cancels
  │       │       │           └─→ IDLE
  │       │       │
  │       │       └─→ User cancels
  │       │           └─→ IDLE
  │       │
  │       └─→ User cancels
  │           └─→ IDLE
  │
  ├─→ User sends "/tasks"
  │   └─→ VIEWING_TASKS
  │       │
  │       └─→ User interacts with keyboard
  │           └─→ IDLE (after action)
  │
  └─→ User sends natural language
      └─→ Process with AI → IDLE
```

## Tool Execution Flow

### Example: Creating a Task

```
Agent decides to create task
    │
    ▼
[Tool: create_task] (agents_parlant/tools.py or ai/tools/task_tool.py)
    │
    ├─→ Validate parameters
    │   ├─→ Title required
    │   ├─→ Pillar valid
    │   └─→ Priority valid
    │
    ├─→ Parse due date (if provided)
    │   ├─→ "tomorrow" → datetime
    │   ├─→ "Dec 25" → datetime
    │   └─→ "next week" → datetime
    │
    └─→ Call Task Service (tasks/service.py)
        │
        ├─→ Create database session
        ├─→ Create Task object
        ├─→ Save to database
        └─→ Return task
            │
            ▼
[Response Formatting]
    │
    └─→ "✅ Task created: Review code (due: tomorrow)"
```

## Error Handling Flow

```
Error occurs
    │
    ▼
[Error Handler] (telegram_bot/bot.py::error_handler)
    │
    ├─→ Categorize error
    │   ├─→ Database error
    │   ├─→ LLM error
    │   ├─→ Calendar error
    │   └─→ Validation error
    │
    ├─→ Log error (with context)
    │
    ├─→ Format user-friendly message
    │   └─→ Use guardrails (edge_cases/guardrails.py)
    │
    └─→ Send to user
        │
        └─→ Retry logic (if applicable)
```

## Memory and Context Flow

```
User sends message
    │
    ▼
[Context Retrieval] (memory/context_retrieval.py)
    │
    ├─→ Get recent conversations
    ├─→ Get active tasks
    ├─→ Get upcoming deadlines
    ├─→ Get user preferences
    └─→ Format context for AI
        │
        ▼
[AI Processing]
    │
    ├─→ Use context in prompt
    └─→ Generate contextual response
        │
        ▼
[Store Conversation] (memory/conversation_store.py)
    │
    └─→ Save to database
        │
        └─→ Update embeddings (for future retrieval)
```

## Database Interaction Flow

```
Handler needs data
    │
    ▼
[Database Connection] (database/connection.py)
    │
    ├─→ Get session (with retry logic)
    │   ├─→ Check connection health
    │   ├─→ Retry on failure (3 attempts)
    │   └─→ Exponential backoff
    │
    ├─→ Execute query
    │   ├─→ SELECT, INSERT, UPDATE, DELETE
    │   └─→ Handle errors
    │
    └─→ Commit/rollback
        │
        └─→ Close session
```

## Scheduling Flow

```
Scheduled Job Triggered (APScheduler)
    │
    ▼
[Job Handler] (scheduler/jobs.py)
    │
    ├─→ Get all active users
    │
    └─→ Execute job
        │
        ├─→ [Check-ins] (scheduler/checkins.py)
        │   ├─→ Get pending clarifications
        │   ├─→ Get active tasks
        │   └─→ Send contextual message
        │
        ├─→ [Reminders] (scheduler/reminders.py)
        │   ├─→ Get upcoming deadlines
        │   └─→ Send reminders
        │
        └─→ [Daily Kickoff] (scheduler/daily_kickoff.py)
            ├─→ Get calendar events
            ├─→ Calculate free time
            └─→ Send daily summary
```

## Key Components Summary

### User-Facing Components
- **Telegram Bot** (`telegram_bot/`): Handles all user interactions
- **Handlers** (`telegram_bot/handlers/`): Process commands and messages
- **Keyboards** (`telegram_bot/keyboards.py`): Interactive UI elements

### AI/Agent Components
- **Intent Extraction** (`ai/intent_extraction.py`): Understands user intent
- **Entity Extraction** (`ai/task_entity_extraction.py`): Extracts structured data
- **Agent Framework** (`agents_parlant/` or `agents_langgraph/`): Processes requests
- **Tools** (`agents_parlant/tools.py`, `ai/tools/`): Execute actions

### Business Logic
- **Task Service** (`tasks/service.py`): Task CRUD operations
- **Calendar Service** (`google_calendar/`): Calendar integration
- **Scheduler** (`scheduler/`): Scheduled jobs

### Data Layer
- **Database** (`database/`): PostgreSQL with async SQLAlchemy
- **Memory** (`memory/`): Conversation storage and context retrieval
- **Analytics** (`analytics/`): Tracking and reporting

### Supporting Components
- **Validation** (`edge_cases/validation.py`): Input validation
- **Guardrails** (`edge_cases/guardrails.py`): Safety checks
- **Error Recovery** (`edge_cases/error_recovery.py`): Error handling

## Example: Complete Flow for "Add task: Review code tomorrow"

1. **User sends**: "Add task: Review code tomorrow"
2. **Telegram Bot** receives update
3. **Message Handler** routes to natural language handler
4. **Intent Extraction** identifies: `intent="create_task"`
5. **Entity Extraction** extracts:
   - `title="Review code"`
   - `due_date="tomorrow"` → parsed to `datetime(2025-11-23 23:59:00)`
6. **Agent Framework** processes request
7. **Tool: create_task** called with parameters
8. **Task Service** validates and creates task
9. **Database** stores task
10. **Response Generation** formats: "✅ Task created: Review code (due: tomorrow)"
11. **Telegram Bot** sends response to user

## Configuration

The system can use either:
- **Parlant Agent** (`USE_PARLANT=true`): Simpler, single-agent approach
- **LangGraph Agent** (`USE_PARLANT=false`): Multi-agent, state machine approach

Both agents use the same tools and business logic, but differ in how they process conversations and make decisions.

