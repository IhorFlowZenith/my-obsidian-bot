# Zefirka Folder Skills

## Purpose
All bot data, settings, and daily management files.

## When to Use This Folder
- Bot configuration
- Task management
- Financial tracking
- Project management
- Daily planning
- Reminders and notifications
- User profile and preferences

## File Naming Convention
- Format: `data_type.md` or `daily_summary_YYYY-MM-DD.md`
- Examples:
  - `tasks.md` - All tasks
  - `finances.md` - Expenses and budget
  - `projects.md` - Pet projects
  - `daily_plans.md` - Daily plans
  - `daily_summary_2026-01-15.md` - Daily summary

## Content Structure

### tasks.md
```markdown
# Tasks

## Active Tasks
### Urgent
- [ ] Task 1

### Important
- [ ] Task 2

### Normal
- [ ] Task 3

## Completed
- [x] Completed task

## Statistics
- Total: X
- Completed: Y
- Rate: Z%
```

### finances.md
```markdown
# Finances

## Monthly Budget
- Limit: 10,000 UAH
- Spent: X UAH
- Remaining: Y UAH

## Expenses by Category
### Food
- Limit: 3,000 UAH
- Spent: X UAH

## Recent Expenses
| Date | Category | Amount | Description |
```

### projects.md
```markdown
# Projects

## Active Projects
### Project 1
- Status: In Progress
- Progress: 50%
- Tech Stack: React Native

## Project Ideas
### Idea 1
- Title: ...
- Description: ...
```

### daily_plans.md
```markdown
# Daily Plans

## Today
### Morning Plan
- [ ] Task 1

### Statistics
- Completed: X/Y
- Spent: Z UAH
```

## Bot Actions
- **Create:** Auto-create daily summaries
- **Edit:** Update tasks, expenses, projects
- **Read:** Load data for analysis and reminders
- **Archive:** Move old data to archive

## Examples
- "Add task: Finish project"
- "Spent 100 on coffee"
- "New project: Mobile App"
- "Show my budget"
- "Daily reflection"

## Important
- This is bot's database
- Don't manually edit (let bot handle it)
- Regular backups
- Archive old data monthly
- Keep format consistent

## File Organization
```
Zefirka/
├── SKILL.md                    # This file
├── SKILLS.md                   # Bot rules
├── README.md                   # Documentation
├── ARCHITECTURE.md             # Technical details
├── tasks.md                    # Task management
├── finances.md                 # Financial tracking
├── projects.md                 # Project management
├── user_profile.md             # User settings
├── reminders.md                # Reminder settings
├── daily_plans.md              # Daily planning
├── daily_notes/                # Daily summaries
│   ├── 2026-01-15.md
│   ├── 2026-01-16.md
│   └── ...
└── archive/                    # Old data
    ├── tasks_archive.md
    ├── finances_archive.md
    └── ...
```
