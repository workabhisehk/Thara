# System Architecture

## Overview

The AI Productivity Agent is a conversational assistant that helps users manage tasks, schedule commitments, and maintain productivity. It uses Telegram as the interface, Google Calendar for scheduling, and AI (Gemini/OpenAI) for intelligent decision-making.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interaction Layer                    │
│                      (Telegram Bot)                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Telegram   │  │   FastAPI    │  │  Scheduler   │     │
│  │   Handlers   │  │   (OAuth)    │  │ (APScheduler)│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Tasks     │  │   Calendar   │  │    AI/LLM    │     │
│  │  Management  │  │ Integration  │  │   Services   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Analytics   │  │   Memory     │  │ Clarifications│     │
│  │  & Reports   │  │   System     │  │    Queue     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         PostgreSQL (Structured Data)                 │  │
│  │  - Users, Tasks, Calendar Events, Analytics          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    PostgreSQL + pgvector (Vector Store)              │  │
│  │  - Conversation embeddings                           │  │
│  │  - Task pattern embeddings                           │  │
│  │  - Context retrieval                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  External Services                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Telegram   │  │    Google    │  │    Gemini    │     │
│  │     API      │  │   Calendar   │  │     API      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Telegram Bot Layer

**File**: `telegram_bot/bot.py`, `telegram_bot/handlers/`

**Responsibilities**:
- Receive and process Telegram messages
- Handle commands (`/start`, `/tasks`, `/prioritize`, etc.)
- Manage conversation state
- Send responses to users

**Key Components**:
- **Bot Application**: Main bot instance using `python-telegram-bot`
- **Handlers**: Command and message handlers
- **Conversation State**: Tracks user interaction state
- **Keyboards**: Interactive inline keyboards

**Flow**:
```
User Message → Handler → Business Logic → Response → User
```

---

### 2. Business Logic Layer

#### 2.1 Task Management (`tasks/`)

**Files**: 
- `tasks/service.py` - CRUD operations
- `tasks/priority_queue.py` - Priority ordering
- `tasks/dependencies.py` - Dependency tracking
- `tasks/escalation.py` - Deadline monitoring
- `tasks/ai_prioritization.py` - AI-driven prioritization
- `tasks/time_based_reminders.py` - Time-based reminders

**Responsibilities**:
- Create, read, update, delete tasks
- Manage task priorities
- Track dependencies
- Monitor deadlines
- AI-powered prioritization
- Calculate reminder times

**Key Features**:
- Priority queue with multiple factors
- Dependency resolution
- Automatic escalation
- Time-based proactive reminders

---

#### 2.2 Calendar Integration (`calendar/`)

**Files**:
- `calendar/auth.py` - OAuth2 authentication
- `calendar/client.py` - Google Calendar API client
- `calendar/scheduling.py` - Task scheduling logic
- `calendar/conflict_detection.py` - Conflict detection
- `calendar/sync.py` - Calendar synchronization

**Responsibilities**:
- Authenticate with Google Calendar
- Create, update, delete calendar events
- Detect scheduling conflicts
- Find available time slots
- Sync calendar events

**Flow**:
```
User Request → OAuth Flow → Google Calendar API → Event Created → Database Updated
```

---

#### 2.3 AI/LLM Services (`ai/`)

**Files**:
- `ai/langchain_setup.py` - LangChain configuration
- `ai/prompts.py` - Prompt templates
- `ai/intent_extraction.py` - Natural language understanding
- `ai/tools/` - LangChain tools for agent

**Responsibilities**:
- Process natural language
- Extract intent and entities
- Categorize tasks
- Generate contextual responses
- Provide intelligent suggestions

**AI Models Used**:
- **Primary**: Google Gemini Pro
- **Fallback**: OpenAI GPT-4
- **Embeddings**: OpenAI text-embedding-3-small

---

#### 2.4 Memory System (`memory/`)

**Files**:
- `memory/llamaindex_setup.py` - LlamaIndex configuration
- `memory/conversation_store.py` - Store conversations
- `memory/context_retrieval.py` - Semantic search
- `memory/pattern_learning.py` - Habit recognition
- `memory/feedback_processor.py` - Feedback processing

**Responsibilities**:
- Store conversation history with embeddings
- Retrieve relevant context for AI
- Learn user patterns and habits
- Process feedback for adaptation

**Technology**:
- **Vector Store**: PostgreSQL with pgvector
- **Framework**: LlamaIndex
- **Embeddings**: OpenAI text-embedding-3-small

**Memory Architecture**:
```
Conversation → Embedding → Vector Store → Semantic Search → Context for AI
```

---

#### 2.5 Analytics (`analytics/`)

**Files**:
- `analytics/completion_tracking.py` - Track completions
- `analytics/readiness_forecasting.py` - Deadline readiness
- `analytics/reports.py` - Report generation

**Responsibilities**:
- Calculate completion rates
- Forecast deadline readiness
- Generate weekly/monthly reports
- Track metrics by pillar

---

#### 2.6 Scheduler (`scheduler/`)

**Files**:
- `scheduler/jobs.py` - Job definitions
- `scheduler/daily_kickoff.py` - Morning summaries
- `scheduler/checkins.py` - 30-min check-ins
- `scheduler/weekly_review.py` - Weekly reviews
- `scheduler/reminders.py` - Deadline reminders
- `scheduler/time_reminders.py` - Time-based reminders

