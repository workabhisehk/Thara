# System Architecture Diagram

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                               │
│                              Telegram Bot                                    │
│                    (python-telegram-bot framework)                          │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                │ User Messages & Commands
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MESSAGE ROUTING LAYER                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Telegram Handlers (telegram_bot/handlers/)                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │   Commands   │  │   Messages   │  │  Callbacks   │              │  │
│  │  │  (/start,    │  │  (Natural    │  │  (Inline     │              │  │
│  │  │   /tasks)    │  │   Language)  │  │   Buttons)    │              │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Conversation State Management (telegram_bot/conversation.py)         │  │
│  │  - Tracks user state (IDLE, ONBOARDING, ADDING_TASK, etc.)           │  │
│  │  - Database-backed persistence                                        │  │
│  │  - Context storage                                                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                │ Route based on state & message type
                                ▼
        ┌───────────────────────┴───────────────────────┐
        │                                               │
        ▼                                               ▼
┌───────────────┐                            ┌──────────────────────┐
│ State-Specific│                            │  Agent Framework      │
│   Handlers    │                            │  Selection            │
│               │                            │                       │
│ - Onboarding  │                            │  ┌────────────────┐  │
│ - Task Flow   │                            │  │ Check Config    │  │
│ - Scheduling  │                            │  │ USE_PARLANT?   │  │
└───────────────┘                            │  └────────┬───────┘  │
                                              │           │           │
                                              │    ┌──────┴──────┐   │
                                              │    │             │   │
                                              │    ▼             ▼   │
                                              │ ┌──────┐    ┌────────┐│
                                              │ │Parlant│    │LangGraph││
                                              │ │Agent  │    │Agents   ││
                                              │ └──────┘    └────────┘│
                                              └──────────────────────┘
                                                      │
        ┌─────────────────────────────────────────────┴──────────────┐
        │                                                            │
        ▼                                                            ▼
┌──────────────────────┐                              ┌──────────────────────────┐
│   PARLANT AGENT      │                              │   LANGGRAPH AGENTS       │
│  (Single Agent)      │                              │  (Multi-Agent System)    │
│                      │                              │                           │
│  ┌────────────────┐  │                              │  ┌────────────────────┐  │
│  │ Process Message│  │                              │  │  Router Agent      │  │
│  │ - Understand   │  │                              │  │  - Analyzes intent │  │
│  │ - Select Tool  │  │                              │  │  - Routes message  │  │
│  │ - Execute      │  │                              │  └──────────┬─────────┘  │
│  └───────┬────────┘  │                              │             │            │
│          │           │                              │             ▼            │
│          ▼           │                              │  ┌────────────────────┐  │
│  ┌──────────────┐    │                              │  │  Task Agent        │  │
│  │   Tools      │    │                              │  │  Calendar Agent    │  │
│  │  - create_   │    │                              │  │  Onboarding Agent  │  │
│  │    task      │    │                              │  │  Human Agent       │  │
│  │  - get_tasks │    │                              │  └──────────┬─────────┘  │
│  │  - update_   │    │                              │             │            │
│  │    task      │    │                              │             ▼            │
│  │  - calendar  │    │                              │  ┌────────────────────┐  │
│  └──────┬───────┘    │                              │  │   Tools            │  │
│         │            │                              │  │  (Same as Parlant)  │  │
│         └────────────┴──────────────────────────────┴──┴──────────┬───────────┘
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
                                                                    │
                                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BUSINESS LOGIC LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Tasks      │  │   Calendar   │  │   Memory     │  │  Analytics   │    │
