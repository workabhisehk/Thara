# Parlant Integration Quick Start

## Installation

```bash
pip install parlant
```

## Enable Parlant

Add to your `.env` file:
```env
USE_PARLANT=true
```

## How It Works

1. **User sends message** on Telegram
2. **Telegram handler** routes to Parlant adapter
3. **Parlant session** processes message:
   - Creates customer (if new)
   - Creates session (if new)
   - Posts message to session
   - Waits for agent response
   - Retrieves agent message from events
4. **Response sent** back to Telegram

## Architecture

```
Telegram User
    ↓
telegram_bot/handlers/start.py
    ↓ (if USE_PARLANT=true)
agents_parlant/telegram_adapter.py
    ↓
agents_parlant/agent.py
    ├── get_or_create_session()
    │   ├── create_agent() [with guidelines & tools]
    │   ├── create_customer()
    │   └── create_session()
    └── process_message()
        ├── session.post_message()
        ├── session.list_events()
        └── extract AI response
    ↓
agents_parlant/tools.py
    ├── get_user_tasks()
    ├── create_user_task()
    ├── get_calendar_events()
    ├── create_calendar_event()
    └── get_user_info()
    ↓
Response → Telegram
```

## Key Components

### 1. Session Management
- Each Telegram user gets a Parlant customer
- Each conversation uses a Parlant session
- Sessions persist across messages

### 2. Guidelines
Rules that agents must follow:
- Task management guidelines
- Calendar operation guidelines
- General conversation guidelines
- Error handling guidelines

### 3. Tools
Functions agents can call:
- All tools receive `ToolContext` with customer/session info
- Tools extract `user_id` from customer mapping
- Tools return `ToolResult` with formatted responses

### 4. User ID Mapping
- `_customer_to_user_id` maps Parlant customer IDs to Telegram user IDs
- Tools use this mapping to identify users

## Testing

Run the test script:
```bash
python scripts/test_parlant_integration.py
```

## Troubleshooting

### Tools can't find user_id
- Check `_customer_to_user_id` mapping is populated
- Verify customer is created before tools are called
- Check logs for context extraction errors

### No agent response
- Increase wait time in `process_message()` (currently 1 second)
- Check Parlant server logs
- Verify guidelines are matching user messages

### Session errors
- Ensure Parlant server is initialized
- Check customer and agent are created before session
- Verify session is not expired

## Next Steps

1. **Customize Guidelines**: Edit `_setup_guidelines()` in `agent.py`
2. **Add Tools**: Create new tools in `tools.py` and register them
3. **Monitor**: Check logs for guideline matches and tool calls
4. **Optimize**: Adjust wait times and response handling

## Resources

- [Parlant Documentation](https://www.parlant.io/docs)
- [Parlant GitHub](https://github.com/emcie-co/parlant)
- [Integration Guide](../docs/PARLANT_INTEGRATION.md)

