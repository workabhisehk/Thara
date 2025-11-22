# Comprehensive Plan: AI Productivity Agent Bot

## Table of Contents
1. [User Flow](#user-flow)
2. [Agent Flow](#agent-flow)
3. [Edge Cases](#edge-cases)
4. [Menu Options & Sub-Options](#menu-options--sub-options)
5. [Operations](#operations)
6. [Use Cases](#use-cases)
7. [Execution Plan](#execution-plan)

## Key Features

### Adaptive Learning & Self-Improvement
The agent is designed to be **adaptive and self-improving**, learning from every interaction:

- **Learning from Mistakes**: The agent learns from user corrections, storing feedback and updating its models to improve accuracy over time
- **Automatic Flow Creation**: Detects recurring patterns in user behavior and suggests automatic workflows (e.g., recurring tasks, task sequences)
- **Behavioral Adaptation**: Continuously monitors user behavior (response times, task completion, scheduling preferences) and adapts agent behavior accordingly
- **Self-Improvement Mechanisms**: Tracks mistakes, calibrates confidence, and creates personalized rules for each user
- **Pattern Recognition**: Identifies patterns in task creation, scheduling, habits, and daily routines to provide better suggestions
- **Real-time Learning**: Every interaction, correction, and acceptance improves future interactions

See sections [5. Adaptive Learning Flow](#5-adaptive-learning-flow-learn-from-mistakes--corrections), [6. Automatic Flow Creation Flow](#6-automatic-flow-creation-flow-behavior-based-automation), and [7. Behavior-Based Adaptation Flow](#7-behavior-based-adaptation-flow-daily-behavior-learning) for detailed flows.

---

## User Flow

### 1. Onboarding Flow (New User)

```
User sends /start
  ↓
Bot checks if user exists in database
  ↓
[User NOT exists] → Create user record → Set state: ONBOARDING_PILLARS
  ↓
[User exists but NOT onboarded] → Set state: ONBOARDING_PILLARS
  ↓
Bot sends welcome message:
  "Hello! 👋 I'm your AI Productivity Agent. My mission is to help you manage tasks, "
  "schedule commitments, and maintain productivity across work, education, and personal domains.\n\n"
  "Let's get you set up! This will only take a few minutes.\n\n"
  "First, which categories (pillars) would you like to track?\n"
  "You can select from common categories or create your own custom categories."
  ↓
Bot shows pillar selection keyboard:
  [Work] [Education] [Projects] [Personal] [Other]
  [➕ Add Custom Pillar] [✅ Done] [Skip]
  ↓
User can:
  - Select/deselect predefined pillars (multiple allowed, toggle on/off)
  - Click "➕ Add Custom Pillar" to create custom category
  ↓
[User clicks "➕ Add Custom Pillar"] → Set state: ONBOARDING_CUSTOM_PILLAR
  ↓
Bot asks: "What would you like to name your custom category?\n\n"
  "Examples: Fitness, Side Projects, Family, Learning, etc.\n"
  "Type the name:"
  ↓
User types custom pillar name (e.g., "Fitness", "Side Projects")
  ↓
Bot validates:
  - Check length (max 50 characters)
  - Check for duplicates (user already has this pillar)
  - Normalize name (trim, capitalize)
  ↓
[Invalid name] → Show error → Ask again
[Valid name] → Add to user's pillar list → Show updated list
  ↓
Bot shows: "✅ Added custom category: 'Fitness'\n\n"
  "Current categories:\n"
  "• Work ✅\n"
  "• Education ✅\n"
  "• Fitness ✅ (custom)\n\n"
  "Select more categories or [Done] to continue:"
  [Work] [Education] [Projects] [Personal] [Other]
  [➕ Add Custom Pillar] [✅ Done]
  → Set state: ONBOARDING_PILLARS (return to pillar selection)
  ↓
[User can add multiple custom pillars] → Repeat custom pillar flow
  ↓
[User clicks "✅ Done" or types "done"] → Validate at least one pillar selected
  ↓
[No pillars selected] → Bot: "Please select at least one category to continue."
  → Return to pillar selection
  ↓
[At least one pillar selected] → Store all pillars (predefined + custom) → Set state: ONBOARDING_WORK_HOURS
  ↓
Bot confirms: "✅ Categories saved:\n"
  "• Work\n"
  "• Education\n"
  "• Fitness (custom)\n\n"
  "You can add more categories later in Settings."
  ↓
Bot asks: "What are your work hours? (e.g., 9 AM - 5 PM)\n\n"
  "You can type: '9 AM to 5 PM' or use 24-hour format: '09:00-17:00'"
  ↓
User responds with work hours (parse with AI/NLP or manual parsing)
  ↓
Bot validates and stores:
  - work_start_hour (e.g., 9)
  - work_end_hour (e.g., 17)
  → Set state: ONBOARDING_TIMEZONE
  ↓
Bot asks: "What timezone are you in?\n\n"
  "Examples: PST, EST, UTC, GMT+5:30, America/New_York\n"
  "Or select from common timezones:"
  [Common Timezones Keyboard: PST/EST/CST/MST/UTC]
  ↓
User responds with timezone OR selects from keyboard
  ↓
Bot validates timezone → Store timezone → Set state: ONBOARDING_INITIAL_TASKS
  ↓
Bot confirms: "✅ Calendar integration is already configured!\n\n"
  "I can schedule tasks and detect conflicts with your calendar events.\n"
  "(Note: Google Calendar is pre-integrated for now. "
  "Future option to connect personal calendar will be available in Settings.)"
  ↓
Bot asks: "Would you like to add some initial tasks to get started?\n\n"
  [Yes, Add Tasks] [No, Skip] [Show Me Around]
  ↓
[User selects Yes] → Task creation flow (guided, create 1-3 tasks)
[User selects No] → Skip to next step
[User selects Show Me Around] → Show brief tutorial → Skip to next step
  → Set state: ONBOARDING_HABITS
  ↓
Bot asks: "Would you like to set up any daily habits to track?\n\n"
  "Examples: Drink water (8 glasses/day), Exercise (30 min/day), Meditation (10 min/day)\n\n"
  "Habits help you build consistency and maintain well-being.\n\n"
  [Yes, Add Habits] [No, Skip] [Maybe Later]
  ↓
[User selects Yes] → Habit creation flow (guided, create 1-3 habits)
[User selects No] → Skip to next step
[User selects Maybe Later] → Skip to next step
  → Set state: ONBOARDING_MOOD_TRACKING
  ↓
Bot asks: "Would you like to enable mood tracking for mental health insights?\n\n"
  "I can help you track your daily mood and provide insights on how your mood "
  "relates to your productivity and habits.\n\n"
  [Yes, Enable] [No, Skip] [Tell Me More]
  ↓
[User selects Yes] → Enable mood tracking → Set mood_tracking_enabled = True
[User selects No] → Skip mood tracking
[User selects Tell Me More] → Show mood tracking info → Ask again
  ↓
Mark user as onboarded (is_onboarded = True) → Set state: NORMAL
  ↓
Bot sends completion message:
  "🎉 Welcome to your AI Productivity Agent!\n\n"
  "You're all set up and ready to go. Here's what you can do:\n\n"
  "📋 Tasks: Create and manage tasks naturally\n"
  "📅 Calendar: View and schedule your commitments\n"
  "🤖 AI Assistant: I'll help prioritize and suggest actions\n"
  "📊 Insights: Get daily summaries and weekly reviews\n\n"
  "Try saying: 'Add task: Prepare presentation for client meeting'\n"
  "Or use /help to see all commands.\n\n"
  "Let's make you more productive! 🚀"
```

### 2. Task Management Flow

#### 2.1 Create Task (Natural Language)
```
User: "Add task: Prepare presentation for client meeting"
  ↓
Bot: "🤔 Processing your message..."
  ↓
AI Intent Extraction:
  - Intent: add_task
  - Entities: {task: "Prepare presentation for client meeting"}
  ↓
AI Task Categorization:
  - Extracts context from user history
  - Gets user's available pillars (predefined + custom)
  - Categorizes into pillar (suggests best match from user's pillars)
  ↓
Bot asks for confirmation:
  "📋 Task: Prepare presentation for client meeting
   Category: Work
   
   Is this correct? (Yes/No)"
  ↓
[User confirms] → Store in context → Next questions
[User corrects] → Update and ask again
  ↓
Bot asks: "What's the priority? (High/Medium/Low)"
  ↓
User selects priority OR responds naturally
  ↓
Bot asks: "When is it due? (e.g., tomorrow, Dec 25, next week)"
  ↓
User responds with due date (AI parses natural language)
  ↓
Bot asks: "How long do you estimate this will take? (e.g., 2 hours, 30 minutes)"
  ↓
User responds with estimated duration
  ↓
Bot creates task in database
  ↓
Bot confirms: "✅ Task created! I'll remind you before the deadline."
```

#### 2.2 Create Task (Command-based)
```
User sends /tasks
  ↓
Bot shows: "📋 Your Active Tasks: [list]"
  
  + "Options:"
  - Add Task
  - View All Tasks
  - Filter by Pillar
  - Filter by Priority
  - Sort Options
  ↓
User clicks "Add Task"
  ↓
Bot asks: "What's the task title?"
  ↓
User responds with title
  ↓
Bot shows pillar selection keyboard:
  - Shows all user's pillars (predefined + custom)
  - [Work] [Education] [Projects] [Personal] [Other] [Custom Pillars...]
  - [➕ Add New Pillar] (to create on-the-fly)
  ↓
User selects pillar from their available categories OR adds new pillar
  ↓
Bot shows priority selection keyboard
  ↓
User selects priority
  ↓
Bot asks: "When is it due? (Send date or 'none')"
  ↓
User responds
  ↓
Bot asks: "Estimated duration? (Send minutes or 'none')"
  ↓
User responds
  ↓
Bot shows summary and confirmation keyboard
  ↓
[User confirms] → Create task → Success message
[User cancels] → Cancel operation
```

#### 2.3 View Tasks
```
User sends /tasks
  ↓
Bot queries database for user's active tasks
  ↓
Groups tasks by:
  - Priority (High/Medium/Low)
  - Pillar (User's defined categories: predefined + custom)
  - Due Date (Overdue/Today/Tomorrow/This Week/Upcoming)
  ↓
Bot formats message:
  "📋 Your Active Tasks:
  
  🔴 HIGH PRIORITY (2)
  1. Prepare presentation (due: 2024-12-25)
  2. Review proposal (due: 2024-12-24)
  
  🟡 MEDIUM PRIORITY (3)
  3. Update documentation
  4. Team meeting prep
  
  🟢 LOW PRIORITY (1)
  5. Organize desk
  
  Options: [View Details] [Filter] [Sort] [Add Task]"
```

#### 2.4 Update Task
```
User clicks on task OR sends: "Update task: [task ID or name]"
  ↓
Bot shows task details:
  "📋 Task: Prepare presentation
   Status: In Progress
   Priority: High
   Due: 2024-12-25
   Pillar: Work
   
   Options: [Complete] [Edit] [Schedule] [Delete] [Set Reminder]"
  ↓
[User clicks Edit] → Shows edit options:
  - Change Title
  - Change Priority
  - Change Due Date
  - Change Status
  - Change Pillar
  - Add Description
  ↓
User selects field to edit
  ↓
Bot asks for new value
  ↓
User responds
  ↓
Bot shows confirmation
  ↓
[User confirms] → Update task → Success
```

#### 2.5 Complete Task
```
User clicks "Complete" on task OR sends: "Complete task: [name/ID]"
  ↓
Bot asks for confirmation
  ↓
[User confirms] → Update status to COMPLETED
  ↓
Bot asks: "How long did it actually take? (e.g., 1.5 hours)"
  ↓
User responds (optional) → Store actual_duration
  ↓
Bot updates analytics
  ↓
Bot sends: "✅ Task completed! Great job!"
  
  [If completed early] "You finished 30 minutes ahead of schedule! 🎉"
  [If completed late] "Task completed (10 minutes over estimate)."
  [If no estimate] "Task completed! 📝"
```

#### 2.6 Delete Task
```
User clicks "Delete" on task
  ↓
Bot asks: "⚠️ Are you sure you want to delete this task?
  
  Task: [task title]
  
  This action cannot be undone."
  ↓
[User confirms] → Delete task (soft delete: mark as CANCELLED)
  ↓
Bot sends: "🗑️ Task deleted."
```

### 3. Calendar Flow

#### 3.1 Connect Calendar
```
User sends /calendar
  ↓
[Calendar NOT connected] → Bot shows:
  "📅 Google Calendar Not Connected
  
  To connect your calendar:
  [Click here to authorize]
  
  After authorizing, use /calendar again to see your events."
  ↓
User clicks link → OAuth flow
  ↓
Google redirects to callback URL with code
  ↓
Bot exchanges code for tokens
  ↓
Store tokens in database → Mark calendar_connected = True
  ↓
Bot sends: "✅ Calendar connected! Use /calendar to view events."
```

#### 3.2 View Calendar
```
User sends /calendar
  ↓
[Calendar connected] → Bot fetches events from Google Calendar API
  ↓
Group events by date (next 7 days)
  ↓
Format message:
  "📅 Your Calendar (Next 7 Days)
  
  📆 Today, December 20
    • 10:00 AM: Team Meeting
    • 2:00 PM: Client Call 📍 Conference Room A
  
  📆 Tomorrow, December 21
    • 9:00 AM: Project Review
  
  📆 Monday, December 23
    • All day: Holiday
  
  Options: [View More] [Sync Now] [Schedule Task]"
```

#### 3.3 Schedule Task on Calendar (With Confirmation)
```
User clicks "Schedule" on task OR requests: "Schedule [task name]"
  ↓
Bot checks calendar availability (next 7 days)
  ↓
Bot finds available time slots based on:
  - Task estimated_duration
  - User work_hours
  - Existing calendar events
  - Task due_date (prefer slots before deadline)
  - Preparation time (if task needs prep, schedule earlier)
  ↓
Bot suggests time slots:
  "⏰ Suggested times for 'Prepare presentation' (2 hours):
  
  1. Tomorrow, Dec 21, 10:00 AM - 12:00 PM ⭐ Recommended
     Reason: Before deadline, high-energy morning slot
  
  2. Tomorrow, Dec 21, 2:00 PM - 4:00 PM
     Reason: Afternoon slot, still before deadline
  
  3. Wednesday, Dec 23, 9:00 AM - 11:00 AM
     Reason: Early morning, focused time
  
  [Select 1] [Select 2] [Select 3] [Custom Time] [Cancel]"
  ↓
[User selects slot] → Bot shows confirmation:
  "📅 Confirm Scheduling:
  
  Task: Prepare presentation
  Duration: 2 hours
  Time: Tomorrow, Dec 21, 10:00 AM - 12:00 PM
  Priority: High
  Due: Dec 22 (1 day after scheduled time)
  
  This will:
  ✅ Create calendar event on Google Calendar
  ✅ Link task to calendar event
  ✅ Sync task list with calendar
  
  Confirm to schedule?"
  
  [✅ Confirm] [❌ Cancel] [Edit Time]
  ↓
[User confirms] → 
  Create calendar event via Google Calendar API
  ↓
Link event to task:
  - Store calendar_event_id in task.calendar_event_id
  - Store scheduled_start and scheduled_end in task
  - Create CalendarEvent record in database
  ↓
Update task status (if applicable):
  - Set task.scheduled_start and task.scheduled_end
  - Optionally set status to IN_PROGRESS (if scheduled for today)
  ↓
Bot sends confirmation:
  "✅ Task scheduled on your calendar!
  
  📅 Event created: Prepare presentation
  ⏰ Time: Tomorrow, Dec 21, 10:00 AM - 12:00 PM
  📋 Linked to task: Prepare presentation
  
  Calendar and task list are now synced! ✅
  
  You'll receive reminders before the scheduled time."
  
  [View Calendar] [Edit Task] [Schedule Another]
```

#### 3.4 Bidirectional Sync (Tasks ↔ Calendar)

**Principle**: Tasks and Google Calendar must stay in sync at all times based on:
- **To-dos**: Tasks with due dates or scheduled times
- **Due dates**: When tasks have deadlines
- **Preparation time**: Time needed before deadlines

**Sync Triggers**:
- Task created/updated/deleted
- Due date changed
- Calendar event created/updated/deleted externally
- Periodic sync (every 4 hours)
- On-demand sync

**Sync Rules**:

##### Task → Calendar Sync:
```
When task is created/updated with:
  - due_date AND estimated_duration
  → Calculate preparation time needed
  → Find optimal time slot (due_date - estimated_duration - prep_time)
  → Suggest scheduling to user
  → If user confirms, create calendar event

When task scheduled_start/scheduled_end changes:
  → Update linked calendar event
  → Or create new event if not linked

When task is completed:
  → Mark calendar event as completed (if linked)
  → Or remove scheduled event

When task is deleted:
  → Delete linked calendar event (if exists)
  → Clean up sync relationship
```

##### Calendar → Task Sync:
```
When calendar event is created externally:
  → Check if event matches existing task (by title/time)
  → If match found, link task to event
  → If no match, ask user if event is related to a task

When calendar event is updated externally:
  → Update linked task's scheduled_start/scheduled_end
  → Recalculate task timing

When calendar event is deleted externally:
  → If linked to task, clear task's calendar_event_id
  → Clear task's scheduled_start/scheduled_end
  → Ask user if task should be rescheduled

When calendar event time changes:
  → Update linked task's scheduled times
  → Check for deadline conflicts
  → Warn if event moved past task due_date
```

##### Sync Based on Due Dates:
```
For tasks with due_date:
  → If task has estimated_duration:
    * Calculate latest start time: due_date - estimated_duration - prep_time
    * If no scheduled time OR scheduled time is after latest start time:
      → Suggest rescheduling or warn user
  → If task approaching deadline (e.g., within 1 day):
    * If not scheduled, create urgent scheduling suggestion
    * Send reminder to schedule immediately
```

##### Sync Based on Preparation Time:
```
When task requires preparation:
  → Add buffer time before scheduled start time
  → Schedule prep time as separate event (optional)
  → Or extend task scheduled time to include prep
  
Preparation time rules:
  - High priority tasks: 30 min - 1 hour prep
  - Urgent deadlines: 1-2 hours prep
  - Complex tasks: Based on task complexity
  - User-defined prep time
```

##### Automatic Sync Operations:
```
1. **On Task Change**:
   Task created/updated → Check if needs calendar sync → Suggest/auto-sync

2. **On Calendar Change** (external):
   Calendar API webhook → Detect changes → Sync to tasks → Notify user

3. **Periodic Sync** (every 4 hours):
   Compare tasks and calendar events → Detect mismatches → Sync → Notify conflicts

4. **Deadline-Based Sync**:
   Task approaching deadline → Check if scheduled → If not, suggest scheduling

5. **Confirmation-Based Sync**:
   Always ask user before:
   - Creating calendar events
   - Modifying existing calendar events
   - Deleting calendar events
   - Rescheduling tasks based on calendar changes
```

##### Sync Conflict Resolution:
```
When conflict detected:
  → Notify user with conflict details
  → Show both versions (task vs calendar)
  → Offer resolution options:
    * Keep task version (update calendar)
    * Keep calendar version (update task)
    * Manual resolution
    * Accept both (if different enough)
```

#### 3.5 Detect Conflicts
```
User schedules task at time with existing event
  ↓
Bot detects conflict:
  "⚠️ Time Conflict Detected!
  
  You have another event at this time:
  - Team Meeting (2:00 PM - 3:00 PM)
  
  Options:
  [Suggest Alternative Time] [Schedule Anyway] [Cancel]"
  ↓
[User selects Suggest Alternative] → Show next available slots
[User selects Schedule Anyway] → Create event (overlap warning)
[User selects Cancel] → Cancel scheduling
```

### 4. Natural Language Interaction Flow

```
User sends any message
  ↓
Bot stores conversation in database + vector store
  ↓
AI Intent Extraction:
  - Analyze message text
  - Retrieve relevant context from memory
  - Extract intent + entities
  ↓
Intent Classification:
  - add_task
  - show_tasks
  - update_task
  - complete_task
  - delete_task
  - schedule
  - calendar_query
  - settings_query
  - general_chat
  - clarification_needed
  ↓
[Intent identified] → Route to appropriate handler
  ↓
Handler processes request → Generates response
  ↓
[Clarification needed] → Bot asks follow-up questions
  ↓
Bot sends response
  ↓
Store conversation for learning
```

### 5. Settings Flow

```
User sends /settings
  ↓
Bot shows settings menu:
  "⚙️ Settings
  
  Current Settings:
  • Work Hours: 9:00 AM - 5:00 PM
  • Timezone: PST
  • Check-in Interval: 30 minutes
  • Active Pillars: Work, Education, Projects, Fitness (custom)
  
  Options:
  [Edit Work Hours] [Change Timezone] [Check-in Settings]
  [Manage Pillars] [Calendar Settings] [Notification Settings]
  [Privacy Settings] [Reset/Delete Account]"
  ↓
User selects setting to change
  ↓
Bot asks for new value
  ↓
User responds
  ↓
Bot validates and saves
  ↓
Bot confirms: "✅ Setting updated!"
```

### 6. Habit Management Flow

#### 6.1 Create Habit
```
User sends /habits OR "Add habit: Drink water"
  ↓
[Command-based] → Bot asks: "What habit would you like to track?"
[Natural Language] → AI extracts habit name from message
  ↓
Bot asks for habit details:
  "Tell me about this habit:\n"
  "1. Habit name: [pre-filled if from NL]\n"
  "2. Target frequency: (e.g., 8 times/day, 30 min/day, once/day)\n"
  "3. Reminder time(s): (optional)\n"
  "4. Unit: (times, minutes, glasses, miles, etc.)\n\n"
  "Please provide:"
  ↓
User responds with habit details OR fills form step-by-step
  ↓
Bot validates and creates habit:
  - name: "Drink Water"
  - target_frequency: 8 (per day)
  - unit: "glasses"
  - reminder_times: ["09:00", "12:00", "15:00", "18:00"]
  - tracking_method: "increment" or "duration"
  ↓
Bot confirms: "✅ Habit created: Drink Water (8 glasses/day)\n\n"
  "I'll remind you at 9 AM, 12 PM, 3 PM, and 6 PM to track your water intake."
  ↓
Store habit in database → Set up reminder schedule
```

#### 6.2 Track Habit Progress
```
User receives habit reminder OR sends: "Log water: 2 glasses"
  ↓
Bot shows current progress:
  "💧 Drink Water Progress\n\n"
  "Today: 2/8 glasses ✅\n"
  "Remaining: 6 glasses\n"
  "Last logged: 2 hours ago\n\n"
  "Log progress:"
  [➕ Log 1 Glass] [➕ Log 2 Glasses] [➕ Log More...] [Skip]
  ↓
[User clicks increment] → Update daily progress
[User types amount] → Parse and update progress
  ↓
Bot updates habit log:
  - date: today
  - logged_value: 2
  - cumulative_today: 4 (was 2, added 2)
  ↓
Bot confirms: "✅ Logged! 4/8 glasses today (50% complete) 🎉"
  
  [If target reached] → "🎉 Congratulations! You've reached your daily goal!"
  [If approaching target] → "Keep going! Only 2 more glasses to go!"
  [If behind schedule] → "You're a bit behind. Try to catch up! 💪"
```

#### 6.3 View Habit Statistics
```
User sends /habits OR "Show my habits"
  ↓
Bot shows all active habits with today's progress:
  "📊 Your Habits (Today)\n\n"
  "💧 Drink Water: 6/8 glasses (75%) ⏰ 2 reminders left\n"
  "  Last: 1 hour ago\n\n"
  "🏃 Exercise: 0/30 minutes (0%) ⏰ Reminder at 7 PM\n"
  "  Status: Not started\n\n"
  "🧘 Meditation: 10/10 minutes (100%) ✅\n"
  "  Completed at 7:00 AM\n\n"
  "📖 Reading: 0/20 pages (0%)\n"
  "  No reminder set\n\n"
  "Options: [View Details] [Log Progress] [Edit Habit] [Delete]"
```

#### 6.4 Daily Habit Check-in
```
Scheduler triggers (based on reminder_times)
  ↓
For each habit with reminder at this time:
  - Check if already logged today
  - Check current progress vs target
  ↓
Generate personalized reminder:
  "💧 Water Reminder!\n\n"
  "You're at 4/8 glasses today (50%).\n"
  "Time for your next glass! 💪\n\n"
  "Track it:"
  [✅ Done (Log 1)] [➕ Log Amount...] [Skip] [Snooze 1hr]
  ↓
[User logs progress] → Update progress → Provide encouragement
[User skips] → Mark as "skipped" → Update streak if applicable
```

### 7. Mood Tracking Flow

#### 7.1 Log Mood
```
User sends /mood OR "I'm feeling happy" OR receives mood check-in
  ↓
Bot shows mood tracking interface:
  "😊 How are you feeling right now?\n\n"
  "Select your mood:"
  [😊 Great] [😌 Good] [😐 Okay] [😔 Low] [😰 Stressed] [😴 Tired]
  [➕ More Options...]
  ↓
[User selects mood] → Store mood entry:
  - mood: "happy"
  - intensity: 4 (1-5 scale)
  - timestamp: now
  - context: optional (can ask "What's making you feel this way?")
  ↓
[Optional: Context Collection]
  Bot asks: "What's contributing to how you're feeling? (optional)\n"
  "You can mention activities, events, or just skip."
  ↓
[User provides context] → Store context with mood entry
[User skips] → Store mood only
  ↓
Bot confirms: "✅ Mood logged: 😊 Great\n\n"
  "You can view your mood trends anytime with /mood or in your weekly review."
  
  [If first time today] → "This is your first mood entry today. Great start!"
  [If multiple today] → "You've logged 3 moods today. Keeping track helps!"
```

#### 7.2 Mood Check-in Flow (Proactive)
```
Scheduler triggers (configurable times, e.g., morning, evening)
  OR
User has mood_tracking_enabled and hasn't logged today
  ↓
Bot sends gentle check-in:
  "👋 Quick Check-in\n\n"
  "How are you feeling right now?\n\n"
  "Taking a moment to check in with yourself can help with productivity and well-being. 💙\n\n"
  [😊 Great] [😌 Good] [😐 Okay] [😔 Low] [😰 Stressed] [Maybe Later]
  ↓
[User selects mood] → Log mood → Acknowledge
[User selects Maybe Later] → Schedule reminder for later
  ↓
[If mood is low/stressed] → Offer support:
  "I notice you're feeling a bit low today. 💙\n\n"
  "Would you like to:\n"
  "- Take a short break?\n"
  "- Adjust your task priorities?\n"
  "- Try a breathing exercise? (coming soon)\n"
  "- Just continue as planned?\n\n"
  "Remember: It's okay to take it easy sometimes."
```

#### 7.3 View Mood Insights
```
User sends /mood OR "Show my mood trends"
  ↓
Bot calculates mood statistics:
  - Average mood this week
  - Mood trends (improving/declining)
  - Correlation with habits/tasks
  - Best/worst days
  ↓
Bot shows mood insights:
  "📊 Your Mood Insights\n\n"
  "📈 This Week:\n"
  "• Average mood: 😌 Good (3.2/5)\n"
  "• Best day: Monday 😊 (4.5/5)\n"
  "• Most common: 😌 Good (60% of entries)\n\n"
  "📉 Trends:\n"
  "• Your mood tends to be better in the mornings\n"
  "• Higher mood on days you exercise 💪\n"
  "• Slightly lower mood on Wednesdays\n\n"
  "💡 Insights:\n"
  "• You feel best when you meditate in the morning\n"
  "• Stress increases when you have >5 active tasks\n"
  "• Mood improves after completing high-priority tasks\n\n"
  "Options: [View Details] [Export Data] [Mood Journal]"
```

#### 7.4 Mood-Productivity Correlation
```
During weekly review OR when user requests insights
  ↓
Analyze correlations:
  - Mood vs task completion rate
  - Mood vs productivity levels
  - Mood vs habit adherence
  - Mood vs calendar events
  ↓
Generate personalized insights:
  "💡 Mood & Productivity Insights\n\n"
  "I've noticed some patterns:\n\n"
  "✅ You're most productive when feeling 😊 Great or 😌 Good\n"
  "  - Completion rate: 85% on good mood days\n"
  "  - vs. 60% on 😐 Okay days\n\n"
  "💧 Your mood improves when you hit your water goal\n"
  "  - Average mood: 4.2/5 after 8+ glasses\n"
  "  - vs. 3.1/5 when you miss it\n\n"
  "📅 Your mood dips before deadlines\n"
  "  - Consider breaking down tasks earlier\n"
  "  - Or schedule breaks before stressful periods\n\n"
  "Would you like personalized recommendations based on these insights?"
```

### 8. Proactive Check-ins Flow (Updated with Habits & Mood)

```
Scheduler triggers (every 30 minutes during work hours)
  ↓
Check if user is active (last_active_at within threshold)
  ↓
Get pending clarifications for user
  ↓
[Has pending clarifications] → Send clarification question
  ↓
[No clarifications] → Generate contextual check-in:
  - Get active tasks
  - Get upcoming deadlines
  - Get recent activity
  - Get calendar events for today
  ↓
AI generates personalized check-in message
  ↓
Bot sends check-in:
  "👋 Check-in
  
  You have 3 active tasks:
  • Prepare presentation (High, due tomorrow)
  • Review proposal (Medium)
  • Update docs (Low)
  
  How are you progressing? Need help prioritizing?"
  
  Options: [View Tasks] [Need Help] [I'm Good]"
```

### 7. Daily Kickoff Flow (Enhanced Morning Summary)

**Note**: This trigger fires both when the bot starts (for immediate overview) and at the user's work_start_hour (for scheduled morning summary).

```
Trigger: 
  - When bot starts (immediate summary for user)
  - OR scheduler triggers at user's work_start_hour (scheduled morning summary)
  ↓
Get user's calendar events for today
  ↓
Calculate free hours (available time slots):
  - Get all calendar events for today (from Google Calendar)
  - Sort events by start time
  - Identify gaps between events:
    * Gap from work_start_hour to first event
    * Gaps between consecutive events
    * Gap from last event to work_end_hour
  - Filter to work hours only (user.work_start_hour to user.work_end_hour)
  - Calculate duration of each free slot (in minutes)
  - Mark slots with:
    * Time range (e.g., "09:30 AM - 10:00 AM")
    * Duration (e.g., "30 minutes")
    * Time of day (morning/mid-morning/afternoon/evening)
    * Energy level (based on user patterns - if user is morning person, mark morning as high energy)
  ↓
Get all active tasks with priorities
  ↓
AI prioritization analysis:
  - Get tasks sorted by priority, deadline proximity
  - Consider task estimated duration
  - Consider task dependencies
  - Get user's productivity patterns
  ↓
Match tasks to free hours (AI-powered recommendations):
  - Get task prioritization scores (from AI prioritization)
  - For each task, find matching free slots:
    * Urgent deadline tasks → Match to earliest available slot
    * High priority tasks → Match to high-energy slots (based on user patterns)
    * Long-duration tasks → Match to largest available slots
    * Quick tasks → Match to small slots (30 min or less)
  - Consider task dependencies (blocked tasks scheduled after dependencies)
  - Consider user productivity patterns:
    * Morning person → Schedule complex tasks in morning slots
    * Afternoon person → Schedule important tasks in afternoon
  - Generate recommendations with reasoning:
    * Why this task at this time
    * What makes it optimal
    * Alternatives if slot unavailable
  ↓
Get upcoming deadlines (next 3 days)
  ↓
Get yesterday's completed tasks (if available)
  ↓
AI generates comprehensive daily summary:
  "🌅 Good Morning! Here's your day plan:
  
  📅 Today's Schedule:
  • 09:00 AM - Team Standup (30 min)
  • 10:00 AM - Client Call (1 hour)
  • 02:00 PM - Project Review (1 hour)
  
  ⏰ Free Hours Available:
  • 09:30 AM - 10:00 AM (30 min) - Morning slot
  • 11:00 AM - 12:00 PM (1 hour) - Mid-morning
  • 12:00 PM - 01:00 PM (1 hour) - Lunch break
  • 03:00 PM - 05:00 PM (2 hours) - Afternoon
  
  📋 Recommended Tasks for Today (Based on Priority & Deadlines):
  
  ⭐ HIGH PRIORITY (Recommended Now):
  1. Prepare presentation (High, due tomorrow)
     💡 Suggested: 03:00 PM - 05:00 PM (2 hours available)
     Reason: High priority + deadline tomorrow + matches your slot
  
  2. Review proposal (High, due today)
     💡 Suggested: 11:00 AM - 12:00 PM (1 hour available)
     Reason: URGENT - due today! Complete this first
  
  🟡 MEDIUM PRIORITY (When You Have Time):
  3. Update documentation (Medium, no deadline)
     💡 Can fit in: 09:30 AM - 10:00 AM (30 min slot)
  
  4. Team meeting prep (Medium)
     💡 Can fit in: 12:00 PM - 01:00 PM (lunch break slot)
  
  ⏰ Upcoming Deadlines:
  • Presentation (High) - Due: Tomorrow
  • Proposal review (High) - Due: TODAY ⚠️
  • Monthly report - Due: Dec 25 (3 days)
  
  💡 Today's Focus Strategy:
  • Start with 'Review proposal' (due today!) - Complete before lunch
  • Then tackle 'Prepare presentation' (2-hour afternoon slot)
  • Use small slots for quick tasks
  
  Ready to tackle the day? Let's go! 🚀
  
  Options: [View All Tasks] [Schedule Task] [Adjust Plan]"
```

### 8. Weekly Review Flow

```
Scheduler triggers (Sunday 10:00 AM)
  ↓
Calculate analytics for past week:
  - Tasks completed
  - Tasks overdue
  - Completion rate by pillar
  - Average task duration vs estimate
  - Productivity patterns
  ↓
AI generates weekly review:
  "📊 Weekly Review
  
  This Week's Performance:
  ✅ Completed: 15 tasks
  ⚠️ Overdue: 2 tasks
  📈 Completion Rate: 88%
  
  By Pillar:
  • Work: 8 completed (90%)
  • Education: 4 completed (100%)
  • Personal: 3 completed (75%)
  
  Insights:
  • You're most productive in the mornings
  • Work tasks are completed faster than estimated
  • Consider breaking down larger personal tasks
  
  Next Week:
  • 5 high-priority tasks
  • 3 deadlines
  
  Would you like to set goals for next week?
  
  [Set Goals] [View Details] [Skip]"
```

---

## Agent Flow

### 1. Message Processing Flow

```
Incoming Message (Telegram)
  ↓
Log message with timestamp, user_id, message_id
  ↓
Store in conversations table
  ↓
Generate embedding for message text
  ↓
Store embedding in vector store (with metadata)
  ↓
Retrieve relevant context:
  - Similar conversations (semantic search)
  - Recent tasks
  - Recent calendar events
  - User habits/patterns
  ↓
AI Intent Extraction:
  Input:
    - Current message
    - Context from memory
    - User history
  ↓
LLM processes (Gemini/GPT-4):
  - Extracts intent (structured)
  - Extracts entities (task, date, priority, etc.)
  - Determines confidence score
  ↓
Intent Result:
  {
    "intent": "add_task",
    "entities": {
      "task": "Prepare presentation",
      "priority": "high",
      "due_date": "2024-12-25"
    },
    "confidence": 0.85
  }
  ↓
[Confidence < 0.7] → Request clarification
[Confidence >= 0.7] → Proceed with action
  ↓
Route to appropriate handler
  ↓
Handler executes business logic
  ↓
Generate response using AI (if needed):
  - Personalize based on user patterns
  - Add context from memory
  - Suggest related actions
  ↓
Send response to user
  ↓
Store response in conversations
  ↓
Update user patterns/habits if applicable
```

### 2. Task Categorization Flow

```
Task title/description received
  ↓
Retrieve user context:
  - Previous tasks in same pillar
  - User habits (when they work on what)
  - Calendar events (work meetings, classes)
  ↓
AI Categorization:
  Prompt: "Categorize task into pillar based on:
    - Task: [task_description]
    - Context: [user_context]
    - History: [similar_tasks]
    
    Respond with ONLY: work, education, projects, personal, or other"
  ↓
LLM returns pillar classification
  ↓
[Uncertain] → Ask user for confirmation
[Confident] → Auto-assign pillar
  ↓
Store categorization for learning
```

### 3. Priority Determination Flow

```
Task created/updated
  ↓
Get task details:
  - Due date
  - Estimated duration
  - Dependencies
  - Pillar
  ↓
Get user context:
  - Other active tasks
  - Deadline proximity
  - User's priority patterns
  ↓
AI Priority Analysis:
  Factors:
    - Deadline urgency (time until deadline)
    - Dependency blocking (blocking other tasks?)
    - Workload balance (not too many urgent)
    - Strategic importance (pillar weight)
    - Time of day patterns (when user is productive)
  ↓
LLM calculates priority score (0-100)
  ↓
Map score to priority level:
  - 80-100: URGENT
  - 60-79: HIGH
  - 40-59: MEDIUM
  - 0-39: LOW
  ↓
Suggest priority to user
  ↓
[Auto-apply enabled] → Update task priority
[Manual confirmation] → Ask user to confirm
```

### 4. Scheduling Suggestion Flow

```
User requests to schedule task
  ↓
Get task details:
  - Estimated duration
  - Priority
  - Due date
  - Pillar
  ↓
Get calendar availability:
  - Work hours
  - Existing calendar events (next 7 days)
  - Timezone
  ↓
Find available slots:
  Algorithm:
    1. Start from now or work_start_hour
    2. Check each 30-minute slot
    3. Skip occupied slots
    4. Skip outside work hours
    5. Prefer slots before deadline
    6. Group slots by day
  ↓
Get user patterns:
  - When they typically work on this pillar
  - Energy levels by time of day
  - Preferred working times
  ↓
AI Suggestion:
  - Rank available slots by preference
  - Consider user patterns
  - Consider deadline proximity
  - Avoid back-to-back meetings
  ↓
Generate suggestions (top 3-5)
  ↓
Format message with reasoning:
  "⏰ Best time for 'Prepare presentation' (2 hours):
  
  1. Tomorrow, 10:00 AM - 12:00 PM ⭐ Recommended
     Reason: Morning slot, high energy, before deadline
  
  2. Tomorrow, 2:00 PM - 4:00 PM
     Reason: After lunch, still productive
  
  3. Wednesday, 9:00 AM - 11:00 AM
     Reason: Early morning, focused time"
```

### 5. Adaptive Learning Flow (Learn from Mistakes & Corrections)

**Core Principle**: The agent learns from every interaction, correction, and user behavior to continuously improve.

```
User corrects agent action OR agent makes mistake
  ↓
Detect correction/mistake:
  - User rejects suggestion
  - User corrects categorization
  - User changes priority
  - User reschedules task
  - User provides feedback
  - User ignores/rejects recommendations
  ↓
Analyze mistake context:
  - What was the agent's action?
  - What was the user's correction?
  - What context was present?
  - What patterns were used?
  - What was the confidence level?
  ↓
Store correction in learning_feedback table:
  - Original action
  - User correction
  - Context (tasks, time, patterns)
  - Pattern that led to mistake
  - Confidence score at time of mistake
  ↓
Identify root cause:
  - Was categorization wrong? → Update pillar associations
  - Was priority wrong? → Adjust priority weights
  - Was timing wrong? → Update scheduling preferences
  - Was intent extraction wrong? → Improve intent patterns
  - Was suggestion inappropriate? → Adjust suggestion criteria
  ↓
Update agent model:
  - Adjust categorization rules (decrease weight for wrong pillar, increase for correct)
  - Update priority weights (learn user's actual priority preferences)
  - Improve intent extraction (add correction to training context)
  - Refine scheduling preferences (learn preferred times)
  - Update suggestion criteria (avoid similar mistakes)
  ↓
Apply learning immediately:
  - Next similar situation, use learned behavior
  - Increase confidence if learning works
  - Create personalized rules for user
  - Avoid repeating same mistake
  ↓
Track learning effectiveness:
  - Monitor if corrections decrease over time
  - Track confidence improvement
  - Measure user satisfaction with suggestions
  - Adjust learning rate based on effectiveness
```

```
Agent makes suggestion/action:
  - Task categorization
  - Priority suggestion
  - Scheduling recommendation
  - Intent extraction
  ↓
User responds:
  - Accepts suggestion ✅
  - Rejects suggestion ❌
  - Corrects suggestion 🔧
  - Ignores suggestion (implicit rejection)
  ↓
Store feedback:
  - Action taken: what agent suggested
  - User response: accept/reject/correct/ignore
  - Context: time, tasks, patterns
  - Confidence before action
  ↓
Analyze feedback:
  [User accepts] →
    - Increase confidence in this pattern
    - Apply more often in similar contexts
    - Strengthen pattern association
  
  [User rejects/corrects] →
    - Decrease confidence
    - Store correction as learning
    - Update behavior model
    - Ask for confirmation next time
  
  [User ignores] →
    - Moderate confidence decrease
    - Try different approach next time
  ↓
Update agent model:
  - Adjust categorization rules
  - Update priority weights
  - Improve intent extraction
  - Refine scheduling preferences
  ↓
Apply learning:
  - Next similar situation, use learned behavior
  - Increase confidence if learning works
  - Create personalized rules for user
```

### 6. Automatic Flow Creation Flow (Behavior-Based Automation)

```
Agent continuously monitors user behavior over time:
  - Task creation patterns (what, when, how often)
  - Scheduling patterns (preferred times, durations)
  - Habit patterns (daily routines, weekly patterns)
  - Calendar patterns (recurring events, busy periods)
  - Task sequences (Task A → Task B → Task C)
  - Response patterns (when user is most active)
  ↓
Pattern Detection (Real-time + Periodic Analysis):
  After 2-3 occurrences, detect pattern:
  Example: "Weekly team meeting" created every Monday at 9 AM
  Example: Task "Review code" always followed by "Deploy to staging"
  Example: User always schedules high-priority tasks at 2 PM
  Example: User creates "Daily standup" every weekday
  Example: User logs water habit at same times daily
  ↓
Calculate Pattern Strength:
  - Frequency (how many times observed)
  - Consistency (same time/pattern/sequence)
  - Confidence score (0-1, based on variance)
  - User acceptance rate (if suggested before)
  - Time since first occurrence
  - Pattern stability (increasing or decreasing)
  ↓
[Pattern strength > threshold (e.g., 0.7)] → Suggest automatic flow:
  "🔍 I noticed a pattern in your behavior!
  
  Pattern: Weekly Team Meeting
  • Created every Monday
  • Scheduled for 10:00 AM - 11:00 AM
  • Priority: High
  • Pillar: Work
  
  Detected: 3 times in last 3 weeks (100% consistency)
  Confidence: High (0.85)
  
  Would you like me to create an automatic flow?
  
  When triggered (every Monday):
  ✅ Auto-create task: 'Weekly Team Meeting'
  ✅ Auto-schedule: 10:00 AM - 11:00 AM
  ✅ Auto-set priority: High
  ✅ Auto-categorize: Work
  
  You'll still get a confirmation before each execution.
  
  [✅ Yes, Create Flow] [✏️ Edit Flow] [⏭️ Skip] [🚫 Never Suggest]"
  ↓
[User confirms] → Create flow template:
  - Store flow definition in database (Flow model)
  - Set trigger conditions:
    * Time-based: "Every Monday at 9:00 AM"
    * Event-based: "When Task X is completed"
    * Pattern-based: "When user creates task matching pattern"
  - Store actions to perform:
    * Create task with specific properties
    * Schedule at specific time
    * Set priority/category
    * Create task sequence
  - Set confirmation requirement (always ask before executing)
  - Set learning flag (learn from user modifications)
  ↓
Flow execution (when triggered):
  - Check if flow should execute (conditions met)
  - Show preview: "I'm about to create 'Weekly Team Meeting' for today. Proceed?"
  - Ask for confirmation (always required)
  - [User confirms] → Execute flow actions
  - [User modifies] → Learn from edits:
    * If user changes time → Update flow's scheduled time
    * If user changes priority → Update flow's priority
    * If user skips → Don't update flow (one-time skip)
    * If user cancels → Decrease flow confidence
  - Update flow if user consistently modifies
  ↓
Flow Evolution:
  - Track flow execution success rate
  - Track user modifications to flow outputs
  - If user modifies >50% of executions → Suggest flow update
  - If user skips >3 times → Suggest disabling flow
  - Learn optimal timing/preferences from modifications
```

#### 6.1 Types of Automatic Flows

**1. Recurring Task Flows:**
- Weekly meetings
- Daily standups
- Monthly reviews
- Recurring habits

**2. Task Sequence Flows:**
- Task A → Task B → Task C (always in order)
- After completing X, always create Y
- Before deadline, always do preparation task

**3. Scheduling Flows:**
- Auto-schedule high-priority tasks at preferred time
- Auto-schedule tasks before deadlines
- Auto-schedule based on user's productive hours

**4. Categorization Flows:**
- Tasks with keyword X → Always category Y
- Tasks created at time T → Usually category C
- Learn user's categorization patterns

**5. Priority Flows:**
- Tasks with deadline < 1 day → Auto-high priority
- Tasks from pillar "Work" → Usually high priority
- Learn user's priority patterns

### 7. Behavior-Based Adaptation Flow (Daily Behavior Learning)

```
Agent continuously monitors user behavior in real-time:
  ↓
Daily Pattern Analysis (Updated Daily):
  - Active hours: 9-11 AM, 2-4 PM (when user responds)
  - Task completion times: mostly mornings (learn optimal times)
  - Response times: faster in afternoon (adapt check-in timing)
  - Scheduling preferences: 2 hours before deadline (learn buffer time)
  - Peak productivity times (when most tasks completed)
  - Energy patterns (morning person vs afternoon person)
  - Task creation patterns (when user creates tasks)
  ↓
Weekly Pattern Analysis (Updated Weekly):
  - Most productive days: Monday, Tuesday
  - Busy days: Wednesday, Thursday
  - Light days: Friday
  - Weekend patterns: minimal work activity
  - Day-specific preferences (e.g., Monday = planning day)
  - Weekly task distribution patterns
  ↓
Task Pattern Analysis (Continuous):
  - Average duration per pillar (learn realistic estimates)
  - Completion rate by time of day (when user actually completes tasks)
  - Priority patterns (user's actual priorities vs AI suggestions)
  - Scheduling patterns (preferred times, learn from rejections)
  - Task categorization accuracy by pillar (learn from corrections)
  - Task naming patterns (learn user's terminology)
  ↓
Calendar Pattern Analysis (Continuous):
  - Busy periods vs free periods (learn availability)
  - Preferred meeting times (learn when user accepts meetings)
  - Typical schedule structure (learn daily rhythm)
  - Recurring events patterns (detect routines)
  - Free time patterns (when user has most free time)
  ↓
Habit Pattern Analysis (Continuous):
  - Habit completion times (when user actually logs habits)
  - Habit success rates (which habits user maintains)
  - Habit-tasking correlations (habits that affect productivity)
  - Habit-mood correlations (habits that improve mood)
  ↓
Mood Pattern Analysis (If Enabled):
  - Mood by time of day
  - Mood by day of week
  - Mood-task completion correlation
  - Mood-productivity correlation
  - Mood-habit correlation
  ↓
Adapt Agent Behavior Based on Patterns (Real-time Adaptation):
  - **Check-in Timing**: Adjust to user's active hours
    * If user responds at 9 AM → Send check-ins around 9 AM
    * If user ignores morning check-ins → Move to afternoon
  - **Suggestion Timing**: When user most responsive
    * Learn best times to send suggestions
    * Avoid sending during busy periods
  - **Priority Suggestions**: Match user's actual priorities
    * If user always changes High → Medium → Learn user prefers Medium
    * If user accepts High suggestions → Increase confidence
  - **Scheduling Suggestions**: Preferred times
    * If user always reschedules to 2 PM → Learn 2 PM preference
    * If user rejects morning slots → Avoid morning suggestions
  - **Categorization**: Learn user's actual categories
    * If user always changes "Work" → "Projects" → Learn correction
    * Build user-specific categorization model
  - **Language Style**: Personalize communication
    * Formal vs casual (learn from user responses)
    * Emoji usage (learn user preferences)
    * Message length (learn if user prefers short/long messages)
  - **Task Recommendations**: Adapt to user behavior
    * Recommend tasks at times user typically works on them
    * Suggest tasks user is likely to accept
    * Avoid suggesting tasks user always rejects
  - **Flow Creation**: Suggest flows based on strong patterns
    * Detect recurring patterns automatically
    * Suggest automation for high-confidence patterns
  ↓
Continuous Learning Loop:
  - Every interaction → Update patterns
  - Every correction → Adjust model
  - Every acceptance → Increase confidence
  - Every rejection → Learn what not to do
  - Periodic review → Consolidate learnings
  - Long-term trends → Adapt to life changes
  - Adapt categorization rules (learn from corrections)
  ↓
Create Personalized Workflows (Automatic):
  - Morning routine: check-in at 9 AM, suggest high-priority tasks
  - Afternoon routine: review progress, suggest afternoon tasks
  - Evening routine: plan next day, schedule tomorrow's tasks
  - Weekly routine: suggest weekly planning on Monday morning
  - Deadline routine: auto-suggest scheduling 2 days before deadline
  ↓
Self-Improvement Mechanisms:
  - **Mistake Tracking**: Log all corrections and mistakes
  - **Pattern Recognition**: Identify what works vs what doesn't
  - **Confidence Calibration**: Adjust confidence based on accuracy
  - **A/B Testing**: Try different approaches, learn which works
  - **Feedback Loop**: Every interaction improves future interactions
  - **Adaptive Thresholds**: Adjust suggestion thresholds based on acceptance rate
  ↓
Continuous Refinement:
  - Monitor if adaptations improve user experience
  - Adjust adaptation parameters
  - Learn what adaptations work best
  - Evolve with user's changing behavior
  - Self-correct when patterns change
  - Adapt to user's life changes (new job, schedule changes, etc.)
```

#### 8.2 Self-Improvement Examples

**Example 1: Learning from Categorization Mistakes**
```
Agent suggests: Task "Code review" → Category: "Work"
User corrects: "Code review" → Category: "Projects"
  ↓
Agent learns:
  - "Code review" tasks → Usually "Projects" not "Work"
  - User's "Projects" category includes development work
  - Update categorization model
  ↓
Next time: Agent suggests "Projects" for similar tasks
  ↓
If user accepts → Increase confidence
If user corrects again → Learn more specific pattern
```

**Example 2: Learning from Scheduling Rejections**
```
Agent suggests: Schedule task at 9:00 AM
User rejects and reschedules to 2:00 PM
  ↓
Agent learns:
  - User prefers afternoon scheduling
  - 9 AM is not optimal for this user
  - Update scheduling preferences
  ↓
Next time: Agent suggests 2:00 PM for similar tasks
  ↓
If user accepts → Learn this is preferred time
If user changes again → Learn more specific preference
```

**Example 3: Learning from Priority Corrections**
```
Agent suggests: Priority "High"
User changes to "Medium"
  ↓
Agent learns:
  - User's "High" threshold is different
  - This type of task is usually "Medium" for user
  - Update priority weights
  ↓
Next time: Agent suggests "Medium" for similar tasks
  ↓
Track: If user accepts → Increase confidence
```

**Example 4: Automatic Flow Creation from Patterns**
```
User creates "Weekly standup" every Monday at 9 AM (3 weeks in a row)
  ↓
Agent detects pattern:
  - Frequency: 3/3 weeks (100%)
  - Consistency: Same day, same time
  - Confidence: High (0.9)
  ↓
Agent suggests automatic flow:
  "I noticed you create 'Weekly standup' every Monday at 9 AM.
   Would you like me to auto-create this every week?"
  ↓
User confirms → Flow created
  ↓
Every Monday: Agent asks "Create Weekly standup for today?" (with confirmation)
  ↓
User accepts → Flow works well
User modifies → Learn from modifications, update flow
```

**Example 5: Adapting Check-in Timing**
```
Agent sends check-ins at 9 AM, 12 PM, 3 PM
User responds at: 10 AM, 2 PM, 4 PM (always 1 hour after)
  ↓
Agent learns:
  - User is active 1 hour after suggested times
  - Adjust check-in times to match user's rhythm
  ↓
Next week: Agent sends check-ins at 10 AM, 1 PM, 4 PM
  ↓
If user responds faster → Timing improved
If still delayed → Continue adjusting
```

#### 8.3 Adaptive Confidence System

```
Agent makes suggestion with confidence score
  ↓
Track outcome:
  - User accepts → Increase confidence
  - User rejects → Decrease confidence
  - User corrects → Moderate decrease, learn correction
  ↓
Adjust confidence thresholds:
  - High confidence (>0.8) → Can auto-apply (with confirmation)
  - Medium confidence (0.5-0.8) → Always ask
  - Low confidence (<0.5) → Ask with alternatives
  ↓
Learn from confidence accuracy:
  - If high confidence wrong → Lower threshold
  - If low confidence right → Increase threshold
  - Calibrate confidence scores over time
```

### 5. Context Retrieval Flow

```
User sends message
  ↓
Generate embedding for current message
  ↓
Semantic Search in Vector Store:
  Query: Current message embedding
  Filters:
    - User ID
    - Time range (last 30 days)
    - Conversation type
  ↓
Retrieve top K similar conversations (K=5-10)
  ↓
Get structured data:
  - Recent tasks (last 7 days)
  - Upcoming calendar events (next 7 days)
  - User habits/patterns
  - Pending clarifications
  ↓
Format context for AI:
  {
    "similar_conversations": [...],
    "recent_tasks": [...],
    "upcoming_events": [...],
    "user_patterns": {...},
    "clarifications": [...]
  }
  ↓
Pass context to LLM in prompt
  ↓
LLM uses context to generate personalized response
```

### 8. Self-Improvement & Adaptive Mechanisms

#### 8.1 Learning from Mistakes & Corrections (Real-time)

```
User corrects agent action OR agent makes mistake:
  - Wrong task categorization
  - Incorrect priority suggestion
  - Misunderstood intent
  - Wrong scheduling suggestion
  - Inappropriate time recommendation
  ↓
Bot detects correction/mistake:
  - User explicitly corrects (e.g., "No, this is actually 'work', not 'education'")
  - User rejects suggestion multiple times
  - User manually changes agent's action
  ↓
Store mistake/feedback:
  - What the agent did wrong
  - What the user corrected it to
  - Context of the mistake
  - Confidence level before mistake
  ↓
Analyze mistake pattern:
  - Similar mistakes repeated?
  - Pattern in corrections (e.g., always categorizing X as Y incorrectly)
  - Context where mistakes occur
  ↓
Update agent behavior:
  - Adjust categorization rules for this user
  - Update priority weighting
  - Improve intent extraction for this user
  - Adjust scheduling preferences
  ↓
Reduce confidence in similar cases:
  - Ask for confirmation more often when uncertain
  - Flag patterns where mistakes occurred
  ↓
Apply learned correction:
  - Next time similar situation occurs, use corrected behavior
  - Increase confidence if correction works
```

#### 6.2 Pattern Recognition for Automatic Flow Creation

```
Agent observes repeated user behavior:
  Example: User always schedules "Weekly team meeting" every Monday at 10 AM
  Example: User always adds "Review documents" task before important meetings
  Example: User always logs water intake after lunch
  ↓
Pattern Detection:
  - Analyze task creation patterns (same task repeated)
  - Analyze scheduling patterns (same time slot used)
  - Analyze task sequences (tasks always created in order)
  - Analyze habit patterns (actions at same times/days)
  ↓
Identify Flow Patterns:
  Pattern 1: Recurring Task Flow
    - Task "X" created every Monday
    - Same pillar, priority, duration
    → Suggest creating recurring task
  
  Pattern 2: Task Sequence Flow
    - Task "A" always followed by Task "B"
    - B depends on A being completed
    → Suggest creating task template/sequence
  
  Pattern 3: Scheduling Flow
    - Similar tasks always scheduled at same time
    - Same day of week pattern
    → Suggest automatic scheduling
  
  Pattern 4: Daily Routine Flow
    - User logs habits at same times daily
    - Same sequence of actions
    → Suggest routine automation
  ↓
Create Automatic Flow:
  "🔍 I noticed a pattern!
  
  You've been creating 'Weekly team meeting' task every Monday
  and scheduling it for 10:00 AM - 11:00 AM.
  
  Would you like me to:
  • Create a recurring task template?
  • Auto-schedule this every Monday?
  • Set up a reminder flow?
  
  [Create Recurring Task] [Set Up Flow] [Skip]"
  ↓
[User confirms] → Create automatic flow:
  - Store flow pattern in database
  - Automatically apply when pattern detected
  - Ask for confirmation before auto-applying
```

#### 6.3 Behavior-Based Adaptation Flow

```
Agent continuously monitors user behavior:
  Daily patterns:
    - When user is most active
    - When user completes most tasks
    - When user checks in
    - When user responds to messages
  ↓
Weekly patterns:
    - Which days are most productive
    - Which days user creates most tasks
    - Which days user completes tasks
    - Weekly routines
  ↓
Task patterns:
    - Average task duration per pillar
    - Completion rate by time of day
    - Priority patterns (how user prioritizes)
    - Scheduling preferences
  ↓
Calendar patterns:
    - Busy vs free days
    - Preferred meeting times
    - Typical schedule structure
  ↓
Adapt agent behavior:
  - Adjust check-in times based on user activity
  - Adjust suggestion timing (e.g., suggest tasks when user is most active)
  - Adapt priority suggestions to match user's actual priorities
  - Adjust scheduling suggestions to user's preferred times
  - Personalize language/style based on user responses
  ↓
Create personalized workflows:
  - Morning routine automation
  - Daily planning workflow
  - Task review workflow
  - Evening wrap-up workflow
```

#### 6.4 Automatic Flow Execution

```
Pattern detected → Automatic flow created
  ↓
Flow triggers based on conditions:
  - Time-based (every Monday at 9 AM)
  - Event-based (when user logs in morning)
  - Task-based (when similar task created)
  - Sequence-based (after task A completed)
  ↓
Before executing automatic flow:
  Bot asks for confirmation:
  "🤖 I noticed it's Monday morning. Would you like me to:
  
  • Create 'Weekly team meeting' task
  • Schedule it for 10:00 AM - 11:00 AM
  • Set priority to High
  
  This is based on your pattern. Continue?
  
  [✅ Yes, Do It] [Edit First] [Skip This Time] [Disable Flow]"
  ↓
[User confirms] → Execute flow automatically:
  - Create tasks
  - Schedule events
  - Set reminders
  - Link dependencies
  ↓
[User edits] → Apply edits → Save updated flow pattern
[User skips] → Skip this time, keep flow active
[User disables] → Disable flow, ask why (for learning)
```

#### 6.5 Continuous Learning & Improvement

```
Every interaction contributes to learning:
  ↓
Track metrics:
  - Suggestion acceptance rate
  - Correction frequency
  - User satisfaction (implicit/explicit)
  - Task completion patterns
  - Scheduling accuracy
  ↓
Weekly pattern analysis:
  - What patterns are strengthening?
  - What patterns are weakening?
  - New patterns emerging?
  - Old patterns breaking?
  ↓
Update agent models:
  - Improve categorization accuracy
  - Refine priority suggestions
  - Better intent extraction
  - More accurate scheduling
  ↓
Adaptive behavior:
  - Increase automation for patterns with high acceptance
  - Ask more questions for uncertain patterns
  - Adjust to user's evolving preferences
  - Learn from successful vs failed suggestions
```

#### 6.6 Learning from Feedback Loop

```
User provides explicit feedback:
  - "That was helpful!" (positive)
  - "No, that's wrong" (negative)
  - "I don't like this suggestion" (negative)
  - Ignores suggestion (implicit negative)
  ↓
Store feedback with context:
  - What was suggested
  - User's response
  - Context (time, day, tasks, etc.)
  - Feedback type (explicit/implicit)
  ↓
Update behavior:
  Positive feedback:
    - Increase confidence in this pattern
    - Apply more often
    - Suggest similar actions
  
  Negative feedback:
    - Decrease confidence
    - Ask for confirmation next time
    - Try alternative approaches
    - Learn what user doesn't like
  ↓
Pattern refinement:
  - Adjust thresholds based on feedback
  - Update weights for different factors
  - Improve personalization
```

---

## Edge Cases

### 1. User Registration Edge Cases

#### 1.1 Duplicate Telegram ID
- **Scenario**: User already exists with same telegram_id
- **Action**: Return existing user, skip creation
- **Handler**: Check before insert, use existing record

#### 1.2 Missing User Data
- **Scenario**: Telegram user object missing first_name
- **Action**: Use username or "User" as fallback
- **Handler**: Validate required fields, use defaults

#### 1.3 Onboarding Interrupted
- **Scenario**: User starts onboarding but doesn't complete
- **Action**: Store partial progress, allow resume
- **Handler**: Check is_onboarded flag, show resume option

#### 1.4 Custom Pillar Edge Cases
- **Scenario**: User tries to add duplicate custom pillar
  - **Action**: Detect duplicate (case-insensitive), show warning: "You already have 'Fitness' category. Use that instead?"
  - **Handler**: Check existing pillars before adding, normalize for comparison

- **Scenario**: User creates custom pillar with very long name
  - **Action**: Truncate to max 50 characters, or request shorter name
  - **Handler**: Validate length, provide feedback

- **Scenario**: User tries to add empty or whitespace-only pillar name
  - **Action**: Reject, ask for valid name
  - **Handler**: Validate non-empty, trimmed name

- **Scenario**: User tries to add custom pillar with special characters
  - **Action**: Sanitize or allow (depending on requirements), inform user
  - **Handler**: Validate format, allow alphanumeric + spaces/dashes/underscores

- **Scenario**: User deletes custom pillar that has active tasks
  - **Action**: Warn user, offer to:
    - Reassign tasks to another pillar
    - Keep pillar until tasks are moved
    - Delete tasks (with confirmation)
  - **Handler**: Check task count, provide migration options

- **Scenario**: User has too many custom pillars (e.g., 20+)
  - **Action**: Suggest consolidating or limit max pillars per user
  - **Handler**: Set reasonable limit (e.g., 10 custom + 5 predefined = 15 max), warn when approaching limit

### 2. Task Management Edge Cases

#### 2.1 Duplicate Tasks
- **Scenario**: User creates same task twice
- **Detection**: Check for similar task titles (semantic similarity)
- **Action**: Show warning: "Similar task exists: [task]. Still create?"
- **Handler**: Compare embeddings, suggest merge or cancel

#### 2.2 Invalid Dates
- **Scenario**: User enters impossible date (e.g., Feb 30)
- **Action**: Validate date parsing, ask for clarification
- **Handler**: Try multiple date formats, catch parsing errors

#### 2.3 Task Dependencies Cycle
- **Scenario**: Task A depends on B, B depends on A
- **Detection**: Check dependency graph for cycles
- **Action**: Reject dependency, show error message
- **Handler**: Build dependency graph, detect cycles

#### 2.4 Task Updates After Completion
- **Scenario**: User tries to edit completed task
- **Action**: Show warning or allow "reopen"
- **Handler**: Check status, offer reopen option

#### 2.5 Very Long Task Titles
- **Scenario**: User enters 500-character task title
- **Action**: Truncate or request shorter title
- **Handler**: Validate length (max 200 chars), prompt truncation

### 3. Calendar Edge Cases

#### 3.1 OAuth Token Expired
- **Scenario**: Google token expired, calendar request fails
- **Detection**: Check token expiry, catch 401 errors
- **Action**: Refresh token automatically or request re-authorization
- **Handler**: Token refresh flow, fallback to re-auth

#### 3.2 Calendar API Rate Limit
- **Scenario**: Too many calendar requests, rate limited
- **Detection**: Catch 429 errors
- **Action**: Queue request, retry after delay, inform user
- **Handler**: Exponential backoff, request queue

#### 3.3 Calendar Sync Conflict
- **Scenario**: Event deleted on Google Calendar but task still has calendar_event_id
- **Detection**: Compare events during sync
- **Action**: Clear task's calendar_event_id, notify user, ask if task should be rescheduled
- **Handler**: Sync reconciliation logic

#### 3.4 Task-Calendar Sync Conflicts
- **Scenario**: Task scheduled time doesn't match calendar event time
  - **Detection**: Compare task.scheduled_start with calendar event start_time
  - **Action**: Notify user of mismatch, offer to:
    - Update calendar to match task (with confirmation)
    - Update task to match calendar (with confirmation)
    - Keep both (if intentional)
  - **Handler**: Sync comparison logic, user confirmation required

- **Scenario**: Task due_date passed but calendar event still scheduled for future
  - **Detection**: Check if due_date < now AND scheduled_end > now
  - **Action**: Warn user, suggest rescheduling task or updating due date (with confirmation)
  - **Handler**: Deadline validation during sync

- **Scenario**: Calendar event updated externally but task not updated
  - **Detection**: Compare last_synced_at with event updated_at
  - **Action**: Notify user of change, ask for confirmation to update task
  - **Handler**: Periodic sync, always require confirmation for updates

- **Scenario**: Task deleted but calendar event still exists
  - **Detection**: Task with calendar_event_id no longer exists
  - **Action**: Ask user if calendar event should be deleted (with confirmation):
    - Yes → Delete calendar event
    - No → Unlink event, keep on calendar
  - **Handler**: Sync cleanup logic, user confirmation required

- **Scenario**: Multiple tasks scheduled for same time slot
  - **Detection**: Check for overlapping scheduled_start/scheduled_end times
  - **Action**: Warn user of conflict, suggest rescheduling one task (with confirmation)
  - **Handler**: Conflict detection before scheduling

- **Scenario**: Task scheduled without user confirmation
  - **Action**: Always require confirmation before creating/modifying calendar events
  - **Handler**: Prevent auto-scheduling without user approval

- **Scenario**: Sync fails during scheduled operation
  - **Action**: Rollback changes, notify user, retry or ask to reschedule
  - **Handler**: Transaction management, error recovery

#### 3.5 Timezone Mismatches
- **Scenario**: Calendar event in different timezone than user
- **Action**: Convert to user's timezone for display
- **Handler**: Use pytz for timezone conversion

### 4. Natural Language Processing Edge Cases

#### 4.1 Ambiguous Intent
- **Scenario**: Message could be multiple intents (low confidence)
- **Detection**: Confidence score < 0.7
- **Action**: Ask clarifying question
- **Handler**: Generate clarification prompts

#### 4.2 No Intent Detected
- **Scenario**: AI can't extract clear intent
- **Action**: Default to general_chat, provide helpful response
- **Handler**: Fallback intent classification

#### 4.3 Non-English Messages
- **Scenario**: User sends message in different language
- **Action**: Detect language, handle if supported, else inform user
- **Handler**: Language detection, multi-language support (future)

#### 4.4 Empty/Whitespace Messages
- **Scenario**: User sends empty message or only spaces
- **Action**: Ignore or ask "What did you want to say?"
- **Handler**: Validate message content before processing

### 5. Scheduling Edge Cases

#### 5.1 No Available Time Slots
- **Scenario**: Calendar fully booked, no time for task
- **Action**: Show message: "No available slots. Consider:
  - Rescheduling existing events
  - Working outside work hours
  - Breaking task into smaller pieces"
- **Handler**: Check all slots, provide alternatives

#### 5.2 Task Duration Exceeds Available Slots
- **Scenario**: Task needs 4 hours, max slot is 2 hours
- **Action**: Suggest splitting task or scheduling across days
- **Handler**: Check slot sizes, suggest splitting

#### 5.3 Deadline Before Available Slot
- **Scenario**: Task due tomorrow but earliest slot is next week
- **Action**: Warn user, suggest:
  - Extend deadline
  - Work outside hours
  - Mark as urgent
- **Handler**: Compare deadline with slots

### 6. Database Edge Cases

#### 6.1 Database Connection Lost
- **Scenario**: PostgreSQL connection fails
- **Action**: Retry with exponential backoff, inform user if persistent
- **Handler**: Connection pool, retry logic, health checks

#### 6.2 Concurrent Updates
- **Scenario**: Multiple requests update same task simultaneously
- **Action**: Use database transactions, optimistic locking
- **Handler**: SQLAlchemy sessions, version fields

#### 6.3 Large Result Sets
- **Scenario**: User has 1000+ tasks, query times out
- **Action**: Paginate results, limit query size
- **Handler**: Pagination, LIMIT clauses

### 7. AI/LLM Edge Cases

#### 7.1 LLM API Failure
- **Scenario**: Gemini API down, OpenAI also fails
- **Action**: Fallback to rule-based responses, cache recent responses
- **Handler**: Retry logic, fallback LLM, graceful degradation

#### 7.2 LLM Rate Limiting
- **Scenario**: Too many AI requests, rate limited
- **Action**: Queue requests, process with delay
- **Handler**: Request queue, rate limiting logic

#### 7.3 Invalid LLM Response
- **Scenario**: LLM returns malformed JSON or invalid data
- **Action**: Parse carefully, validate, retry if possible
- **Handler**: JSON parsing with error handling, validation

#### 7.4 Context Too Large
- **Scenario**: User history too large for LLM context window
- **Action**: Summarize context, prioritize recent/relevant
- **Handler**: Context summarization, truncation logic

### 8. User Interaction Edge Cases

#### 8.1 User Inactivity
- **Scenario**: User hasn't responded in days
- **Action**: Send gentle check-in, ask if still active
- **Handler**: Inactivity detection, re-engagement messages

#### 8.2 Rapid Message Spam
- **Scenario**: User sends 10 messages in 5 seconds
- **Action**: Queue messages, process sequentially, rate limit
- **Handler**: Message queue, rate limiting per user

#### 8.3 User Deletes Message
- **Scenario**: User deletes message after bot processed it
- **Action**: Handle gracefully, don't crash
- **Handler**: Check message existence before replying

#### 8.4 Blocked Bot
- **Scenario**: User blocks bot
- **Detection**: Telegram API returns "bot blocked" error
- **Action**: Mark user as inactive, stop sending messages
- **Handler**: Catch block errors, update user status

### 9. Adaptive Learning Edge Cases

#### 9.1 Over-Learning from Single Correction
- **Scenario**: Agent learns too aggressively from one correction
- **Detection**: Track if single correction changes behavior too much
- **Action**: Use weighted learning (multiple corrections needed for major changes)
- **Handler**: Learning rate adjustment, require multiple confirmations for major changes

#### 9.2 Conflicting Patterns
- **Scenario**: User behavior changes, old patterns conflict with new patterns
- **Detection**: Compare recent patterns vs historical patterns
- **Action**: Detect pattern shift, ask user if behavior changed, adapt gradually
- **Handler**: Pattern comparison, gradual adaptation, user confirmation for major shifts

#### 9.3 False Pattern Detection
- **Scenario**: Agent detects pattern that's actually coincidence
- **Detection**: Low confidence pattern suggested as flow
- **Action**: Require high confidence (>0.8) before suggesting flows, allow user to reject
- **Handler**: Pattern validation, confidence thresholds, user feedback

#### 9.4 Flow Execution Failure
- **Scenario**: Automatic flow executes but user rejects result
- **Detection**: User modifies or cancels flow output
- **Action**: Learn from rejection, decrease flow confidence, ask if flow should be updated
- **Handler**: Track flow success rate, adapt or disable failing flows

#### 9.5 Learning Feedback Loop
- **Scenario**: Agent learns wrong thing, makes more mistakes, learns more wrong things
- **Detection**: Track mistake rate over time, detect increasing errors
- **Action**: Reset learning for specific pattern, ask user for explicit guidance
- **Handler**: Learning validation, mistake rate monitoring, reset mechanisms

#### 9.6 Pattern Drift
- **Scenario**: User's behavior changes gradually, agent doesn't adapt
- **Detection**: Compare recent patterns vs old patterns, detect drift
- **Action**: Gradually update patterns, weight recent behavior more heavily
- **Handler**: Time-weighted pattern analysis, gradual adaptation

### 10. Error Recovery Edge Cases

#### 10.1 Partial Task Creation
- **Scenario**: Task created in DB but calendar event creation fails
- **Action**: Rollback or mark task as "needs scheduling"
- **Handler**: Transaction management, compensation logic

#### 9.2 Message Send Failure
- **Scenario**: Can't send message to user (blocked, network error)
- **Action**: Log error, retry later, don't crash bot
- **Handler**: Error handling, retry queue

#### 9.3 State Inconsistency
- **Scenario**: User state doesn't match database
- **Action**: Rebuild state from database, reset if needed
- **Handler**: State validation, recovery logic

---

## Menu Options & Sub-Options

### Main Menu Commands

#### 1. `/start`
- **Purpose**: Start bot or restart onboarding
- **Sub-options**: None (triggers onboarding or welcome)

#### 2. `/help`
- **Purpose**: Show available commands and usage
- **Sub-options**: None (static help text)

#### 3. `/tasks`
- **Purpose**: View and manage tasks
- **Sub-options**:
  - View All Tasks
  - View by Pillar (Work/Education/Projects/Personal/Other)
  - View by Priority (High/Medium/Low)
  - View by Status (Pending/In Progress/Completed)
  - View by Due Date (Today/Tomorrow/This Week/Overdue/No Due Date)
  - Add New Task
  - Search Tasks
  - Sort Options (Priority/Due Date/Created Date)
  - Task Statistics

#### 4. `/calendar`
- **Purpose**: View and manage calendar
- **Sub-options**:
  - View Today's Events
  - View This Week's Events
  - View This Month's Events
  - Connect/Disconnect Google Calendar
  - Sync Calendar Now
  - Schedule Task on Calendar
  - View Conflicts
  - Calendar Settings

#### 5. `/settings`
- **Purpose**: Configure bot settings
- **Sub-options**:
  - Edit Work Hours
  - Change Timezone
  - Check-in Settings (interval, on/off)
  - Manage Pillars (add/remove)
  - Calendar Settings
  - Notification Settings
  - Privacy Settings (data deletion)
  - AI Preferences (auto-categorization, auto-priority)
  - Reset/Delete Account

#### 6. `/prioritize`
- **Purpose**: AI-powered task prioritization
- **Sub-options**:
  - Auto-prioritize All Tasks
  - Prioritize by Pillar
  - View Priority Suggestions
  - Apply Suggestions
  - Custom Priority Rules

#### 7. `/stats` or `/analytics`
- **Purpose**: View productivity statistics
- **Sub-options**:
  - Today's Stats
  - This Week's Stats
  - This Month's Stats
  - By Pillar Statistics
  - Completion Rate
  - Time Tracking
  - Productivity Trends

### Inline Keyboard Options

#### Task Action Menu (per task)
- Complete Task
- Edit Task
  - Change Title
  - Change Priority
  - Change Due Date
  - Change Status
  - Change Pillar
  - Add Description
- Schedule on Calendar
- Set Reminder
- Add Dependency
- Delete Task

#### Confirmation Menus
- Yes/No
- Confirm/Cancel
- Accept/Reject

#### Pillar Selection Menu
- Work
- Education
- Projects
- Personal
- Other
- Done (finish selection)

#### Priority Selection Menu
- Urgent (🔴)
- High (🟠)
- Medium (🟡)
- Low (🟢)

#### Settings Navigation Menu
- Back to Main Menu
- Save Changes
- Cancel Changes
- Reset to Default

### Natural Language Triggers

Users can also use natural language to access features:

- **Task Creation**:
  - "Add task: [description]"
  - "Create task: [description]"
  - "New task: [description]"
  - "I need to [description]"

- **Task Viewing**:
  - "Show my tasks"
  - "What tasks do I have?"
  - "List tasks"
  - "What's on my plate?"

- **Task Updates**:
  - "Update task: [name/id]"
  - "Change task: [name/id]"
  - "Edit task: [name/id]"
  - "Mark [name/id] as complete"

- **Calendar Queries**:
  - "What's on my calendar?"
  - "Show calendar"
  - "What do I have today?"
  - "When is my next meeting?"

- **Scheduling**:
  - "Schedule [task]"
  - "When should I do [task]?"
  - "Find time for [task]"

---

## Operations

### CRUD Operations

#### User Operations
- **Create**: Register new user
- **Read**: Get user profile, settings
- **Update**: Update settings, work hours, timezone
- **Delete**: Delete account (soft delete)

#### Task Operations
- **Create**: Add new task with metadata
- **Read**: List tasks (with filters, sorting, pagination)
- **Update**: Modify task properties
- **Delete**: Remove task (soft delete: mark as CANCELLED)

#### Calendar Event Operations
- **Create**: Add event to Google Calendar (with user confirmation)
- **Read**: Fetch events from Google Calendar
- **Update**: Modify calendar event (with user confirmation)
- **Delete**: Remove calendar event (with user confirmation)
- **Sync**: Bidirectional sync with Google Calendar (automatic + on-demand)
  - Task → Calendar sync (when tasks change)
  - Calendar → Task sync (when events change externally)
  - Based on due dates and preparation time

#### Conversation Operations
- **Create**: Store user/bot messages
- **Read**: Retrieve conversation history (with semantic search)
- **Update**: N/A (conversations are immutable)
- **Delete**: Delete old conversations (privacy)

### Business Logic Operations

#### Task Management
- **Prioritize**: AI-powered priority assignment
- **Categorize**: Auto-categorize into pillars
- **Schedule**: Find time slots and create calendar events
- **Remind**: Set reminders based on deadlines
- **Track**: Monitor task completion, time tracking
- **Dependency Management**: Handle task dependencies
- **Bulk Operations**: Complete multiple tasks, batch updates

#### Calendar Management
- **Availability Check**: Find available time slots
- **Conflict Detection**: Detect scheduling conflicts
- **Time Suggestion**: AI-suggested optimal times
- **Sync**: Bidirectional sync with Google Calendar
  - **Task → Calendar**: Sync when tasks created/updated/deleted
  - **Calendar → Task**: Sync when events changed externally
  - **Due Date Sync**: Auto-schedule tasks based on due dates and prep time
  - **Periodic Sync**: Every 4 hours + on-demand
  - **Always Confirm**: User confirmation required for all sync operations
- **Timezone Conversion**: Convert between timezones

#### AI/ML Operations
- **Intent Extraction**: Understand user messages
- **Entity Extraction**: Extract task details, dates, priorities
- **Context Retrieval**: Semantic search for relevant context
- **Pattern Learning**: Learn user habits and preferences
- **Recommendation**: Suggest actions, priorities, times
- **Personalization**: Tailor responses to user

#### Analytics Operations
- **Completion Tracking**: Calculate completion rates
- **Time Analysis**: Compare estimated vs actual duration
- **Productivity Metrics**: Measure productivity by pillar, time
- **Trend Analysis**: Identify patterns over time
- **Forecasting**: Predict deadline readiness
- **Reporting**: Generate daily/weekly/monthly reports

#### Scheduler Operations
- **Daily Kickoff**: Morning summary generation (on bot start + work_start_hour)
  - Shows existing schedule
  - Calculates free hours
  - Recommends tasks based on priority and deadlines
- **Check-ins**: Periodic proactive check-ins
- **Reminders**: Deadline reminders
- **Weekly Review**: End-of-week summary
- **Calendar Sync**: Periodic calendar synchronization (every 4 hours + on-demand)
  - Bidirectional sync (tasks ↔ calendar)
  - Always requires user confirmation
- **Cleanup**: Archive old data, cleanup tasks

#### Memory Operations
- **Store**: Save conversations with embeddings
- **Search**: Semantic search for similar conversations
- **Retrieve**: Get relevant context for AI
- **Learn**: Update patterns based on user behavior
- **Forget**: Privacy-based data deletion

#### Adaptive Learning Operations
- **Learn from Mistakes**: Store corrections, update behavior
  - Track when user corrects agent actions
  - Store mistake patterns (wrong categorization, priority, scheduling)
  - Update agent behavior based on corrections
  - Reduce confidence in patterns where mistakes occurred
  
- **Pattern Recognition**: Identify repeated behaviors
  - Recurring task patterns (same task repeated)
  - Scheduling patterns (same times used)
  - Task sequences (tasks always in order)
  - Daily routine patterns
  
- **Automatic Flow Creation**: Create workflows from patterns
  - Detect flow patterns (recurring actions)
  - Suggest automatic flow creation
  - Create reusable workflows
  - Store flow templates
  
- **Behavior-Based Adaptation**: Adapt to daily behavior
  - Monitor user activity patterns (when most active)
  - Adjust check-in times based on activity
  - Personalize suggestions to user's schedule
  - Adapt to evolving preferences
  
- **Continuous Learning**: Improve over time
  - Track suggestion acceptance rates
  - Monitor correction frequency
  - Update confidence scores
  - Refine personalization models
  
- **Feedback Loop Processing**: Learn from user feedback
  - Process explicit feedback (positive/negative)
  - Learn from implicit feedback (ignored suggestions)
  - Update behavior based on feedback
  - Refine patterns based on success/failure

### Integration Operations

#### Telegram Integration
- **Send Message**: Send text, keyboards, media
- **Receive Message**: Handle commands, text, callbacks
- **Edit Message**: Update sent messages
- **Delete Message**: Remove messages
- **Rate Limiting**: Respect Telegram rate limits

#### Google Calendar Integration
- **OAuth Flow**: Authorize access to calendar (pre-integrated for now, optional in future)
- **Token Management**: Refresh expired tokens
- **Event CRUD**: Create, read, update, delete events (always with user confirmation)
- **Bidirectional Sync**: Keep tasks and calendar synchronized
  - **Task → Calendar**: When tasks created/updated/deleted, sync to calendar (with confirmation)
  - **Calendar → Task**: When events changed externally, sync to tasks (with confirmation)
  - **Due Date Based**: Auto-suggest scheduling based on due dates and prep time
  - **Periodic Sync**: Every 4 hours + on-demand sync
  - **Always Confirm**: User confirmation required for all sync operations
- **API Error Handling**: Handle rate limits, errors
- **Webhook Handling**: Receive calendar updates (future - for real-time sync)

#### LLM Integration (Gemini/OpenAI)
- **Chat Completion**: Generate responses
- **Embeddings**: Generate text embeddings
- **Fallback Logic**: Switch between providers
- **Rate Limiting**: Respect API rate limits
- **Error Handling**: Retry, fallback, graceful degradation

#### Database Operations
- **Connection Pooling**: Manage database connections
- **Transactions**: Ensure data consistency
- **Migrations**: Schema updates
- **Backup**: Regular data backups
- **Query Optimization**: Efficient queries with indexes

---

## Use Cases

### User Use Cases

#### UC1: New User Onboarding
**Actor**: New User  
**Goal**: Set up account and start using bot  
**Steps**:
1. User sends `/start` on Telegram
2. Bot welcomes and starts onboarding
3. User selects pillars (work, education, etc.)
4. User sets work hours and timezone
5. User optionally connects Google Calendar
6. User adds initial tasks (optional)
7. Onboarding complete, bot ready to use

**Success Criteria**: User can use all bot features

#### UC2: Create Task via Natural Language
**Actor**: User  
**Goal**: Quickly add a task by talking naturally  
**Steps**:
1. User sends: "Add task: Prepare presentation for meeting tomorrow"
2. Bot extracts intent and entities
3. Bot categorizes task (e.g., "work")
4. Bot asks for confirmation and missing details
5. User confirms or corrects
6. Bot creates task with metadata
7. Bot confirms creation

**Success Criteria**: Task created with correct details

#### UC3: Schedule Task on Calendar (With Confirmation)
**Actor**: User  
**Goal**: Find time and schedule task on calendar with confirmation  
**Steps**:
1. User views task list
2. User clicks "Schedule" on a task
3. Bot checks calendar availability (considers due dates, prep time)
4. Bot suggests optimal time slots with reasoning
5. User selects preferred time
6. Bot shows scheduling confirmation with details
7. User confirms scheduling
8. Bot creates calendar event (with confirmation message)
9. Bot links event to task (calendar_event_id stored)
10. Bot updates task scheduled_start/scheduled_end
11. Bot confirms synchronization

**Success Criteria**: Task scheduled, visible in Google Calendar, task and calendar in sync

#### UC3b: Bidirectional Task-Calendar Sync
**Actor**: User  
**Goal**: Keep tasks and calendar synchronized automatically  
**Steps**:
1. User creates task with due_date and estimated_duration
2. Bot calculates optimal scheduling time (due_date - duration - prep_time)
3. Bot suggests scheduling (with confirmation required)
4. OR user updates task due_date
5. Bot detects change, suggests rescheduling (if already scheduled)
6. User confirms sync
7. Bot updates calendar event
8. OR calendar event changed externally (via Google Calendar app)
9. Bot detects change during periodic sync (every 4 hours)
10. Bot notifies user of calendar change
11. Bot asks for confirmation to update task
12. User confirms
13. Bot syncs task times from calendar

**Success Criteria**: Tasks and calendar always in sync, changes confirmed before applying

#### UC4: Receive Proactive Check-in
**Actor**: User  
**Goal**: Get helpful reminders and prompts  
**Steps**:
1. Bot triggers check-in (every 30 min during work hours)
2. Bot analyzes user's current state (tasks, calendar, patterns)
3. Bot generates personalized check-in message
4. Bot sends check-in with context
5. User can respond or ignore
6. Bot learns from interactions

**Success Criteria**: User receives timely, helpful check-ins

#### UC5: Daily Morning Summary (Enhanced)
**Actor**: User  
**Goal**: Start day with overview of schedule, free hours, and task recommendations  
**Steps**:
1. Bot triggers when bot starts OR at user's work_start_hour
2. Bot fetches today's calendar events from Google Calendar
3. Bot calculates free hours (available time slots)
4. Bot gets all active tasks with priorities
5. Bot analyzes task priorities, deadlines, and prep time
6. Bot matches tasks to free hours (AI-powered recommendations)
7. Bot generates comprehensive summary with:
   - Today's schedule
   - Free hours available
   - Recommended tasks with suggested times
   - Reasoning for recommendations
8. Bot sends morning summary
9. User reviews and can take action

**Success Criteria**: User gets comprehensive daily overview with actionable task recommendations

#### UC6: Weekly Review
**Actor**: User  
**Goal**: Review past week and plan next week  
**Steps**:
1. Bot triggers weekly review (Sunday morning)
2. Bot calculates analytics for past week
3. Bot generates insights and trends
4. Bot sends weekly review message
5. User reviews statistics
6. User optionally sets goals for next week
7. Bot stores goals for tracking

**Success Criteria**: User understands productivity patterns

#### UC7: AI-Powered Task Prioritization
**Actor**: User  
**Goal**: Get intelligent task prioritization  
**Steps**:
1. User sends `/prioritize`
2. Bot gets all active tasks
3. Bot retrieves user patterns and context
4. AI analyzes tasks considering:
   - Deadlines
   - Dependencies
   - Workload
   - User patterns
5. Bot suggests new priorities with reasoning
6. User reviews suggestions
7. User applies or customizes priorities
8. Bot updates task priorities

**Success Criteria**: Tasks prioritized intelligently

#### UC8: Manage Settings
**Actor**: User  
**Goal**: Customize bot behavior  
**Steps**:
1. User sends `/settings`
2. Bot shows current settings
3. User selects setting to change
4. Bot asks for new value
5. User provides new value
6. Bot validates and saves
7. Bot confirms update

**Success Criteria**: Settings updated and applied

#### UC9: Handle Calendar Conflicts
**Actor**: User  
**Goal**: Resolve scheduling conflicts  
**Steps**:
1. User attempts to schedule task
2. Bot detects conflict with existing event
3. Bot warns user about conflict
4. Bot suggests alternative times
5. User selects alternative OR chooses to schedule anyway
6. Bot processes choice
7. Bot confirms scheduling

**Success Criteria**: Conflict resolved, user informed

#### UC10: Natural Language Task Updates
**Actor**: User  
**Goal**: Update tasks using natural language  
**Steps**:
1. User sends: "Change task 'Prepare presentation' priority to high"
2. Bot extracts intent and entities
3. Bot finds matching task
4. Bot asks for confirmation
5. User confirms
6. Bot updates task
7. Bot confirms update

**Success Criteria**: Task updated correctly via natural language

#### UC11: Agent Learns from Correction
**Actor**: User  
**Goal**: Agent improves from user corrections  
**Steps**:
1. Agent suggests: Task "Code review" → Category "Work"
2. User corrects: "Code review" → Category "Projects"
3. Agent detects correction
4. Agent stores correction in learning_feedback
5. Agent updates categorization model
6. Agent adjusts confidence for similar tasks
7. Next time: Agent suggests "Projects" for "Code review" tasks
8. User accepts → Agent increases confidence
9. Agent continues learning from future interactions

**Success Criteria**: Agent accuracy improves over time, fewer corrections needed

#### UC12: Automatic Flow Creation
**Actor**: User  
**Goal**: Agent creates automatic flows from user patterns  
**Steps**:
1. User creates "Weekly standup" every Monday at 9 AM (3 weeks)
2. Agent detects recurring pattern
3. Agent calculates pattern strength (high confidence)
4. Agent suggests automatic flow creation
5. User reviews flow details
6. User confirms flow creation
7. Agent creates flow template
8. Every Monday: Agent asks "Create Weekly standup?" (with confirmation)
9. User accepts → Flow executes
10. User modifies → Agent learns from modification, updates flow
11. Flow evolves with user's needs

**Success Criteria**: Flow created, executes correctly, adapts to user changes

#### UC13: Behavioral Adaptation
**Actor**: User  
**Goal**: Agent adapts to user's daily behavior  
**Steps**:
1. Agent monitors user behavior (response times, task completion, scheduling)
2. Agent detects patterns:
   - User responds at 10 AM (not 9 AM)
   - User prefers afternoon scheduling
   - User completes tasks faster in mornings
3. Agent adapts behavior:
   - Moves check-ins to 10 AM
   - Suggests afternoon scheduling times
   - Recommends complex tasks in morning
4. User notices improved suggestions
5. User accepts more suggestions (higher acceptance rate)
6. Agent continues monitoring and adapting

**Success Criteria**: Agent behavior matches user preferences, acceptance rate increases

#### UC11: Agent Learns from Mistake
**Actor**: User  
**Goal**: Agent learns when it makes a mistake  
**Steps**:
1. Agent categorizes task incorrectly (e.g., "education" instead of "work")
2. User corrects: "No, this is work, not education"
3. Agent stores correction with context
4. Agent updates categorization model
5. Next time similar task appears, agent uses corrected category
6. Agent asks for confirmation when uncertain
7. Over time, agent improves accuracy for this user

**Success Criteria**: Agent learns from corrections, improves accuracy over time

#### UC12: Automatic Flow Creation from Patterns
**Actor**: User  
**Goal**: Agent creates automatic workflows from repeated patterns  
**Steps**:
1. User repeatedly creates "Weekly team meeting" every Monday at 10 AM
2. Agent detects pattern after 2-3 occurrences
3. Agent suggests: "I notice you create this task every Monday. Would you like me to set up a recurring flow?"
4. User confirms
5. Agent creates automatic flow template
6. Next Monday, agent suggests creating the task automatically
7. User confirms or edits
8. Agent learns from user's edits to improve flow

**Success Criteria**: Agent detects patterns, creates flows, learns to automate repeated actions

#### UC13: Behavior-Based Adaptation
**Actor**: User  
**Goal**: Agent adapts to daily behavior patterns  
**Steps**:
1. Agent monitors user activity over time
2. Agent learns: User is most active 9-11 AM and 2-4 PM
3. Agent adjusts check-in times to these active hours
4. Agent learns: User completes work tasks better in mornings
5. Agent suggests work tasks for morning slots
6. Agent learns: User prefers scheduling tasks 1 day before deadline
7. Agent adapts scheduling suggestions to match preference
8. User notices agent "getting smarter" and more personalized

**Success Criteria**: Agent adapts suggestions to user's actual behavior patterns

### Agent Use Cases

#### AC1: Intent Extraction
**Actor**: AI Agent  
**Goal**: Understand user's intent from message  
**Steps**:
1. Receive user message
2. Retrieve relevant context from memory
3. Generate embedding for message
4. Pass to LLM with context
5. Extract intent (structured)
6. Extract entities (task, date, priority, etc.)
7. Calculate confidence score
8. Return structured result

**Success Criteria**: Intent identified with >70% confidence

#### AC2: Context-Aware Response Generation
**Actor**: AI Agent  
**Goal**: Generate personalized, context-aware responses  
**Steps**:
1. User sends message
2. Retrieve user context:
   - Recent conversations
   - Active tasks
   - Calendar events
   - User patterns
3. Generate embedding for query
4. Semantic search for similar past interactions
5. Build context object
6. Pass context to LLM
7. LLM generates personalized response
8. Return response to user

**Success Criteria**: Response is relevant and personalized

#### AC3: Task Auto-Categorization
**Actor**: AI Agent  
**Goal**: Automatically categorize tasks into pillars  
**Steps**:
1. Receive task title/description
2. Retrieve user's task history
3. Get user patterns (what they categorize similarly)
4. Pass to LLM with context
5. LLM categorizes task
6. Store categorization
7. Learn from user corrections

**Success Criteria**: Categorization accuracy >85%

#### AC4: Priority Scoring
**Actor**: AI Agent  
**Goal**: Calculate optimal priority for tasks  
**Steps**:
1. Get task details (due date, duration, dependencies)
2. Get user's active tasks
3. Retrieve user priority patterns
4. Calculate factors:
   - Deadline urgency
   - Dependency blocking
   - Workload balance
   - Strategic importance
5. LLM generates priority score (0-100)
6. Map to priority level
7. Provide reasoning

**Success Criteria**: Priority aligns with user's actual urgency

#### AC5: Time Slot Suggestion
**Actor**: AI Agent  
**Goal**: Suggest optimal times for task scheduling  
**Steps**:
1. Get task details (duration, priority, deadline)
2. Get calendar availability
3. Get user work hours and patterns
4. Find available slots
5. Rank slots by:
   - Deadline proximity
   - User energy patterns
   - Meeting breaks
   - Preferred working times
6. Generate top suggestions with reasoning
7. Return to user

**Success Criteria**: Suggestions are practical and accepted >60%

#### AC6: Pattern Learning
**Actor**: AI Agent  
**Goal**: Learn user habits and preferences  
**Steps**:
1. Monitor user actions (task completion, scheduling, etc.)
2. Calculate metrics (completion times, patterns)
3. Identify correlations:
   - Time of day productivity
   - Pillar preferences
   - Priority patterns
   - Duration estimates
4. Store patterns in habits table
5. Update pattern weights
6. Use patterns for future suggestions

**Success Criteria**: Patterns improve suggestion accuracy over time

#### AC7: Proactive Check-in Generation
**Actor**: AI Agent  
**Goal**: Generate contextual, helpful check-ins  
**Steps**:
1. Scheduler triggers check-in
2. Get user's current state:
   - Active tasks
   - Upcoming deadlines
   - Calendar events
   - Recent activity
3. Check for pending clarifications
4. Generate personalized check-in message
5. Include relevant context
6. Offer actionable options
7. Send to user

**Success Criteria**: Check-ins are timely and helpful

#### AC8: Deadline Readiness Forecasting
**Actor**: AI Agent  
**Goal**: Predict if user will meet deadlines  
**Steps**:
1. Get task with deadline
2. Calculate remaining work:
   - Task duration
   - Dependencies
   - User's workload
3. Get user's completion patterns:
   - Average completion time
   - Productivity trends
4. Calculate readiness score
5. Alert if at risk
6. Suggest actions (break down task, extend deadline, etc.)

**Success Criteria**: Accurately predicts deadline risks

#### AC9: Conversation Memory Management
**Actor**: AI Agent  
**Goal**: Maintain and retrieve conversation context  
**Steps**:
1. Store each conversation with embedding
2. Generate embedding for new message
3. Semantic search for relevant past conversations
4. Retrieve top K similar conversations
5. Build context from conversations
6. Pass context to LLM
7. Update memory with new conversation

**Success Criteria**: Context retrieval improves response quality

#### AC10: Learn from User Corrections
**Actor**: Agent  
**Goal**: Improve accuracy by learning from user corrections  
**Steps**:
1. Agent suggests task categorization: "Code review" → "Work"
2. User corrects: "Code review" → "Projects"
3. Agent detects correction
4. Agent stores correction in learning_feedback table:
   - Original action: Category "Work"
   - User correction: Category "Projects"
   - Context: Task title "Code review", time, user patterns
   - Confidence before: 0.7
5. Agent analyzes root cause: Categorization model needs update
6. Agent updates categorization rules:
   - Decrease weight for "Work" category for "code review" tasks
   - Increase weight for "Projects" category for "code review" tasks
7. Agent adjusts confidence scores for similar tasks
8. Next similar task: Agent suggests "Projects" with higher confidence
9. If user accepts → Agent increases confidence further
10. Agent continues learning from future corrections

**Success Criteria**: Agent accuracy improves, fewer corrections needed over time

#### AC11: Detect and Suggest Automatic Flows
**Actor**: Agent  
**Goal**: Create automatic flows from detected user patterns  
**Steps**:
1. Agent monitors user behavior over 3 weeks
2. Agent detects pattern: "Weekly standup" created every Monday at 9 AM
3. Agent calculates pattern strength:
   - Frequency: 3/3 weeks (100%)
   - Consistency: Same day, same time
   - Confidence: 0.9 (high)
4. Pattern strength > threshold (0.7) → Suggest flow
5. Agent generates flow suggestion message
6. User reviews and confirms flow creation
7. Agent creates flow template in database:
   - Trigger: Every Monday at 9:00 AM
   - Actions: Create task "Weekly standup", schedule 9-10 AM, priority High
   - Confirmation required: Yes
8. Every Monday: Agent checks if flow should execute
9. Agent asks for confirmation before executing
10. User accepts → Flow executes
11. User modifies → Agent learns from modification, updates flow
12. Agent tracks flow success rate, adapts if needed

**Success Criteria**: Flow created, executes correctly, adapts to user changes

#### AC12: Adapt to User's Daily Behavior
**Actor**: Agent  
**Goal**: Adapt agent behavior to match user's daily patterns  
**Steps**:
1. Agent continuously monitors user behavior:
   - Response times: User responds at 10 AM (not 9 AM)
   - Task completion: Mostly in mornings
   - Scheduling: User prefers afternoon times
   - Active hours: 10 AM - 12 PM, 2 PM - 5 PM
2. Agent analyzes patterns daily/weekly
3. Agent adapts behavior:
   - Check-in timing: Move from 9 AM to 10 AM
   - Task recommendations: Suggest complex tasks in morning
   - Scheduling suggestions: Prefer afternoon times
   - Message timing: Send during active hours only
4. Agent tracks adaptation effectiveness:
   - Acceptance rate increases
   - User responds faster
   - Fewer rejections
5. Agent continues monitoring and adapting
6. Agent detects behavior changes and adapts accordingly

**Success Criteria**: Agent behavior matches user preferences, acceptance rate increases

#### AC13: Self-Improvement Through Feedback Loop
**Actor**: Agent  
**Goal**: Continuously improve through feedback and pattern analysis  
**Steps**:
1. Agent tracks all interactions:
   - Suggestions made
   - User responses (accept/reject/correct)
   - Confidence scores
   - Outcomes
2. Agent analyzes patterns:
   - Which suggestions are accepted
   - Which suggestions are rejected
   - What corrections are made
   - When mistakes occur
3. Agent updates models:
   - Adjust categorization rules
   - Update priority weights
   - Refine scheduling preferences
   - Improve intent extraction
4. Agent calibrates confidence:
   - If high confidence wrong → Lower threshold
   - If low confidence right → Increase threshold
   - Learn accurate confidence levels
5. Agent creates personalized rules for user
6. Agent monitors improvement:
   - Mistake rate decreases
   - Acceptance rate increases
   - User satisfaction improves
7. Agent continues self-improvement cycle

**Success Criteria**: Agent accuracy and user satisfaction improve over time

#### AC14: Error Recovery and Fallbacks
**Actor**: AI Agent  
**Goal**: Handle failures gracefully  
**Steps**:
1. Detect error (API failure, parsing error, etc.)
2. Attempt retry with exponential backoff
3. If retry fails, use fallback:
   - Rule-based responses
   - Cached responses
   - Generic helpful message
4. Log error for debugging
5. Notify user of issue (if needed)
6. Continue service with degraded functionality

**Success Criteria**: Service continues despite errors

#### AC11: Learn from Mistakes (Enhanced)
**Actor**: AI Agent  
**Goal**: Learn when user corrects agent's actions  
**Steps**:
1. Agent makes action (categorization, priority suggestion, etc.)
2. User corrects agent's action
3. Agent stores correction:
   - What agent did wrong
   - What user corrected to
   - Context of mistake
   - Confidence level before mistake
4. Analyze mistake pattern:
   - Is this mistake repeated?
   - Pattern in corrections
   - Context where mistakes occur
5. Update agent behavior:
   - Adjust rules for this user
   - Reduce confidence in similar cases
   - Ask for confirmation more when uncertain
6. Apply learned correction:
   - Next similar situation, use corrected behavior
   - Increase confidence if correction works

**Success Criteria**: Agent learns from corrections, improves accuracy over time

#### AC12: Pattern Recognition for Automatic Flows (Enhanced)
**Actor**: AI Agent  
**Goal**: Detect repeated patterns and suggest automation  
**Steps**:
1. Monitor user behavior continuously
2. Detect repeated patterns:
   - Recurring tasks (same task repeated)
   - Scheduling patterns (same time slots)
   - Task sequences (tasks always in order)
   - Daily routines (same actions at same times)
3. Identify flow patterns:
   - Recurring task flows
   - Task sequence flows
   - Scheduling flows
   - Daily routine flows
4. Calculate pattern strength:
   - How many times pattern occurred
   - Consistency of pattern
   - Confidence score
5. Suggest automatic flow creation:
   - Show pattern detected
   - Offer to create automatic flow
   - Explain what will be automated
6. Create flow template when user confirms
7. Apply flow automatically (with confirmation)

**Success Criteria**: Agent detects patterns, creates workflows, automates repeated actions

#### AC13: Behavior-Based Adaptation
**Actor**: AI Agent  
**Goal**: Adapt to user's daily behavior patterns  
**Steps**:
1. Monitor user behavior continuously:
   - Activity times (when user is active)
   - Task completion times
   - Scheduling preferences
   - Response patterns
2. Identify behavior patterns:
   - Daily patterns (time of day)
   - Weekly patterns (day of week)
   - Task patterns (pillars, priorities)
   - Calendar patterns (busy/free times)
3. Adapt agent behavior:
   - Adjust check-in times to user's active hours
   - Adjust suggestion timing
   - Adapt priority suggestions to user's actual priorities
   - Adjust scheduling suggestions to preferred times
4. Create personalized workflows:
   - Morning routines
   - Daily planning workflows
   - Task review workflows
5. Continuously refine adaptation:
   - Update as patterns change
   - Adapt to evolving preferences
   - Learn from user's changing behavior

**Success Criteria**: Agent adapts suggestions to user's actual behavior patterns

#### AC14: Feedback Loop Processing
**Actor**: AI Agent  
**Goal**: Learn from user feedback (explicit and implicit)  
**Steps**:
1. Track user feedback:
   - Explicit feedback (positive/negative ratings)
   - Implicit feedback (ignored suggestions, corrections)
   - User actions (accept/reject suggestions)
2. Analyze feedback patterns:
   - What suggestions are accepted?
   - What suggestions are rejected?
   - What patterns lead to positive feedback?
   - What patterns lead to negative feedback?
3. Update behavior based on feedback:
   - Positive feedback → Increase confidence, apply more often
   - Negative feedback → Decrease confidence, ask more questions
   - Patterns with high acceptance → Automate more
   - Patterns with low acceptance → Ask for confirmation
4. Refine personalization:
   - Adjust thresholds based on feedback
   - Update weights for different factors
   - Improve suggestions over time
5. Continuous improvement:
   - Monitor suggestion acceptance rates
   - Track correction frequency
   - Update confidence scores
   - Refine models based on success/failure

**Success Criteria**: Agent learns from feedback, improves suggestions over time

---

## Execution Plan

### Phase 1: Foundation & Core Features (Weeks 1-2)

#### Week 1: Setup & Basic Infrastructure
- [ ] Fix dependency conflicts (Pydantic/LangChain)
- [ ] Set up proper error handling
- [ ] Implement robust logging
- [ ] Create database connection pooling
- [ ] Set up basic command handlers (/start, /help)

**Deliverables**:
- Working bot with basic commands
- Stable database connections
- Error handling framework

#### Week 2: Task Management Core
- [ ] Implement task CRUD operations
- [ ] Create task list view with filtering
- [ ] Implement task creation flow (command-based)
- [ ] Add task status management
- [ ] Create task detail view

**Deliverables**:
- Complete task management
- Task filtering and sorting
- Task status transitions

### Phase 2: AI & Natural Language (Weeks 3-4)

#### Week 3: Intent Extraction
- [ ] Implement AI intent extraction
- [ ] Create entity extraction for tasks
- [ ] Build natural language task creation
- [ ] Add task categorization (AI-powered)
- [ ] Implement confidence scoring

**Deliverables**:
- Natural language task creation
- AI categorization
- Intent extraction working

#### Week 4: Context & Memory
- [ ] Set up vector store for conversations
- [ ] Implement conversation storage
- [ ] Create context retrieval system
- [ ] Build semantic search
- [ ] Add personalized responses

**Deliverables**:
- Memory system operational
- Context-aware responses
- Conversation history search

### Phase 3: Calendar Integration (Weeks 5-6)

#### Week 5: Calendar Connection
- [ ] Implement OAuth flow for Google Calendar
- [ ] Create token management (refresh, expiry)
- [ ] Build calendar event fetching
- [ ] Add calendar connection UI
- [ ] Test OAuth flow end-to-end

**Deliverables**:
- Calendar OAuth working
- Token management robust
- Calendar events viewable

#### Week 6: Scheduling & Conflicts
- [ ] Implement availability checking
- [ ] Create time slot finding algorithm
- [ ] Build conflict detection
- [ ] Add task-to-calendar scheduling
- [ ] Implement calendar sync

**Deliverables**:
- Task scheduling on calendar
- Conflict detection
- Calendar sync working

### Phase 4: Advanced Features & Adaptive Learning (Weeks 7-8)

#### Week 7: Prioritization, Analytics & Adaptive Learning Foundation
- [ ] **Prioritization & Analytics**:
  - [ ] Implement AI priority scoring
  - [ ] Create prioritization UI (/prioritize command)
  - [ ] Build analytics calculations
  - [ ] Add statistics views
  - [ ] Implement deadline forecasting

- [ ] **Learn from Mistakes**:
  - [ ] Implement feedback storage (explicit and implicit)
  - [ ] Create mistake tracking system
  - [ ] Build correction learning mechanism
  - [ ] Update categorization rules based on corrections
  - [ ] Adjust confidence scores based on feedback
  - [ ] Test with corrections and verify learning

- [ ] **Pattern Recognition**:
  - [ ] Enhance pattern detection algorithms
  - [ ] Track recurring task patterns
  - [ ] Detect scheduling patterns
  - [ ] Identify task sequence patterns
  - [ ] Calculate pattern strength scores
  - [ ] Test pattern detection accuracy

- [ ] **Behavior Monitoring**:
  - [ ] Monitor daily activity patterns (active hours)
  - [ ] Track weekly patterns (productive days)
  - [ ] Analyze task completion patterns
  - [ ] Monitor calendar usage patterns
  - [ ] Store behavior metrics in database

**Deliverables**:
- AI prioritization
- Analytics dashboard
- Deadline predictions
- Adaptive learning foundation
- Pattern recognition system
- Behavior monitoring

#### Week 8: Proactive Features & Automatic Adaptation
- [ ] **Proactive Features**:
  - [ ] Implement scheduler jobs
  - [ ] Create daily kickoff summary (enhanced with free hours and recommendations)
  - [ ] Build check-in system (30-min intervals, adaptive timing)
  - [ ] Add reminder system
  - [ ] Create weekly review

- [ ] **Automatic Flow Creation**:
  - [ ] Create flow template system
  - [ ] Implement flow suggestion mechanism
  - [ ] Build flow execution engine
  - [ ] Add flow confirmation system
  - [ ] Create flow editing interface
  - [ ] Test automatic flow creation and execution

- [ ] **Behavior-Based Adaptation**:
  - [ ] Implement adaptive check-in timing (based on user activity)
  - [ ] Adjust suggestion timing based on activity
  - [ ] Adapt priority suggestions to user patterns
  - [ ] Personalize scheduling suggestions
  - [ ] Create personalized workflows (morning, afternoon, evening)
  - [ ] Test adaptation accuracy

- [ ] **Feedback Loop Processing**:
  - [ ] Process explicit feedback (ratings, comments)
  - [ ] Process implicit feedback (ignored suggestions)
  - [ ] Update models based on feedback
  - [ ] Refine personalization over time
  - [ ] Monitor suggestion acceptance rates
  - [ ] Test feedback loop effectiveness

**Deliverables**:
- Scheduler operational
- Daily summaries with free hours and recommendations
- Proactive check-ins (adaptive timing)
- Weekly reviews
- Automatic flow creation
- Behavior-based adaptation
- Feedback loop processing

### Phase 5: Onboarding & Settings (Week 9)

#### Week 9: User Experience
- [ ] Complete onboarding flow
- [ ] Implement settings management
- [ ] Add pillar management
- [ ] Create work hours configuration
- [ ] Build user preference management

**Deliverables**:
- Complete onboarding
- Settings management
- User preferences working

### Phase 6: Edge Cases & Polish (Weeks 10-11)

#### Week 10: Error Handling
- [ ] Implement all edge case handlers
- [ ] Add graceful error recovery
- [ ] Create user-friendly error messages
- [ ] Add retry logic for APIs
- [ ] Implement rate limiting

**Deliverables**:
- Robust error handling
- Graceful degradation
- User-friendly errors

#### Week 11: Testing & Optimization
- [ ] Write unit tests for core features
- [ ] Write integration tests
- [ ] Performance optimization
- [ ] Database query optimization
- [ ] Load testing

**Deliverables**:
- Test coverage >70%
- Optimized performance
- Load tested

### Phase 7: Documentation & Deployment (Week 12)

#### Week 12: Final Polish
- [ ] Complete documentation
- [ ] Create user guide
- [ ] Set up production deployment
- [ ] Configure monitoring (Sentry)
- [ ] User acceptance testing

**Deliverables**:
- Complete documentation
- Production deployment
- Monitoring setup
- Bot ready for users

### Implementation Priorities

#### Must Have (MVP)
1. ✅ User registration & onboarding
2. ✅ Task CRUD operations
3. ✅ Basic natural language task creation
4. ✅ Calendar connection & viewing
5. ✅ Task scheduling on calendar
6. ✅ Basic AI intent extraction

#### Should Have (Version 1.0)
1. ✅ AI categorization & prioritization
2. ✅ Context-aware responses
3. ✅ Proactive check-ins
4. ✅ Daily summaries
5. ✅ Weekly reviews
6. ✅ Settings management

#### Nice to Have (Version 2.0)
1. ⏳ Advanced analytics
2. ⏳ Task dependencies
3. ⏳ Multi-language support
4. ⏳ Task templates
5. ⏳ Collaboration features
6. ⏳ Mobile app integration

### Risk Mitigation

#### Technical Risks
- **Dependency Conflicts**: ✅ Fixed (Pydantic/LangChain upgraded)
- **API Rate Limits**: Implement queueing and caching
- **Database Performance**: Add indexes, optimize queries
- **LLM Costs**: Implement caching, use efficient models

#### User Experience Risks
- **Confusing Onboarding**: Iterate based on feedback
- **Natural Language Accuracy**: Provide fallback commands
- **Information Overload**: Limit message length, paginate

#### Operational Risks
- **Service Downtime**: Implement health checks, monitoring
- **Data Loss**: Regular backups, transaction safety
- **Scalability**: Plan for horizontal scaling early

### Success Metrics

#### Technical Metrics
- Uptime >99%
- Response time <2 seconds
- Error rate <1%
- Test coverage >70%

#### User Metrics
- Onboarding completion rate >80%
- Daily active users
- Task creation rate
- Calendar connection rate

#### AI Metrics
- Intent extraction accuracy >85%
- Task categorization accuracy >80%
- User satisfaction with AI suggestions >70%

---

## Conclusion

This comprehensive plan covers all aspects of the AI Productivity Agent bot:
- **Complete user flows** from onboarding to advanced features
- **Detailed agent flows** for AI processing and decision-making
- **Comprehensive edge cases** with solutions
- **Full menu structure** with all options and sub-options
- **All operations** (CRUD, business logic, integrations)
- **User and agent use cases** with step-by-step flows
- **12-week execution plan** with clear phases and deliverables

The plan is designed to be:
- **Iterative**: Build incrementally, test frequently
- **User-centric**: Focus on solving real productivity problems
- **AI-enhanced**: Leverage AI while maintaining reliability
- **Scalable**: Architecture supports growth
- **Maintainable**: Clean code, good documentation

Next steps: Begin Phase 1, Week 1 implementation!