│  │  Service     │  │   Service    │  │   System     │  │  & Reports   │    │
│  │              │  │              │  │              │  │              │    │
│  │ - CRUD       │  │ - Sync       │  │ - Context    │  │ - Completion │    │
│  │ - Priority   │  │ - Schedule   │  │   Retrieval  │  │   Tracking   │    │
│  │ - Dependencies│ │ - Conflicts  │  │ - Learning   │  │ - Forecasting│    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │ Clarifications│ │  Scheduler   │  │  Edge Cases  │                      │
│  │    Queue      │ │  (Jobs)      │  │  & Validation│                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL Database (Neon DB / Supabase)                            │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │  │
│  │  │  Structured    │  │  Vector Store   │  │  Migrations    │        │  │
│  │  │  Data          │  │  (pgvector)     │  │  (Alembic)     │        │  │
│  │  │               │  │                  │  │                │        │  │
│  │  │ - Users       │  │ - Embeddings    │  │ - Schema       │        │  │
│  │  │ - Tasks       │  │ - Conversations │  │   Updates      │        │  │
│  │  │ - Events      │  │ - Patterns      │  │                │        │  │
│  │  │ - Analytics   │  │                 │  │                │        │  │
│  │  └────────────────┘  └────────────────┘  └────────────────┘        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Telegram   │  │    Google    │  │    OpenAI    │  │    Gemini    │   │
│  │     API      │  │   Calendar   │  │     API      │  │     API      │   │
│  │              │  │     API      │  │              │  │              │   │
│  │ - Messages   │  │ - Events      │  │ - GPT-4o-mini│  │ - Fallback   │   │
│  │ - Callbacks  │  │ - OAuth      │  │ - Embeddings│  │   LLM         │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Agent Framework Comparison

### Current Setup: LangGraph (USE_PARLANT=False)

```
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH FLOW                               │
│                                                                 │
│  User Message                                                   │
│      │                                                          │
│      ▼                                                          │
│  ┌──────────────────┐                                          │
│  │  Router Agent    │                                          │
│  │  - Analyzes      │                                          │
│  │  - Determines    │                                          │
│  │    intent        │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ├─→ Task Intent? ──→ Task Agent                      │
│           │                      │                              │
│           │                      ├─→ Use task tools            │
│           │                      └─→ Generate response         │
│           │                                                     │
│           ├─→ Calendar Intent? ─→ Calendar Agent                │
│           │                      │                              │
│           │                      ├─→ Use calendar tools         │
│           │                      └─→ Generate response         │
│           │                                                     │
│           ├─→ Onboarding? ──────→ Onboarding Agent              │
│           │                      │                              │
│           │                      └─→ Guide user                 │
│           │                                                     │
│           └─→ General? ──────────→ Human Agent                   │
│                                    │                              │
│                                    └─→ Conversational response   │
│                                                                 │
│  State Machine: Tracks transitions between agents              │
└─────────────────────────────────────────────────────────────────┘
```

### Alternative: Parlant (USE_PARLANT=True)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PARLANT FLOW                                 │
│                                                                 │
│  User Message                                                   │
│      │                                                          │
│      ▼                                                          │
│  ┌──────────────────┐                                          │
│  │  Parlant Agent   │                                          │
│  │  (Single Agent)    │                                          │
│  │                  │                                          │
│  │  - Process        │                                          │
│  │  - Understand     │                                          │
│  │  - Select Tool    │                                          │
│  │  - Execute        │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │  Direct Tool     │                                          │
│  │  Execution       │                                          │
│  │                  │                                          │
│  │  - create_task   │                                          │
│  │  - get_tasks     │                                          │
│  │  - update_task   │                                          │
│  │  - calendar_ops   │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │  Business Logic  │                                          │
│  │  (Same as        │                                          │
│  │   LangGraph)     │                                          │
│  └──────────────────┘                                          │
│                                                                 │
│  Simpler: No routing, direct tool access                       │
└─────────────────────────────────────────────────────────────────┘
```

## Task Creation Flow (Current - LangGraph)

```
User: "Add task: Write LOR tomorrow"
    │
    ▼
[Message Handler]
    │
    ├─→ State: IDLE
    │
    ▼
[LangGraph Integration]
    │
    ├─→ Router Agent
    │   └─→ Intent: create_task
    │       └─→ Route to: Task Agent
    │
    ▼
[Task Agent]
    │
    ├─→ Extract Entities
    │   ├─→ title: "Write LOR"
    │   ├─→ due_date: "tomorrow"
    │   └─→ pillar: (AI categorization)
    │
    ├─→ Categorize Task
    │   └─→ Suggested: "education"
    │
    └─→ Call Natural Language Handler
        │
        ▼
[Natural Language Task Handler]
    │
    ├─→ Show Confirmation Card
    │   └─→ "Task: Write LOR"
    │       "Category: Education"
    │       "Is this correct?"
    │
    ▼
User: "category: other"
    │
    ▼
[Message Handler]
    │
    ├─→ Detect pending task in context
    ├─→ Parse correction: category="other"
    ├─→ Update context
    └─→ Re-show confirmation
        │
        ▼
User: Clicks "Yes, Create"
    │
    ▼