**Responsibilities**:
- Schedule background jobs
- Send daily summaries
- Periodic check-ins
- Weekly reviews
- Deadline reminders
- Time-based task reminders

**Scheduled Jobs**:
- Daily kickoff (workday start)
- Check-ins (every 30 minutes)
- Weekly review (Sunday 10am)
- Deadline reminders (hourly)
- Deadline escalation (every 6 hours)
- Calendar sync (every 4 hours)
- Time-based reminders (every 30 minutes)

---

### 3. Data Layer

#### 3.1 Database Models (`database/models.py`)

**Tables**:
- `users` - User accounts and settings
- `tasks` - Task data
- `calendar_events` - Synced calendar events
- `conversations` - Message history
- `habits` - Learned patterns
- `analytics` - Metrics and statistics
- `clarifications` - Pending questions
- `learning_feedback` - User feedback

**Relationships**:
- User → Tasks (one-to-many)
- User → Calendar Events (one-to-many)
- User → Conversations (one-to-many)
- Task → Task (self-referential for dependencies)

---

#### 3.2 Vector Store

**Technology**: PostgreSQL + pgvector extension

**Collections**:
- Conversation embeddings
- Task pattern embeddings
- User behavior embeddings

**Operations**:
- Store embeddings with metadata
- Semantic search for context
- Similarity matching

---

### 4. External Services

#### 4.1 Telegram API
- **Purpose**: Bot communication
- **Method**: Long polling (python-telegram-bot)
- **Rate Limits**: 30 messages/second per bot

#### 4.2 Google Calendar API
- **Purpose**: Calendar management
- **Auth**: OAuth2
- **Scopes**: `https://www.googleapis.com/auth/calendar`
- **Rate Limits**: 1,000,000 queries/day

#### 4.3 Gemini API
- **Purpose**: AI/LLM processing
- **Model**: gemini-pro
- **Rate Limits**: Varies by tier

#### 4.4 OpenAI API (Fallback)
- **Purpose**: AI fallback
- **Model**: gpt-4
- **Rate Limits**: Varies by tier

---

## Data Flow Examples

### Task Creation Flow

```
User: "Add task: Prepare presentation"
  ↓
Telegram Handler → Intent Extraction (AI)
  ↓
Extract: title="Prepare presentation"
  ↓
Task Categorization (AI) → pillar="work"
  ↓
Ask for: priority, due_date, estimated_duration
  ↓
Create Task → Database
  ↓
Store in Vector Store (for pattern learning)
  ↓
Calculate reminder time
  ↓
Response: "Task created! I'll remind you at [time]"
```

### Daily Kickoff Flow

```
Scheduler (8am) → Get User
  ↓
Get Calendar Events (Google Calendar API)
  ↓
Get Priority Tasks (Database)
  ↓
Get Upcoming Deadlines (Database)
  ↓
Format Summary
  ↓
Send via Telegram
```

### AI Prioritization Flow

```
User: /prioritize
  ↓
Get All Active Tasks
  ↓
Get User Habits & Patterns
  ↓
Get Context (recent conversations, tasks)
  ↓
AI Analysis (Gemini) → Priority Scores
  ↓
Format Suggestions with Reasoning
  ↓
Send to User → Apply if confirmed
```

---

## Security Considerations

1. **API Keys**: Stored in environment variables, never in code
2. **OAuth Tokens**: Encrypted in database
3. **Database**: Connection strings secured
4. **Input Validation**: All user inputs validated
5. **Rate Limiting**: Implemented at API level
6. **Error Handling**: No sensitive data in error messages

---

## Scalability Considerations

1. **Database**: PostgreSQL can scale horizontally with read replicas
2. **Vector Store**: pgvector scales with PostgreSQL
3. **Scheduler**: APScheduler handles multiple users efficiently
4. **AI API**: Rate limits may require queuing for high volume
5. **Telegram**: Long polling is efficient for moderate user counts

**For High Scale**:
- Consider webhook instead of polling
- Add Redis for caching
- Use message queue for AI requests
- Horizontal scaling with load balancer

---

## Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| Bot Framework | python-telegram-bot |
| Web Framework | FastAPI |
| Database | PostgreSQL |
| Vector Store | pgvector (PostgreSQL extension) |
| ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| AI Framework | LangChain |
| Vector Framework | LlamaIndex |
| AI Models | Gemini Pro, GPT-4 |
| Embeddings | OpenAI text-embedding-3-small |
| Scheduler | APScheduler |
| Calendar API | Google Calendar API v3 |
| Deployment | Railway/Render/Fly.io |

---

## File Structure

```
Thara/
├── ai/                    # AI/LLM services
├── analytics/             # Analytics and reporting
├── calendar/              # Google Calendar integration
├── clarifications/        # Clarification queue
├── database/              # Database models and migrations
├── edge_cases/            # Error handling and edge cases
├── memory/                # Memory and learning system
├── scheduler/             # Background jobs
├── tasks/                 # Task management
├── telegram_bot/          # Telegram bot handlers
├── tests/                 # Test suite
├── deployment/            # Deployment configs
└── scripts/               # Utility scripts
```

---

## Future Architecture Improvements

1. **Microservices**: Split into separate services
2. **Message Queue**: Add Redis/RabbitMQ for async processing
3. **Caching**: Redis for frequently accessed data
4. **Webhooks**: Replace polling with webhooks
5. **GraphQL API**: Add GraphQL for flexible queries
6. **Event Sourcing**: Track all state changes
7. **CQRS**: Separate read/write models

