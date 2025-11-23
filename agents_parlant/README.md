# Parlant Integration for Thara

This module integrates [Parlant](https://github.com/emcie-co/parlant) with the Thara Telegram bot to provide rule-following AI agent behavior.

## Overview

Parlant ensures that AI agents follow guidelines and rules reliably, which is perfect for:
- **Content Understanding**: Better understanding of user intent and context
- **Task Completion**: Reliable execution of tasks with proper validation
- **Rule Following**: Ensured compliance with business rules and guidelines

## Features

- ✅ **Guidelines**: Define behavioral rules that agents must follow
- ✅ **Tools**: Integrate with existing task and calendar services
- ✅ **Journeys**: Structured conversation flows (can be extended)
- ✅ **Telegram Integration**: Seamless integration with Telegram bot

## Setup

1. **Install Parlant**:
   ```bash
   pip install parlant
   ```

2. **Enable Parlant** in your `.env` file:
   ```env
   USE_PARLANT=true
   ```

3. **Restart the bot** - Parlant will be used for natural language processing instead of LangGraph.

## Architecture

```
Telegram Message
    ↓
telegram_bot/handlers/start.py
    ↓
agents_parlant/telegram_adapter.py
    ↓
agents_parlant/agent.py (Parlant Agent)
    ↓
agents_parlant/tools.py (Task/Calendar Tools)
    ↓
Response → Telegram
```

## Tools Available

The Parlant agent has access to these tools:

1. **get_user_tasks**: Retrieve user's tasks (active, completed, or all)
2. **create_user_task**: Create a new task with validation
3. **get_calendar_events**: Get calendar events for upcoming days
4. **create_calendar_event**: Schedule a calendar event
5. **get_user_info**: Get user information and preferences

## Guidelines

The agent follows these guidelines:

- **Task Management**: Automatically uses tools when users ask about or want to create tasks
- **Calendar Operations**: Handles calendar queries and event creation
- **Clarification**: Asks for missing information before executing actions
- **Error Handling**: Provides clear error messages and next steps
- **Friendliness**: Maintains a warm, helpful tone

## Usage

Once enabled, users can interact naturally:

```
User: "Show me my tasks"
Bot: [Uses get_user_tasks tool and displays tasks]

User: "Add task: Prepare presentation for Monday"
Bot: [Uses create_user_task tool and confirms creation]

User: "What's on my calendar this week?"
Bot: [Uses get_calendar_events tool and displays events]
```

## Configuration

You can customize the agent behavior by modifying:
- `agents_parlant/agent.py`: Add more guidelines or modify existing ones
- `agents_parlant/tools.py`: Add new tools or modify existing ones

## Fallback Behavior

If Parlant is not enabled or encounters an error, the system falls back to:
1. LangGraph multi-agent system
2. Traditional natural language handler

This ensures the bot always responds, even if Parlant has issues.

## Notes

- Each user gets their own Parlant agent instance for personalized context
- Tools automatically handle user identification from Telegram user IDs
- All database operations use the existing async session pattern
- Error handling is built into tools and guidelines

## Troubleshooting

If Parlant isn't working:

1. Check that `USE_PARLANT=true` in your `.env` file
2. Verify Parlant is installed: `pip list | grep parlant`
3. Check logs for Parlant-specific errors
4. The bot will automatically fall back to LangGraph if Parlant fails