[Task Service]
    │
    ├─→ Validate
    ├─→ Create Task
    └─→ Save to Database
        │
        ▼
Response: "✅ Task created!"
```

## Component Interaction Map

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       │ Telegram API
       ▼
┌─────────────────────────────────────────────────────────────┐
│  telegram_bot/bot.py                                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Application                                          │   │
│  │  - Error Handler                                      │   │
│  │  - Handler Registration                               │   │
│  └──────────────────────────────────────────────────────┘   │
└──────┬──────────────────────────────────────────────────────┘
       │
       ├─→ Command Handlers (telegram_bot/handlers/)
       │   ├─→ start.py
       │   ├─→ tasks.py
       │   ├─→ calendar_handler.py
       │   └─→ ...
       │
       ├─→ Message Handler (telegram_bot/handlers/start.py)
       │   │
       │   ├─→ State Check
       │   │   ├─→ Onboarding? → onboarding.py
       │   │   ├─→ Adding Task? → tasks.py
       │   │   └─→ IDLE? → Agent Framework
       │   │
       │   └─→ Agent Selection
       │       ├─→ USE_PARLANT=True? → Parlant
       │       └─→ USE_PARLANT=False? → LangGraph
       │
       └─→ Callback Handler (telegram_bot/handlers/callbacks.py)
           └─→ Routes to specific callback handlers
```

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    REQUEST FLOW                              │
└─────────────────────────────────────────────────────────────┘

User Input
    │
    ▼
Telegram Update
    │
    ▼
Handler Selection
    │
    ├─→ Command? → Command Handler
    ├─→ Callback? → Callback Handler
    └─→ Message? → Message Handler
        │
        ├─→ State Check
        │   └─→ Route to state handler
        │
        └─→ Agent Framework
            │
            ├─→ Parlant (if enabled)
            │   └─→ Single agent processes
            │
            └─→ LangGraph (default)
                └─→ Router → Specialized Agent
                    │
                    └─→ Tool Execution
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    EXECUTION FLOW                            │
└─────────────────────────────────────────────────────────────┘

Tool Call
    │
    ▼
Business Logic Service
    │
    ├─→ Validation (edge_cases/validation.py)
    ├─→ Business Rules
    └─→ Database Operation
        │
        ▼
Database (PostgreSQL)
    │
    ├─→ Structured Data
    └─→ Vector Store (pgvector)
        │
        ▼
Response Generation
    │
    ├─→ Format Message
    ├─→ Add Keyboards (if needed)
    └─→ Send to User
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    TECHNOLOGY STACK                         │
└─────────────────────────────────────────────────────────────┘

Frontend:
  └─→ Telegram Bot API (python-telegram-bot)

Agent Frameworks:
  ├─→ LangGraph (default) - Multi-agent system
  └─→ Parlant (optional) - Single agent

AI/LLM:
  ├─→ OpenAI GPT-4o-mini (primary)
  ├─→ Google Gemini (fallback)
  └─→ OpenAI Embeddings (text-embedding-3-small)

Database:
  ├─→ PostgreSQL (Neon DB / Supabase)
  ├─→ pgvector (vector storage)
  └─→ SQLAlchemy (ORM)

Scheduling:
  └─→ APScheduler

External APIs:
  ├─→ Telegram Bot API
  ├─→ Google Calendar API
  └─→ OpenAI API / Gemini API
```

## File Structure Overview

```
Thara/
├── telegram_bot/          # Telegram interface
│   ├── bot.py            # Main bot instance
│   ├── handlers/         # Message handlers
│   ├── keyboards.py      # Inline keyboards
│   └── conversation.py   # State management
│
├── agents_langgraph/     # LangGraph agents (default)
│   ├── graph.py         # Agent graph
│   ├── integration.py   # Telegram integration
│   └── agents/          # Specialized agents
│
├── agents_parlant/       # Parlant agent (optional)
│   ├── agent.py         # Main agent
│   ├── telegram_adapter.py
│   └── tools.py         # Tool definitions
│
├── ai/                   # AI services
│   ├── intent_extraction.py
│   ├── task_entity_extraction.py
│   └── tools/           # LangChain tools
│
├── tasks/                # Task management
├── google_calendar/       # Calendar integration
├── memory/               # Memory system
├── database/             # Database layer
└── scheduler/            # Scheduled jobs
```

