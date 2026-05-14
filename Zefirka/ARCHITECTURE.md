# Zefirka Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram User                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Telegram Bot (Python)                           │
│  - Message handler                                          │
│  - Command processor                                        │
│  - Response formatter                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Deepseek    │  │   GitHub     │  │   Local      │
│  API (AI)    │  │   API        │  │   Storage    │
│              │  │              │  │              │
│ - Analyze    │  │ - Read files │  │ - JSON files │
│ - Decide     │  │ - Write data │  │ - Cache      │
│ - Respond    │  │ - Sync       │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Obsidian Vault (GitHub)                        │
│  Zefirka/                                                   │
│  ├── SKILLS.md                                              │
│  ├── user_profile.json                                      │
│  ├── tasks.json                                             │
│  ├── finances.json                                          │
│  ├── projects.json                                          │
│  ├── reminders.json                                         │
│  ├── daily_plans.json                                       │
│  ├── daily_notes/                                           │
│  └── archive/                                               │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User sends message
```
User → Telegram → Bot receives message
```

### 2. Bot processes message
```
Bot reads SKILLS.md (rules)
Bot reads user_profile.json (context)
Bot sends to Deepseek API (AI analysis)
Deepseek decides action (create task, add expense, etc.)
```

### 3. Bot executes action
```
Action type:
├── Read: Get data from JSON files
├── Create: Add to JSON, sync to GitHub
├── Update: Modify JSON, sync to GitHub
└── Delete: Remove from JSON, sync to GitHub
```

### 4. Bot syncs to GitHub
```
Bot → GitHub API → Obsidian Vault
Obsidian Git plugin auto-syncs
User sees changes in Obsidian
```

### 5. Bot responds to user
```
Bot formats response
Bot sends to Telegram
User sees result
```

## Component Details

### Message Handler
```python
async def handle_message(update, context):
    1. Get user message
    2. Load SKILLS.md
    3. Load user_profile.json
    4. Send to Deepseek
    5. Execute action
    6. Sync to GitHub
    7. Send response
```

### AI Decision Engine (Deepseek)
```
Input: User message + context
Process: Analyze with system prompt
Output: JSON with action and parameters
{
    "action": "create_task" | "add_expense" | "query" | etc,
    "parameters": {...},
    "reasoning": "why this action"
}
```

### Data Manager
```
Read: GitHub → Local cache → JSON parse
Write: JSON modify → GitHub API → Obsidian sync
Delete: JSON remove → GitHub API → Obsidian sync
Archive: Move old data → archive/ folder
```

### Reminder System
```
Scheduler checks reminders.json every minute
If time matches:
  - Load daily_plans.json
  - Get pending tasks
  - Send reminder to user
  - Mark as sent
```

## File Formats

### JSON Structure
```json
{
  "metadata": {
    "version": "1.0",
    "last_updated": "2026-01-15T10:00:00Z",
    "user_id": "123456789"
  },
  "data": [
    {
      "id": "unique_id",
      "created_at": "ISO8601",
      "updated_at": "ISO8601",
      ...
    }
  ]
}
```

### Daily Notes Format
```markdown
# Daily Summary - 2026-01-15

## Tasks
- [x] Task 1
- [ ] Task 2

## Expenses
- Coffee: 100 UAH
- Lunch: 250 UAH
Total: 350 UAH

## Projects
- Project 1: 50% done

## Reflection
Good day, completed most tasks.
```

## Error Handling

### GitHub Sync Fails
```
1. Save to local cache
2. Retry in 5 minutes
3. If still fails, notify user
4. Sync when connection restored
```

### Invalid JSON
```
1. Log error
2. Restore from backup
3. Notify user
4. Ask to re-enter data
```

### API Fails
```
1. Use cached data
2. Retry with exponential backoff
3. Notify user if critical
4. Continue with local operations
```

## Performance Optimization

### Caching
- Cache SKILLS.md in memory
- Cache user_profile.json
- Cache recent tasks
- Invalidate cache every 5 minutes

### Batch Operations
- Batch GitHub writes (max 5 per minute)
- Batch reminders (send together)
- Archive old data weekly

### Database Queries
- Index by date
- Index by priority
- Index by category
- Limit results to last 100 items

## Security

### Data Protection
- Encrypt sensitive data (passwords, tokens)
- Use .env for credentials
- Never log sensitive data
- Validate all inputs

### Access Control
- Only user can access their data
- Bot token in .env
- GitHub token in .env
- API keys in .env

### Privacy
- Delete data after user request
- Archive old data (don't delete)
- No data sharing
- GDPR compliant

## Scalability

### Current Limits
- 1 user per bot instance
- ~1000 tasks max
- ~10000 expenses max
- ~100 projects max

### Future Scaling
- Multi-user support
- Database instead of JSON
- Caching layer (Redis)
- Message queue (RabbitMQ)
- Microservices architecture

## Deployment

### Development
```
Local machine
Python 3.9+
.env file with credentials
```

### Production
```
Railway / Render / VPS
Docker container
Environment variables
GitHub Actions for CI/CD
```

### Monitoring
```
Log all actions
Track API usage
Monitor performance
Alert on errors
```

## Testing

### Unit Tests
- Test each function
- Mock GitHub API
- Mock Deepseek API

### Integration Tests
- Test full workflow
- Test data sync
- Test error handling

### E2E Tests
- Test from Telegram
- Test full cycle
- Test edge cases
