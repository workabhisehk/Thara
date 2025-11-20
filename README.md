# AI Productivity Agent

A context-aware conversational AI assistant that helps you manage tasks, schedule commitments, and maintain productivity across work, education, and personal domains. Built with Telegram for conversations, Google Calendar for scheduling, and powered by Gemini AI with adaptive learning capabilities.

## Features

- **Conversational Interface**: Natural language interaction via Telegram
- **Intelligent Scheduling**: Automatic calendar integration with conflict detection
- **Adaptive Learning**: Memory system that learns from your habits and preferences
- **Multi-Domain Support**: Organize tasks across work, education, projects, and personal
- **Proactive Check-ins**: 30-minute intervals with contextual prompts
- **Weekly Reviews**: Strategic planning and analytics
- **Deadline Management**: Priority escalation and readiness forecasting

## Architecture

- **Backend**: Python 3.11+ with FastAPI
- **AI Framework**: LangChain with Gemini API (OpenAI fallback)
- **Memory System**: LlamaIndex + Supabase PostgreSQL with pgvector
- **Telegram Bot**: python-telegram-bot
- **Calendar**: Google Calendar API v3
- **Deployment**: Railway.app or Supabase

## Setup

### Prerequisites

- Python 3.11 or higher
- PostgreSQL database (Supabase recommended)
- Telegram Bot Token
- Google Cloud Project with Calendar API enabled
- Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Thara
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Set up database**
   ```bash
   # Run migrations
   alembic upgrade head
   ```

6. **Run the application**
   ```bash
   # Start the Telegram bot
   python bot_main.py
   
   # Or start FastAPI server (if needed)
   uvicorn main:app --reload
   ```

## Configuration

See `.env.example` for all required environment variables:

- `TELEGRAM_BOT_TOKEN`: Get from [@BotFather](https://t.me/botfather)
- `GEMINI_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`: Create OAuth2 credentials in Google Cloud Console
- `DATABASE_URL`: PostgreSQL connection string

## Project Structure

```
/
├── config.py                 # Configuration management
├── main.py                   # FastAPI app entry point
├── bot_main.py              # Telegram bot entry point
├── database/                # Database models and migrations
├── telegram_bot/            # Telegram bot handlers
├── calendar/                # Google Calendar integration
├── ai/                      # AI/LLM services (LangChain)
├── memory/                  # Memory system (LlamaIndex)
├── tasks/                   # Task management
├── scheduler/               # Background jobs
├── analytics/               # Analytics and reporting
└── tests/                   # Test suite
```

## Usage

1. Start a conversation with your bot on Telegram
2. Complete onboarding (set pillars, work hours, initial tasks)
3. Connect your Google Calendar
4. The agent will send daily summaries, check-ins, and weekly reviews

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
flake8 .
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

