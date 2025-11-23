# Duplicate Task Detection

## Overview

The bot now detects duplicate or similar tasks before creating them, helping users avoid accidentally creating the same task multiple times.

## How It Works

### Detection Methods

1. **Title Similarity**
   - Uses fuzzy string matching (SequenceMatcher)
   - Compares normalized task titles
   - Threshold: 85% similarity (configurable)

2. **Due Date Proximity**
   - Checks if tasks have similar due dates
   - Window: ±7 days (configurable)
   - Boosts similarity score if dates are close

3. **Exact Matches**
   - Detects exact title matches (case-insensitive)
   - Removes common prefixes ("add", "create", "new", etc.)

### Normalization

Task titles are normalized before comparison:
- Removes common prefixes: "add", "create", "new", "task", "reminder", "todo"
- Converts to lowercase
- Normalizes whitespace
- Trims punctuation

## User Experience

### Natural Language Task Creation

When creating a task via natural language:

1. **Duplicate Detected** (≥85% similarity):
   - Bot shows warning with similar tasks
   - Displays similarity percentage
   - Shows task details (title, due date, status)
   - Offers options:
     - ✅ Create Anyway
     - ❌ Cancel

2. **No Duplicate**:
   - Task is created normally
   - No interruption

### Parlant Agent

When using Parlant agent:
- Duplicate check happens automatically
- Warning is included in response if duplicate found
- Task is still created (user can decide to keep or delete)

## Configuration

### Similarity Threshold

Default: `0.85` (85% similarity)

Can be adjusted in:
- `tasks/duplicate_detection.py` - `check_for_duplicates()`
- `tasks/service.py` - `create_task()`

### Date Window

Default: `7 days`

Tasks with due dates within 7 days are considered for duplicate checking.

## Examples

### Example 1: Exact Duplicate

**Existing Task:**
- Title: "Write LOR"
- Due: Monday morning

**New Task:**
- Title: "write LOR"
- Due: Monday morning

**Result:** ⚠️ Exact duplicate detected (100% similarity)

### Example 2: Similar Task

**Existing Task:**
- Title: "Prepare presentation for client meeting"
- Due: Friday

**New Task:**
- Title: "Prepare presentation for client"
- Due: Friday

**Result:** ⚠️ Similar task found (90% similarity)

### Example 3: Different Tasks

**Existing Task:**
- Title: "Write LOR"
- Due: Monday

**New Task:**
- Title: "Review code"
- Due: Tuesday

**Result:** ✅ No duplicate, task created

## Implementation Details

### Files

- `tasks/duplicate_detection.py` - Core duplicate detection logic
- `tasks/service.py` - Integration with task creation
- `telegram_bot/handlers/natural_language_tasks.py` - UI for duplicate warnings
- `agents_parlant/tools.py` - Parlant agent integration

### Functions

- `check_for_duplicates()` - Main detection function
- `find_duplicate_tasks()` - Finds all similar tasks
- `calculate_string_similarity()` - String similarity calculation
- `normalize_title()` - Title normalization

### Database

Duplicate information is stored in `task_metadata` field:
```json
{
  "duplicate_check": {
    "has_duplicates": true,
    "similar_count": 2,
    "highest_similarity": 0.92
  }
}
```

## Future Enhancements

Potential improvements:
1. **Semantic Similarity** - Use embeddings for better semantic matching
2. **User Learning** - Learn from user decisions (create anyway vs cancel)
3. **Smart Merging** - Suggest merging similar tasks
4. **Time-based Filtering** - Only check recent tasks (e.g., last 30 days)
5. **Category-aware** - Consider pillar/category in similarity

## Testing

To test duplicate detection:

1. Create a task: "Write LOR"
2. Try to create again: "write LOR" or "Write LOR"
3. Bot should detect duplicate and warn

## Troubleshooting

### Issue: False Positives

**Solution:** Lower similarity threshold or improve normalization

### Issue: Missing Duplicates

**Solution:** Increase similarity threshold or check date window

### Issue: Performance

**Solution:** Limit to recent tasks or add caching

