# Parlant Integration Guide

This guide explains how to use Parlant with the Thara Telegram bot for improved content understanding and task completion.

## What is Parlant?

[Parlant](https://github.com/emcie-co/parlant) is an AI agent framework that ensures rule-following behavior. Unlike traditional prompt-based approaches, Parlant uses **guidelines** that are reliably enforced, making agents more predictable and reliable.

## Why Use Parlant?

- ✅ **Better Content Understanding**: Improved intent extraction and context awareness
- ✅ **Reliable Task Completion**: Tools are called correctly based on guidelines
- ✅ **Rule Following**: Agents follow business rules consistently
- ✅ **Fewer Hallucinations**: Structured responses reduce errors

## Quick Start

### 1. Install Parlant

```bash
pip install parlant
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### 2. Enable Parlant

Add to your `.env` file:
```env
USE_PARLANT=true
```

### 3. Restart the Bot

The bot will now use Parlant for natural language processing instead of LangGraph.

## How It Works

### Architecture Flow

```
User sends message on Telegram
    ↓
telegram_bot/handlers/start.py (checks USE_PARLANT)
    ↓
agents_parlant/telegram_adapter.py
    ↓
agents_parlant/agent.py (Parlant Agent with guidelines)
    ↓
agents_parlant/tools.py (Task/Calendar operations)
    ↓
Response sent back to Telegram
```

### Guidelines

Parlant uses **guidelines** instead of system prompts. Guidelines are reliably matched and followed:

```python
await agent.create_guideline(
    condition="User asks about tasks",
    action="Use get_user_tasks tool to retrieve and display tasks",
    tools=[get_user_tasks]
)
```

Current guidelines cover:
- Task viewing and creation
- Calendar queries and event scheduling
- User information retrieval
- General conversation and help
- Error handling

### Tools

Tools are functions that the agent can call:

- `get_user_tasks`: Retrieve user's tasks
- `create_user_task`: Create a new task
- `get_calendar_events`: Get calendar events
- `create_calendar_event`: Schedule an event
- `get_user_info`: Get user information

## Example Interactions

### Task Management

**User**: "Show me my tasks"
**Bot**: [Calls `get_user_tasks` tool and displays formatted task list]

**User**: "Add task: Prepare presentation for Monday"
**Bot**: [Calls `create_user_task` tool, extracts details, creates task, confirms]

### Calendar

**User**: "What's on my calendar this week?"
**Bot**: [Calls `get_calendar_events` tool and displays upcoming events]

**User**: "Schedule a meeting tomorrow at 2pm"
**Bot**: [Calls `create_calendar_event` tool, creates event, confirms]

## Customization

### Adding New Guidelines

Edit `agents_parlant/agent.py`:

```python
await agent.create_guideline(
    condition="User asks about [your condition]",
    action="[what the agent should do]",
    tools=[relevant_tools]  # optional
)
```

### Adding New Tools

1. Create tool in `agents_parlant/tools.py`:

```python
@p.tool
async def my_new_tool(context: p.ToolContext, param: str) -> p.ToolResult:
    """Tool description for Parlant."""
    user_id = context.user_id  # Extract user_id from context
    # Your tool logic here
    return p.ToolResult("Result message")
```

2. Register tool in `agents_parlant/agent.py`:

```python
await agent.create_tool(my_new_tool)
```

3. Create guideline to use the tool:

```python
await agent.create_guideline(
    condition="User needs [your use case]",
    action="Use my_new_tool to [action]",
    tools=[my_new_tool]
)
```

## Fallback Behavior

If Parlant is disabled or encounters an error, the system automatically falls back to:
1. LangGraph multi-agent system
2. Traditional natural language handler

This ensures the bot always responds.

## Troubleshooting

### Parlant Not Working

1. **Check Installation**:
   ```bash
   pip list | grep parlant
   ```

2. **Check Configuration**:
   ```bash
   grep USE_PARLANT .env
   ```

3. **Check Logs**:
   Look for "Parlant Integration" messages in bot logs

4. **Verify API Compatibility**:
   The code tries multiple Parlant API patterns. If none work, check Parlant SDK documentation for the correct API.

### Tools Not Being Called

- Ensure guidelines match user messages correctly
- Check tool registration in `agent.py`
- Verify user_id is being passed correctly to tools
- Check logs for tool execution errors

### User ID Issues

Tools extract `user_id` from context in multiple ways:
- `context.user_id`
- `context.user.id`
- `context.get('user_id')` (if dict)

If tools can't find user_id, they'll return an error message.

## Comparison: Parlant vs LangGraph

| Feature | Parlant | LangGraph |
|---------|---------|-----------|
| Rule Following | ✅ Ensured | ⚠️ Prompt-based |
| Content Understanding | ✅ Strong | ✅ Strong |
| Task Completion | ✅ Reliable | ✅ Good |
| Multi-Agent | ⚠️ Single agent | ✅ Multi-agent |
| Complexity | ✅ Simple | ⚠️ More complex |

## Best Practices

1. **Start Simple**: Begin with basic guidelines, add complexity gradually
2. **Test Guidelines**: Ensure guidelines match user messages correctly
3. **Tool Validation**: Always validate inputs in tools
4. **Error Handling**: Provide clear error messages in tools
5. **User Context**: Always extract user_id correctly in tools

## Next Steps

- Review existing guidelines in `agents_parlant/agent.py`
- Add domain-specific guidelines for your use case
- Create custom tools for specialized operations
- Test with real user conversations
- Monitor logs for guideline matching and tool usage

## Resources

- [Parlant GitHub](https://github.com/emcie-co/parlant)
- [Parlant Documentation](https://www.parlant.io/docs)
- [Parlant Discord](https://discord.gg/duxWqxKk6J)

## Support

If you encounter issues:
1. Check the logs for detailed error messages
2. Verify Parlant SDK version compatibility
3. Test with simple messages first
4. Fall back to LangGraph if needed (set `USE_PARLANT=false`)

