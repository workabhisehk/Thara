# To-Do List - Prioritized by Dependencies

## 🔴 Critical Path (Must Do First)

### Phase 1: Environment Setup & Configuration
**Dependencies**: None  
**Estimated Time**: 30-60 minutes

#### For You (User):
- [x] **1.1** Get Telegram Bot Token ✅
  - Go to [@BotFather](https://t.me/botfather) on Telegram
  - Send `/newbot` and follow instructions
  - Save the bot token
  
- [x] **1.2** Get OpenAI API Key ✅
  - Go to [OpenAI Platform](https://platform.openai.com/api-keys)
  - Sign up or log in
  - Create API key
  - Save the key (you won't be able to see it again!)
  - Note: Free tier has $5 credit, then pay-as-you-go
  - Optional: Get Gemini API Key for fallback (if OpenAI fails)
    - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
- [x] **1.2b** Get Gemini API Key (optional fallback) ✅
  
- [x] **1.3** Set up Google Cloud Project (for Calendar API) ✅
  - Go to [Google Cloud Console](https://console.cloud.google.com/)
  - Create new project or select existing
  - Enable Google Calendar API
  - **Step 4: Configure OAuth Consent Screen** (see detailed instructions below)
  - Create OAuth 2.0 credentials (Web application)
  - Set redirect URI: `http://localhost:8000/auth/callback` (for local) or your deployment URL
  - Download credentials JSON (optional, we'll use env vars)
  
  **Detailed Step 4 - OAuth Consent Screen:**
  1. In Google Cloud Console:
     - Look at the left sidebar menu (hamburger menu ☰ if not visible)
     - Click **"APIs & Services"**
     - In the submenu, click **"OAuth consent screen"**
  2. **First Time Setup** - You'll see one of these:
     
     **Option A: If you see a page asking "What user type do you want to support?"**
     - You'll see two cards/buttons: "External" and "Internal"
     - Click on **"External"** (unless you have Google Workspace)
     - Click **"CREATE"** button at the bottom
     
     **Option B: If you see a form with fields like "App name", "User support email"**
     - You're already past the user type selection
     - Skip to step 3 below
     
     **Option C: If you see "OAuth consent screen" with tabs (App information, Scopes, Audience, etc.)**
     - The consent screen is already configured
     - You're on the right page! Look for these tabs at the top:
       - **App information** (or "OAuth consent screen")
       - **Scopes**
       - **Test users** (if External)
       - **Summary**
     - Click on **"App information"** tab first to fill in the app details
     - Then go to **"Scopes"** tab to add calendar permission
     - You can skip to Step 5 (Create OAuth credentials) after configuring these
  3. **App Information** page:
     - **App name**: "Thara Productivity Agent" (or any name you like)
     - **User support email**: Your email address
     - **App logo**: (optional, skip for now)
     - **App domain**: (optional, skip for now)
     - **Developer contact information**: Your email address
     - Click "Save and Continue"
  4. **Scopes** page:
     - Click "Add or Remove Scopes"
     - Search for "calendar" 
     - Check the box for: `https://www.googleapis.com/auth/calendar`
     - Click "Update"
     - Click "Save and Continue"
  5. **Test users** page (if External):
     - You can add your email as a test user (optional for now)
     - Click "Save and Continue"
  6. **Summary** page:
     - Review everything
     - Click "Back to Dashboard"
  
  **Note**: If you see "Publishing status: Testing", that's fine for now. You can use it in testing mode.
  
- [x] **1.4** Set up Database ✅
  - **Option A: Supabase (Recommended - Free tier)**
    - Go to [supabase.com](https://supabase.com)
    - Create account and new project
    - Get connection string from Settings > Database
    - ✅ Enable pgvector extension: Go to SQL Editor, run: `CREATE EXTENSION IF NOT EXISTS vector;` ✅
  - **Option B: Railway PostgreSQL**
    - Go to [railway.app](https://railway.app)
    - Create account
    - Create new project > Add PostgreSQL
    - Get connection string from Variables tab
  
- [x] **1.5** Create `.env` file ✅
  - Copy `.env.example` to `.env`
  - Fill in all required values:
    ```
    TELEGRAM_BOT_TOKEN=your_token_here
    OPENAI_API_KEY=your_key_here
    GEMINI_API_KEY=your_key_here (optional)
    DATABASE_URL=postgresql://user:pass@host:port/db
    GOOGLE_CLIENT_ID=your_client_id
    GOOGLE_CLIENT_SECRET=your_client_secret
    GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
    ```

#### For Me (AI/Development):
- [ ] **1.6** Fix any missing dependencies in `requirements.txt`
- [ ] **1.7** Create database initialization script improvements
- [ ] **1.8** Add environment validation on startup

---

### Phase 2: Database Setup
**Dependencies**: Phase 1 complete  
**Estimated Time**: 15-30 minutes

#### For You:
- [ ] **2.1** Install Python dependencies
  ```bash
  # Create virtual environment (if not done)
  python3 -m venv venv
  source venv/bin/activate  # Mac/Linux
  # OR venv\Scripts\activate  # Windows
  
  # Install dependencies
  pip install -r requirements.txt
  ```

- [ ] **2.2** Create initial database migration
  ```bash
  # Make sure you're in the project directory and venv is activated
  alembic revision --autogenerate -m "Initial schema"
  ```
  This creates the migration file based on your database models.

- [ ] **2.3** Run database migrations
  ```bash
  alembic upgrade head
  ```
  This creates all the tables in your database.

#### For Me:
- [ ] **2.4** Verify all models are included in migration
- [ ] **2.5** Test database connection

---

### Phase 3: Local Testing
**Dependencies**: Phase 2 complete  
**Estimated Time**: 30-60 minutes

#### For You:
- [ ] **3.1** Test bot locally
  ```bash
  python bot_main.py
  ```
  
- [ ] **3.2** Test `/start` command on Telegram
  - Start conversation with your bot
  - Complete onboarding flow
  
- [ ] **3.3** Test Google Calendar connection
  - Follow OAuth flow when prompted
  - Verify calendar sync works

#### For Me:
- [ ] **3.4** Fix any runtime errors
- [ ] **3.5** Improve error messages
- [ ] **3.6** Add better logging

---

### Phase 4: Deployment Preparation
**Dependencies**: Phase 3 complete  
**Estimated Time**: 30-45 minutes

#### For You:
- [ ] **4.1** Choose deployment platform (see DEPLOYMENT.md)
  - Railway.app (recommended for simplicity)
  - Render.com
  - Fly.io
  - Self-hosted (VPS)

- [ ] **4.2** Update `GOOGLE_REDIRECT_URI` in `.env` with deployment URL
  - Format: `https://your-domain.com/auth/callback`

#### For Me:
- [ ] **4.3** Create deployment configuration files
- [ ] **4.4** Add health check endpoints
- [ ] **4.5** Optimize Dockerfile if needed

---

### Phase 5: Deployment
**Dependencies**: Phase 4 complete  
**Estimated Time**: 30-60 minutes

#### For You:
- [ ] **5.1** Deploy to chosen platform (see DEPLOYMENT.md for instructions)
- [ ] **5.2** Set environment variables on deployment platform
- [ ] **5.3** Verify bot is running
- [ ] **5.4** Test all features in production

#### For Me:
- [ ] **5.5** Create deployment troubleshooting guide
- [ ] **5.6** Add monitoring/logging setup

---

## 🟡 Important (Do After Critical Path)

### Phase 6: Feature Testing & Refinement
**Dependencies**: Phase 5 complete  
**Estimated Time**: 2-4 hours

#### For You:
- [ ] **6.1** Test all commands (`/start`, `/tasks`, `/calendar`, `/prioritize`, `/help`)
- [ ] **6.2** Test task creation with estimated time
- [ ] **6.3** Test time-based reminders
- [ ] **6.4** Test AI prioritization
- [ ] **6.5** Test calendar integration
- [ ] **6.6** Test daily kickoff summaries
- [ ] **6.7** Test weekly reviews

#### For Me:
- [ ] **6.8** Fix any bugs found
- [ ] **6.9** Improve user experience based on feedback
- [ ] **6.10** Add missing error handling

---

### Phase 7: Production Hardening
**Dependencies**: Phase 6 complete  
**Estimated Time**: 1-2 hours

#### For You:
- [ ] **7.1** Set up monitoring/alerting (optional)
- [ ] **7.2** Configure backup strategy for database
- [ ] **7.3** Review security settings

#### For Me:
- [ ] **7.4** Add rate limiting
- [ ] **7.5** Improve error recovery
- [ ] **7.6** Add comprehensive logging
- [ ] **7.7** Create backup/restore scripts

---

## 🟢 Nice to Have (Future Enhancements)

### Phase 8: Advanced Features
**Dependencies**: Phase 7 complete  
**Estimated Time**: Ongoing

#### For You:
- [ ] **8.1** Customize work hours per day of week
- [ ] **8.2** Set up task templates
- [ ] **8.3** Configure notification preferences

#### For Me:
- [ ] **8.4** Implement natural language time parsing
- [ ] **8.5** Add task templates feature
- [ ] **8.6** Implement smart task breakdown
- [ ] **8.7** Add energy/productivity tracking
- [ ] **8.8** Improve conversation context persistence
- [ ] **8.9** Add multi-language support

---

## 📋 Quick Reference Checklist

### Before First Run:
- [ ] All API keys obtained
- [ ] Database set up and accessible
- [ ] `.env` file configured
- [ ] Dependencies installed
- [ ] Database migrations run

### Before Deployment:
- [ ] Local testing successful
- [ ] All environment variables ready
- [ ] Deployment platform chosen
- [ ] Redirect URIs updated

### After Deployment:
- [ ] Bot responds to commands
- [ ] Calendar integration works
- [ ] Scheduled jobs running
- [ ] No errors in logs

---

## 🚨 Blockers & Issues

If you encounter issues, check:
1. **Database connection errors** → Verify DATABASE_URL format
2. **Telegram bot not responding** → Check TELEGRAM_BOT_TOKEN
3. **Calendar OAuth fails** → Verify redirect URI matches exactly
4. **Scheduler not working** → Check timezone settings
5. **AI errors** → Verify OPENAI_API_KEY is valid

---

## 📊 Progress Tracking

**Current Phase**: Phase 2 - Database Setup  
**Phase 1 Completed**: ✅
- ✅ 1.1 - Telegram Bot Token
- ✅ 1.2 - OpenAI API Key
- ✅ 1.2b - Gemini API Key (optional)
- ✅ 1.3 - Google Cloud Project + OAuth Credentials
- ✅ 1.4 - Database (Supabase) + pgvector extension enabled
- ✅ 1.5 - .env file created with all credentials

**Next Steps (Phase 2)**: 
1. Install Python dependencies (2.1)
2. Run database migrations (2.2)

**Next Milestone**: Complete Phase 1 and move to Phase 2  
**Estimated Time to MVP**: 3-4 hours  
**Estimated Time to Production**: 6-8 hours

