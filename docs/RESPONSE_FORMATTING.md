# Response Formatting Guidelines

## Overview

The bot's responses are now structured with proper paragraph formatting for better readability, especially on mobile devices.

## Formatting Rules

### Paragraph Structure
- **Use double line breaks** (`\n\n`) to separate paragraphs
- **Keep paragraphs concise** (2-4 sentences each)
- **Break long responses** into multiple paragraphs
- **Separate different topics** with paragraph breaks

### Example

**Before (unformatted):**
```
I can't access your calendar directly, but I can help you with any scheduling questions or tasks you want to manage! If you tell me what you need, I'll do my best to assist you. Do you want to set up a new event or check something specific?
```

**After (formatted):**
```
I can't access your calendar directly, but I can help you with any scheduling questions or tasks you want to manage!

If you tell me what you need, I'll do my best to assist you. Do you want to set up a new event or check something specific?
```

## Implementation

### Agent Description
The Parlant agent includes formatting instructions in its description:
- Always structure responses with clear paragraphs
- Use double line breaks between paragraphs
- Keep paragraphs concise (2-4 sentences)
- Format for mobile readability

### Formatting Guidelines
A guideline is set that applies to all responses:
- Structure responses with clear paragraphs
- Use double line breaks (`\n\n`) to separate paragraphs
- Break long responses into multiple paragraphs
- Keep responses well-formatted for mobile devices

### Post-Processing
The `_format_response()` function automatically:
- Normalizes line breaks
- Adds paragraph breaks to long responses without structure
- Groups sentences into logical paragraphs (2-3 sentences each)
- Cleans up excessive whitespace

## Best Practices

### When to Use Paragraphs
1. **Separate topics**: Each new topic gets its own paragraph
2. **Long explanations**: Break into multiple paragraphs
3. **Lists**: Use line breaks between list items
4. **Questions**: Separate questions from explanations

### Example Structure

```
[Introduction paragraph - 2-3 sentences]

[Main content paragraph - explains the topic]

[Action paragraph - what the user can do next]

[Optional closing paragraph - offer further help]
```

## Testing

To test formatting:
1. Send a message that would generate a long response
2. Check that the response has proper paragraph breaks
3. Verify readability on mobile devices

## Configuration

Formatting is controlled by:
- `agents_parlant/agent.py` - Agent description and guidelines
- `_format_response()` function - Post-processing

To adjust formatting, modify:
1. Agent description formatting rules
2. Formatting guidelines
3. `_format_response()` function logic

