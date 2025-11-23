# Parlant Integration - Complete Setup Guide

> **Status**: ✅ Ready for testing and deployment  
> **Version**: 1.0.0  
> **Last Updated**: 2025-11-22

This guide provides complete documentation for integrating and using Parlant with the Thara Telegram bot.

## 📑 Table of Contents

1. [What's Been Implemented](#-whats-been-implemented)
2. [Quick Start](#-quick-start)
3. [Features](#-features)
4. [Architecture](#-architecture)
5. [Configuration](#-configuration)
6. [Usage Examples](#-usage-examples)
7. [Implementation Details](#-implementation-details)
8. [Troubleshooting](#-troubleshooting)
9. [Production Deployment](#-production-deployment)
10. [Best Practices](#-best-practices)

## ✅ What's Been Implemented

### 1. Core Integration (`agents_parlant/`)
- **`agent.py`**: Session-based Parlant agent setup with guidelines
- **`tools.py`**: 5 tools for tasks, calendar, and user operations
- **`telegram_adapter.py`**: Bridge between Telegram and Parlant
- **`__init__.py`**: Module initialization

### 2. Configuration
- Added `USE_PARLANT` setting to `config.py`
- Updated `requirements.txt` with `parlant>=3.0.0`
- Message handler routes to Parlant when enabled

### 3. Documentation
- `agents_parlant/README.md`: Module overview
- `agents_parlant/QUICK_START.md`: Quick reference
- `docs/PARLANT_INTEGRATION.md`: Comprehensive guide

### 4. Testing
- `scripts/test_parlant_integration.py`: Test script for validation

### 5. Lifecycle Management
- Cleanup on bot shutdown (`bot_main.py`)
- Proper resource management

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Telegram bot token
- Database connection (PostgreSQL/Neon)
- OpenAI API key (or Gemini as fallback)

### Step 1: Install Parlant

```bash
# Install Parlant SDK
pip install parlant

# Or install all dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create or update your `.env` file:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# AI/LLM
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key  # Optional, for fallback

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Parlant Configuration
USE_PARLANT=true  # Enable Parlant integration
```

### Step 3: Test the Integration

```bash
# Run the test script
python scripts/test_parlant_integration.py
```

Expected output:
```
✅ Parlant SDK imported successfully
✅ Configuration loaded
✅ Tools Definition
✅ Session Creation
✅ Telegram Adapter
✅ Message Processing
```

### Step 4: Run the Bot

```bash
# Start the bot
python bot_main.py
```

The bot will:
1. Initialize Parlant server (if enabled)
2. Load all handlers
3. Start polling for Telegram messages
4. Route messages to Parlant when `USE_PARLANT=true`

## 📋 Features

### Guidelines (Rule-Following Behavior)

Parlant uses **guidelines** instead of system prompts. Guidelines are reliably enforced:

| Guideline Type | Condition | Action |
|---------------|-----------|--------|
| **Task Viewing** | User asks about tasks | Use `get_user_tasks` tool |
| **Task Creation** | User wants to add/create task | Extract details, use `create_user_task` |
| **Calendar Query** | User asks about calendar/schedule | Use `get_calendar_events` tool |
| **Event Scheduling** | User wants to schedule something | Extract details, use `create_calendar_event` |
| **User Info** | User asks about themselves | Use `get_user_info` tool |
| **Greeting** | User greets or says hello | Respond warmly, offer help |
| **Help Request** | User asks for help | Explain capabilities |
| **Clarification** | Request is unclear | Ask clarifying questions |
| **Error Handling** | Tool returns error | Acknowledge, explain, provide next steps |

### Tools (Available Functions)

All tools are async and return `ToolResult`:

| Tool | Purpose | Parameters | Returns |
|------|---------|------------|---------|
| `get_user_tasks` | View user's tasks | `status: str` (active/completed/all) | Formatted task list |
| `create_user_task` | Create new task | `title`, `description`, `pillar`, `priority`, `due_date`, `estimated_duration` | Task creation confirmation |
| `get_calendar_events` | View calendar events | `days: int` (default: 7) | Formatted event list |
| `create_calendar_event` | Schedule event | `title`, `start_time`, `end_time`, `description`, `location` | Event creation confirmation |
| `get_user_info` | Get user information | None | User profile summary |

### Architecture Features

- ✅ **Session-based conversations**: Each user gets a persistent session
- ✅ **Per-user customer management**: Customer records for personalization
- ✅ **User ID mapping**: Seamless translation between Telegram and Parlant IDs
- ✅ **Automatic fallback**: Falls back to LangGraph if Parlant fails
- ✅ **Error recovery**: Graceful error handling with user-friendly messages
- ✅ **Resource cleanup**: Proper cleanup on bot shutdown

## 🔧 How It Works

### Message Flow

```
┌─────────────────┐
│  Telegram User  │
│  Sends Message  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ telegram_bot/handlers/   │
│ start.py                 │
│ handle_message()         │
└────────┬─────────────────┘
         │
         ▼
    ┌──────────────┐
    │ USE_PARLANT? │
    └──────┬───────┘
           │
    ┌──────┴───────┐
    │              │
   YES            NO
    │              │
    ▼              ▼
┌─────────────┐  ┌──────────────────┐
│ Parlant     │  │ LangGraph        │
│ Integration │  │ (Fallback)       │
└──────┬──────┘  └──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ agents_parlant/          │
│ telegram_adapter.py      │
│ handle_message_with_     │
│ parlant()                │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ agents_parlant/agent.py  │
│ process_message()        │
│                          │
│ 1. get_or_create_       │
│    session()            │
│ 2. session.post_message()│
│ 3. Wait for processing  │
│ 4. session.list_events()│
│ 5. Extract AI response  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ agents_parlant/tools.py  │
│ (If tools are called)    │
│                          │
│ - Extract user_id        │
│ - Execute operation      │
│ - Return ToolResult      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Response sent to        │
│ Telegram user           │
└─────────────────────────┘
```

### Detailed Process

1. **Message Reception**
   - Telegram bot receives user message
   - Handler checks `USE_PARLANT` setting

2. **Session Management** (if Parlant enabled)
   - Get or create Parlant customer for user
   - Get or create Parlant session
   - Map customer ID to Telegram user ID

3. **Message Processing**
   - Post message to Parlant session
   - Agent processes message using guidelines
   - Tools are called if needed
   - Agent generates response

4. **Response Retrieval**
   - Wait for agent processing (1 second)
   - List events from session
   - Extract AI agent message
   - Format and return response

5. **Fallback Handling** (if Parlant fails)
   - Catch exceptions
   - Log errors
   - Fallback to LangGraph
   - Fallback to traditional handler

## 📁 File Structure

```
agents_parlant/
├── __init__.py              # Module initialization
├── agent.py                 # Agent setup, sessions, guidelines
├── tools.py                 # Task/calendar/user tools
├── telegram_adapter.py     # Telegram integration
├── README.md                # Module documentation
└── QUICK_START.md          # Quick reference

docs/
└── PARLANT_INTEGRATION.md  # Comprehensive guide

scripts/
└── test_parlant_integration.py  # Test script
```

## 🎯 Key Implementation Details

### Session Management
- Each Telegram user → Parlant customer
- Each conversation → Parlant session
- Sessions persist across messages

### User ID Mapping
- `_customer_to_user_id`: Maps Parlant customer IDs to Telegram user IDs
- Tools extract user_id from ToolContext using this mapping

### Message Processing
```python
session.post_message(message, source=CUSTOMER)
await asyncio.sleep(1)  # Wait for processing
events = await session.list_events()
# Extract AI agent response
```

### Tool Context
Tools receive `ToolContext` and extract user_id via:
1. `context.customer_id` → lookup in mapping
2. `context.customer.id` → lookup in mapping
3. `context.session.customer_id` → lookup in mapping
4. Fallback to `context.user_id`

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|------------|
| `USE_PARLANT` | No | `false` | Enable Parlant integration |
| `TELEGRAM_BOT_TOKEN` | Yes | - | Telegram bot token |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for LLM |
| `GEMINI_API_KEY` | No | - | Gemini API key (fallback) |
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `LOG_LEVEL` | No | `INFO` | Logging level |

### Parlant Server Configuration

The Parlant server is initialized automatically when the first message is processed. Configuration options:

```python
# In agents_parlant/agent.py
_parlant_server = p.Server()
# Server runs on default port (8800) or can be configured
```

### Agent Configuration

Each agent is configured with:
- **Name**: `Thara-{user_id}`
- **Description**: Productivity assistant persona
- **Guidelines**: Behavioral rules (see Features section)
- **Tools**: 5 registered tools

### Session Configuration

Sessions are created with:
- **Customer ID**: Linked to Telegram user
- **Title**: `Thara Conversation - User {user_id}`
- **Mode**: Auto (default Parlant mode)

## 💡 Usage Examples

### Example 1: User Asks About Tasks

**User**: "Show me my tasks"

**Flow**:
1. Message routed to Parlant
2. Guideline matches: "User asks about tasks"
3. Agent calls `get_user_tasks` tool
4. Tool retrieves tasks from database
5. Agent formats and returns response

**Response**:
```
Your active tasks:

1. 🔴 Prepare presentation for client meeting (Due: 2025-01-15 14:00)
   Create slides and prepare talking points

2. 🟡 Review project proposal (Due: 2025-01-16 10:00)

3. 🟢 Update documentation
```

### Example 2: User Creates a Task

**User**: "Add task: Finish quarterly report by Friday"

**Flow**:
1. Guideline matches: "User wants to add a task"
2. Agent extracts: title="Finish quarterly report", due_date="Friday"
3. Agent calls `create_user_task` tool
4. Tool creates task in database
5. Agent confirms creation

**Response**:
```
✅ Task created successfully!

**Finish quarterly report**
Priority: 🟡 Medium
Pillar: Work
Due: 2025-01-17 23:59
```

### Example 3: User Schedules Event

**User**: "Schedule team meeting tomorrow at 2pm"

**Flow**:
1. Guideline matches: "User wants to schedule something"
2. Agent extracts: title="team meeting", start_time="tomorrow at 2pm"
3. Agent calls `create_calendar_event` tool
4. Tool creates calendar event
5. Agent confirms

**Response**:
```
✅ Calendar event created successfully!

**team meeting**
📆 2025-01-16 14:00 - 15:00
```

### Example 4: Error Handling

**User**: "Show my tasks" (but user not onboarded)

**Flow**:
1. Guideline matches
2. Tool called but user not found
3. Tool returns error: "User not found. Please complete onboarding first."
4. Error handling guideline matches
5. Agent explains issue and provides next steps

**Response**:
```
I see you haven't completed onboarding yet. Please use /start to set up your account first, then I can help you manage tasks!
```

## 🐛 Troubleshooting

### Issue: Tools can't find user_id
**Solution**: Check `_customer_to_user_id` is populated when customer is created

### Issue: No agent response
**Solution**: 
- Increase wait time in `process_message()`
- Check Parlant server is running
- Verify guidelines match user messages

### Issue: Import errors
**Solution**: 
```bash
pip install parlant
```

### Issue: Session errors
**Solution**: 
- Ensure Parlant server initializes correctly
- Check customer/agent created before session
- Verify session lifecycle

### Issue: Slow responses
**Solution**:
- Increase wait time in `process_message()` (currently 1 second)
- Check Parlant server performance
- Monitor tool execution times
- Consider async processing improvements

### Issue: Guidelines not matching
**Solution**:
- Review guideline conditions - make them more specific
- Check logs for guideline match scores
- Test with different phrasings
- Add more specific guidelines

### Issue: Tools not being called
**Solution**:
- Verify tools are registered with agent
- Check guideline tool associations
- Review tool function signatures
- Check ToolContext user_id extraction

### Issue: User ID mapping errors
**Solution**:
- Verify `_customer_to_user_id` is populated
- Check customer creation happens before tool calls
- Review ToolContext extraction logic
- Add logging to trace user_id flow

## 🚀 Production Deployment

### Pre-Deployment Checklist

- [ ] Parlant SDK installed (`pip install parlant`)
- [ ] Environment variables configured
- [ ] `USE_PARLANT=true` in production `.env`
- [ ] Database connection tested
- [ ] OpenAI API key valid
- [ ] Test script passes
- [ ] Logging configured
- [ ] Error monitoring set up (Sentry)

### Deployment Steps

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   # Copy example env file
   cp .env.example .env
   # Edit with production values
   nano .env
   ```

3. **Run Tests**
   ```bash
   python scripts/test_parlant_integration.py
   ```

4. **Start Bot**
   ```bash
   python bot_main.py
   ```

5. **Monitor**
   - Check logs for Parlant initialization
   - Monitor first user interactions
   - Watch for errors

### Monitoring

**Key Metrics to Track**:
- Parlant session creation rate
- Message processing time
- Tool execution success rate
- Guideline match rate
- Error rate and types
- User satisfaction

**Log Locations**:
- Console output
- `bot.log` file
- Sentry (if configured)

### Performance Optimization

1. **Session Management**
   - Sessions persist across messages
   - Consider session expiration for inactive users
   - Monitor memory usage

2. **Wait Times**
   - Current: 1 second wait for agent processing
   - Adjust based on response times
   - Consider polling instead of fixed wait

3. **Tool Execution**
   - Tools are async and non-blocking
   - Database queries are optimized
   - Consider caching for frequent queries

## 📚 Next Steps

### Immediate Actions

1. **Test the integration**:
   ```bash
   python scripts/test_parlant_integration.py
   ```

2. **Enable in development**:
   - Set `USE_PARLANT=true` in `.env`
   - Restart bot
   - Test with real messages

3. **Monitor and iterate**:
   - Check logs for guideline matches
   - Monitor tool execution
   - Track user satisfaction

### Customization

1. **Add Guidelines**:
   ```python
   # In agents_parlant/agent.py, _setup_guidelines()
   await agent.create_guideline(
       condition="Your condition here",
       action="What agent should do",
       tools=[relevant_tools]  # Optional
   )
   ```

2. **Create New Tools**:
   ```python
   # In agents_parlant/tools.py
   @p.tool
   async def my_new_tool(context: p.ToolContext, param: str) -> p.ToolResult:
       user_id = extract_user_id(context)
       # Your logic here
       return p.ToolResult("Result message")
   ```

3. **Adjust Behavior**:
   - Modify wait times in `process_message()`
   - Update error messages
   - Customize agent description

### Future Enhancements

- [ ] Add more tools (habits, analytics, etc.)
- [ ] Implement session expiration
- [ ] Add conversation history to context
- [ ] Create custom journeys
- [ ] Add response templates
- [ ] Implement A/B testing
- [ ] Add analytics dashboard

## 📖 Documentation

- **Quick Start**: `agents_parlant/QUICK_START.md`
- **Full Guide**: `docs/PARLANT_INTEGRATION.md`
- **Module Docs**: `agents_parlant/README.md`

## 🔗 Resources

- [Parlant GitHub](https://github.com/emcie-co/parlant)
- [Parlant Documentation](https://www.parlant.io/docs)
- [Parlant Discord](https://discord.gg/duxWqxKk6J)

## ✨ Benefits

### Why Parlant?

| Feature | Traditional Approach | Parlant Approach |
|---------|---------------------|------------------|
| **Rule Following** | Hope LLM follows prompts | ✅ Guidelines enforced |
| **Consistency** | Variable responses | ✅ Predictable behavior |
| **Tool Usage** | May skip tools | ✅ Tools called reliably |
| **Error Handling** | Unpredictable | ✅ Structured error recovery |
| **Customization** | Complex prompt engineering | ✅ Simple guideline creation |

### Key Advantages

1. **Reliable Rule Following**
   - Guidelines are enforced, not just suggested
   - No more "hallucinating" responses
   - Consistent behavior across conversations

2. **Better Content Understanding**
   - Improved intent extraction
   - Context-aware responses
   - Natural conversation flow

3. **Task Completion**
   - Tools are called correctly based on guidelines
   - Proper validation and error handling
   - Clear confirmation messages

4. **Easy Customization**
   - Add guidelines in natural language
   - Create tools with simple decorators
   - No complex prompt engineering

5. **Production Ready**
   - Built-in error handling
   - Session management
   - Resource cleanup
   - Fallback mechanisms

## 🎓 Best Practices

### Guideline Design

1. **Be Specific**: More specific conditions = better matching
   ```python
   # Good
   condition="User asks about tasks, wants to see tasks, or asks what tasks they have"
   
   # Better
   condition="User asks about their tasks, wants to view tasks, or asks 'what tasks do I have'"
   ```

2. **Include Tools**: Associate guidelines with relevant tools
   ```python
   await agent.create_guideline(
       condition="...",
       action="...",
       tools=[get_user_tasks]  # Explicit tool association
   )
   ```

3. **Error Handling**: Always include error handling guidelines
   ```python
   await agent.create_guideline(
       condition="A tool returns an error",
       action="Acknowledge, explain, provide next steps"
   )
   ```

### Tool Development

1. **Extract User ID First**: Always extract user_id at the start
   ```python
   user_id = extract_user_id(context)
   if not user_id:
       return p.ToolResult("Error: Could not identify user.")
   ```

2. **Validate Inputs**: Check inputs before processing
   ```python
   if not title or len(title) < 3:
       return p.ToolResult("Error: Task title must be at least 3 characters.")
   ```

3. **Return Clear Messages**: Format responses for users
   ```python
   return p.ToolResult(f"✅ Task created: {task.title}")
   ```

### Session Management

1. **Reuse Sessions**: Sessions persist across messages
2. **Handle Errors**: Always catch and handle session errors
3. **Cleanup**: Properly cleanup on shutdown

### Testing

1. **Test Each Tool**: Verify tools work independently
2. **Test Guidelines**: Ensure guidelines match correctly
3. **Test Error Cases**: Verify error handling works
4. **Test Integration**: End-to-end testing with Telegram

## 📊 Comparison: Parlant vs LangGraph

| Aspect | Parlant | LangGraph |
|-------|---------|-----------|
| **Rule Following** | ✅ Enforced | ⚠️ Prompt-based |
| **Complexity** | ✅ Simple | ⚠️ More complex |
| **Multi-Agent** | ⚠️ Single agent | ✅ Multi-agent |
| **Tool Reliability** | ✅ High | ⚠️ Variable |
| **Setup Time** | ✅ Fast | ⚠️ Longer |
| **Customization** | ✅ Easy | ⚠️ More complex |

**Recommendation**: Use Parlant for reliable, rule-following behavior. Use LangGraph for complex multi-agent workflows.

---

**Status**: ✅ Ready for testing and deployment  
**Version**: 1.0.0  
**Maintained by**: Thara Development Team

