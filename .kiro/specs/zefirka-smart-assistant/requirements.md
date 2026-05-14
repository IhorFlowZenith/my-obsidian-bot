# Requirements Document: Zefirka Smart Daily Assistant

## Introduction

Zefirka is an intelligent Telegram bot assistant designed to help users manage their daily activities, finances, and pet projects. The system integrates with GitHub for data synchronization, uses Deepseek AI for intelligent decision-making, and stores all data in an Obsidian Vault. The bot provides context-aware assistance across multiple languages and automatically routes information to appropriate categories based on user intent.

## Glossary

- **Zefirka**: The Telegram bot system that manages user data and provides intelligent assistance
- **User**: The person interacting with Zefirka through Telegram
- **Obsidian_Vault**: Local file storage system synchronized with GitHub containing all user data
- **GitHub_Repository**: Remote storage for Obsidian Vault data with version control
- **Deepseek_AI**: External AI service used for analyzing user intent and generating intelligent responses
- **Task**: A discrete unit of work with priority, category, and completion status
- **Expense**: A financial transaction with category, amount, and date
- **Pet_Project**: A personal project idea with progress tracking and status
- **Context**: Historical information about user interactions, preferences, and previous decisions
- **Router**: System component that determines the appropriate storage category (Study/Projects/Work/Personal)
- **Memory_Service**: Component that maintains conversation history and user context
- **Smart_Router**: AI-powered component that automatically categorizes user input
- **Sync_Operation**: Process of pushing local changes to GitHub and pulling remote updates
- **Acceptance_Criteria**: Measurable conditions that verify requirement fulfillment
- **Message_Handler**: Component that processes incoming Telegram messages
- **Vault_Service**: Component that manages local Obsidian Vault file operations
- **GitHub_Service**: Component that handles GitHub API interactions

## Requirements

### Requirement 1: Task Management with Context Preservation

**User Story:** As a user, I want to create, prioritize, and track tasks while the bot remembers the context of my previous interactions, so that I can efficiently manage my daily work without repeating information.

#### Acceptance Criteria

1. WHEN a user sends a message to create a task, THE Zefirka SHALL parse the message using Deepseek_AI to extract task name, priority level, and category
2. WHEN a task is created, THE Zefirka SHALL store the task in Zefirka/tasks.md with metadata including creation timestamp, priority (High/Medium/Low), and category
3. WHEN a user asks about a previously created task, THE Memory_Service SHALL retrieve the conversation history and provide context about when and why the task was created
4. WHEN a user updates a task status, THE Zefirka SHALL update the task in Zefirka/tasks.md and synchronize the change to GitHub within 30 seconds
5. WHILE a user is in an active conversation, THE Memory_Service SHALL maintain the conversation context for at least 24 hours, allowing the user to reference previous messages
6. WHEN a user asks "What should I do first?", THE Zefirka SHALL analyze all tasks using priority and deadline information to recommend the next action
7. IF a user creates a task without specifying a category, THEN THE Smart_Router SHALL automatically determine the appropriate category (Study/Projects/Work/Personal) based on task keywords and user profile

#### Property-Based Testing Criteria

1. **Idempotence**: Creating the same task twice with identical parameters SHALL result in only one task entry in Zefirka/tasks.md
2. **Context Preservation**: FOR ALL user messages in a conversation, THE Memory_Service SHALL preserve the complete message history and allow retrieval of any previous message within 24 hours
3. **Round-Trip Consistency**: FOR ALL tasks created and stored, parsing the task data and re-storing it SHALL produce an equivalent task object

---

### Requirement 2: Intelligent Expense Tracking with Budget Analysis

**User Story:** As a user, I want to log expenses with automatic categorization and receive budget analysis, so that I can understand my spending patterns and stay within my budget.

#### Acceptance Criteria

1. WHEN a user sends an expense message (e.g., "Spent 100 on coffee"), THE Deepseek_AI SHALL extract the amount, category, and optional description
2. WHEN an expense is recorded, THE Zefirka SHALL store it in Zefirka/finances.md with timestamp, amount, category, and description
3. WHEN a user asks "How much did I spend this week?", THE Zefirka SHALL calculate the total expenses for the current week and provide a breakdown by category
4. WHEN total expenses exceed 80% of the monthly budget, THE Zefirka SHALL send a warning notification to the user
5. WHEN a user requests budget analysis, THE Zefirka SHALL compare current spending against the monthly budget and provide recommendations
6. IF a user enters an expense without a category, THEN THE Smart_Router SHALL automatically assign a category based on keywords and historical spending patterns
7. WHEN a user asks for expense history, THE Zefirka SHALL retrieve expenses from Zefirka/finances.md and present them grouped by category and time period

#### Property-Based Testing Criteria

1. **Invariant Preservation**: FOR ALL expense records, the sum of individual expenses SHALL equal the total monthly spending
2. **Metamorphic Property**: IF expenses are added in different orders, THE total spending calculation SHALL produce identical results
3. **Round-Trip Consistency**: FOR ALL expenses serialized to Zefirka/finances.md, parsing and re-serializing SHALL produce equivalent expense objects

---

### Requirement 3: Pet Project Management with Progress Tracking

**User Story:** As a user, I want to create and manage pet projects with progress tracking, so that I can organize my personal ideas and monitor their development.

#### Acceptance Criteria

1. WHEN a user creates a new project (e.g., "New project: Mobile App"), THE Zefirka SHALL store the project in Zefirka/projects.md with name, description, creation date, and initial status (Idea/In Progress/On Hold/Completed)
2. WHEN a user updates project progress (e.g., "Update project: 50% done"), THE Zefirka SHALL parse the progress percentage and update the project status in Zefirka/projects.md
3. WHEN a user asks "Show my projects", THE Zefirka SHALL retrieve all projects from Zefirka/projects.md and display them with current status and progress
4. WHEN a user requests project ideas, THE Zefirka SHALL retrieve all projects with status "Idea" and present them for review
5. WHEN a project is updated, THE Zefirka SHALL synchronize the change to GitHub within 30 seconds
6. IF a user provides project details without explicit status, THEN THE Smart_Router SHALL infer the status based on context and project description

#### Property-Based Testing Criteria

1. **Invariant Preservation**: FOR ALL projects, the progress percentage SHALL remain between 0 and 100
2. **Idempotence**: Updating a project with identical parameters multiple times SHALL result in a single consistent project state
3. **Round-Trip Consistency**: FOR ALL projects serialized to Zefirka/projects.md, parsing and re-serializing SHALL produce equivalent project objects

---

### Requirement 4: GitHub Synchronization and Obsidian Vault Integration

**User Story:** As a user, I want all my data to be automatically synchronized with GitHub and accessible in my Obsidian Vault, so that I have a reliable backup and can access my data across devices.

#### Acceptance Criteria

1. WHEN a user creates, updates, or deletes data (task, expense, or project), THE Zefirka SHALL push the changes to GitHub within 30 seconds
2. WHEN the GitHub_Service detects a conflict during synchronization, THE Zefirka SHALL resolve the conflict by keeping the most recent version and logging the conflict
3. WHEN a user's Obsidian Vault is updated externally (via GitHub), THE Zefirka SHALL pull the latest changes and update its local cache
4. WHEN a synchronization operation fails, THE Zefirka SHALL retry the operation with exponential backoff (5s, 10s, 20s) up to 3 attempts
5. IF a synchronization fails after 3 attempts, THEN THE Zefirka SHALL notify the user and store the pending changes locally until the connection is restored
6. WHEN the connection is restored, THE Zefirka SHALL automatically push all pending changes to GitHub
7. WHEN a user requests data export, THE Zefirka SHALL provide all data in Markdown format compatible with Obsidian

#### Property-Based Testing Criteria

1. **Idempotence**: Pushing the same data to GitHub multiple times SHALL result in a single consistent state
2. **Confluence**: FOR ALL synchronization operations, the order of push/pull operations SHALL not affect the final data state
3. **Round-Trip Consistency**: FOR ALL data synchronized to GitHub, pulling and re-pushing SHALL produce equivalent data

---

### Requirement 5: Multilingual Support

**User Story:** As a user, I want to interact with Zefirka in my preferred language (Ukrainian, Russian, or English), so that I can communicate naturally and receive responses in my language.

#### Acceptance Criteria

1. WHEN a user sends a message in Ukrainian, Russian, or English, THE Zefirka SHALL detect the language and respond in the same language
2. WHEN a user sets their language preference in user_profile.md, THE Zefirka SHALL use that language for all subsequent responses
3. WHEN Zefirka generates responses, THE Zefirka SHALL use language-appropriate terminology and formatting
4. WHEN a user switches languages mid-conversation, THE Zefirka SHALL immediately switch to the new language for subsequent messages
5. IF a user sends a message in an unsupported language, THEN THE Zefirka SHALL ask the user to clarify in one of the supported languages

#### Property-Based Testing Criteria

1. **Idempotence**: Detecting language for the same message multiple times SHALL produce identical language identification
2. **Invariant Preservation**: FOR ALL user messages, the detected language SHALL match the language preference stored in user_profile.md after user selection

---

### Requirement 6: Smart Router for Automatic Categorization

**User Story:** As a user, I want the bot to automatically determine where to store my information (Study/Projects/Work/Personal), so that my data is organized without manual categorization.

#### Acceptance Criteria

1. WHEN a user creates a task, expense, or project, THE Smart_Router SHALL analyze the content using Deepseek_AI to determine the appropriate category
2. WHEN the Smart_Router categorizes content, THE Zefirka SHALL store the content in the appropriate folder (Study/Projects/Work/Personal) within the Obsidian Vault
3. WHEN a user explicitly specifies a category, THE Smart_Router SHALL use the user-specified category instead of automatic detection
4. WHEN the Smart_Router encounters ambiguous content, THE Zefirka SHALL ask the user to clarify the category
5. WHEN a user reviews categorized content, THE Zefirka SHALL display the category alongside the content
6. IF a user disagrees with the automatic categorization, THEN THE Zefirka SHALL allow the user to recategorize the content and learn from the correction

#### Property-Based Testing Criteria

1. **Consistency**: FOR ALL identical content, THE Smart_Router SHALL produce identical categorization results
2. **Metamorphic Property**: IF content is categorized and then re-categorized with the same parameters, THE result SHALL be identical
3. **Invariant Preservation**: FOR ALL categorized content, the category SHALL be one of the four valid categories (Study/Projects/Work/Personal)

---

### Requirement 7: Memory and Context Management

**User Story:** As a user, I want Zefirka to remember my conversation history and understand the context of my requests, so that I don't have to repeat information and can have natural conversations.

#### Acceptance Criteria

1. WHEN a user sends a message, THE Memory_Service SHALL retrieve the conversation history from the last 24 hours
2. WHEN the Memory_Service processes a message, THE Zefirka SHALL use the conversation history to understand context and provide relevant responses
3. WHEN a user references a previous task or expense, THE Memory_Service SHALL identify the reference and provide the relevant information
4. WHEN a conversation reaches 24 hours old, THE Memory_Service SHALL archive the conversation history to daily_notes.md
5. WHEN a user asks "What did I do yesterday?", THE Zefirka SHALL retrieve the archived daily notes and provide a summary
6. WHEN the Memory_Service stores conversation history, THE Zefirka SHALL encrypt sensitive information (passwords, tokens) before storage
7. IF a user requests to delete conversation history, THEN THE Zefirka SHALL permanently delete the specified conversation records

#### Property-Based Testing Criteria

1. **Idempotence**: Retrieving conversation history multiple times for the same time period SHALL produce identical results
2. **Invariant Preservation**: FOR ALL conversation history, the chronological order of messages SHALL be preserved
3. **Round-Trip Consistency**: FOR ALL conversation history archived to daily_notes.md, retrieving and re-archiving SHALL produce equivalent records

---

### Requirement 8: Deepseek AI Integration for Intelligent Analysis

**User Story:** As a user, I want Zefirka to use AI to analyze my requests and provide intelligent recommendations, so that I receive smart suggestions and the bot understands my intent accurately.

#### Acceptance Criteria

1. WHEN a user sends a message, THE Deepseek_AI SHALL analyze the message to determine the user's intent (create_task, add_expense, query, etc.)
2. WHEN Deepseek_AI analyzes a message, THE Zefirka SHALL extract relevant parameters (name, amount, category, priority) from the user's natural language
3. WHEN a user asks for advice (e.g., "Help me decide..."), THE Deepseek_AI SHALL analyze the context and provide intelligent recommendations
4. WHEN Deepseek_AI processes a request, THE Zefirka SHALL include reasoning in the response explaining why a particular action was taken
5. WHEN a Deepseek_AI request fails, THE Zefirka SHALL retry the request with exponential backoff (2s, 4s, 8s) up to 3 attempts
6. IF a Deepseek_AI request fails after 3 attempts, THEN THE Zefirka SHALL fall back to rule-based processing and notify the user
7. WHEN a user provides feedback on AI recommendations, THE Zefirka SHALL log the feedback for future model improvement

#### Property-Based Testing Criteria

1. **Consistency**: FOR ALL identical user messages, THE Deepseek_AI SHALL produce identical intent analysis results
2. **Metamorphic Property**: IF a message is analyzed with different context, THE intent analysis SHALL be consistent with the provided context
3. **Invariant Preservation**: FOR ALL AI responses, the extracted parameters SHALL be valid and match the user's intent

---

### Requirement 9: Message Handler and Command Processing

**User Story:** As a user, I want to interact with Zefirka using natural language commands and messages, so that I can use the bot intuitively without learning complex syntax.

#### Acceptance Criteria

1. WHEN a user sends a message starting with "/", THE Message_Handler SHALL treat it as a command and route it to the appropriate command handler
2. WHEN a user sends a regular message, THE Message_Handler SHALL route it to the Deepseek_AI for intent analysis
3. WHEN a command is processed, THE Zefirka SHALL execute the command and send a response within 5 seconds
4. WHEN a message is processed, THE Zefirka SHALL send a response within 10 seconds
5. IF a message cannot be processed, THEN THE Zefirka SHALL send an error message explaining what went wrong and suggesting alternatives
6. WHEN a user sends multiple messages in quick succession, THE Message_Handler SHALL queue the messages and process them sequentially

#### Property-Based Testing Criteria

1. **Idempotence**: Processing the same message multiple times SHALL produce identical results
2. **Invariant Preservation**: FOR ALL processed messages, the response time SHALL not exceed the specified timeout

---

### Requirement 10: User Profile Management and Preferences

**User Story:** As a user, I want to manage my profile settings and preferences, so that Zefirka can personalize its behavior to my needs.

#### Acceptance Criteria

1. WHEN a user updates their profile (language, timezone, budget), THE Zefirka SHALL store the changes in user_profile.md
2. WHEN a user sets a monthly budget, THE Zefirka SHALL use this budget for expense tracking and alerts
3. WHEN a user sets reminder times, THE Zefirka SHALL send reminders at the specified times
4. WHEN a user requests their profile information, THE Zefirka SHALL display all stored preferences
5. WHEN a user changes their timezone, THE Zefirka SHALL adjust all timestamps and reminder times accordingly
6. IF a user provides invalid profile data, THEN THE Zefirka SHALL reject the change and explain the validation error

#### Property-Based Testing Criteria

1. **Idempotence**: Updating the same profile setting multiple times with identical values SHALL result in a single consistent state
2. **Invariant Preservation**: FOR ALL profile settings, the values SHALL match the user's most recent update

---

### Requirement 11: Error Handling and Recovery

**User Story:** As a user, I want Zefirka to handle errors gracefully and recover from failures, so that I can rely on the bot to work consistently.

#### Acceptance Criteria

1. WHEN an error occurs during message processing, THE Zefirka SHALL log the error with full context and stack trace
2. WHEN a GitHub synchronization fails, THE Zefirka SHALL retry with exponential backoff and notify the user if the failure persists
3. WHEN a Deepseek_AI request fails, THE Zefirka SHALL fall back to rule-based processing
4. WHEN a file operation fails, THE Zefirka SHALL restore from the most recent backup
5. IF a critical error occurs, THEN THE Zefirka SHALL send an error report to the user and suggest recovery steps
6. WHEN the bot recovers from an error, THE Zefirka SHALL resume normal operation without data loss

#### Property-Based Testing Criteria

1. **Idempotence**: Retrying a failed operation multiple times SHALL eventually succeed or fail consistently
2. **Invariant Preservation**: FOR ALL error recovery operations, the data integrity SHALL be maintained

---

### Requirement 12: Data Persistence and Backup

**User Story:** As a user, I want my data to be safely stored and backed up, so that I don't lose important information.

#### Acceptance Criteria

1. WHEN data is created or modified, THE Zefirka SHALL store it in Zefirka/tasks.md, Zefirka/finances.md, or Zefirka/projects.md
2. WHEN data is stored, THE Zefirka SHALL create a backup copy in the archive/ folder
3. WHEN a user requests data recovery, THE Zefirka SHALL restore data from the most recent backup
4. WHEN old data reaches 3 months (for tasks) or 6 months (for expenses), THE Zefirka SHALL automatically archive it
5. IF a data file becomes corrupted, THEN THE Zefirka SHALL restore from the most recent backup and notify the user
6. WHEN a user deletes data, THE Zefirka SHALL move it to archive/ instead of permanently deleting it

#### Property-Based Testing Criteria

1. **Idempotence**: Creating multiple backups of the same data SHALL result in identical backup copies
2. **Round-Trip Consistency**: FOR ALL archived data, restoring and re-archiving SHALL produce equivalent data

---

## Constraints

### Technical Constraints
- The system MUST use Python 3.9 or higher
- The system MUST use Telegram Bot API for user interface
- The system MUST use GitHub API for data synchronization
- The system MUST use Deepseek API for AI analysis
- The system MUST store data in JSON format compatible with Obsidian
- The system MUST support only Ukrainian, Russian, and English languages
- The system MUST process messages within 10 seconds
- The system MUST process commands within 5 seconds

### Data Constraints
- Maximum task count: 1000 per user
- Maximum expense count: 10000 per user
- Maximum project count: 100 per user
- Maximum conversation history: 24 hours
- Maximum file size: 10 MB per data file
- Minimum monthly budget: 100 UAH
- Maximum monthly budget: 1000000 UAH

### Operational Constraints
- The system MUST maintain 99% uptime
- The system MUST retry failed operations up to 3 times
- The system MUST use exponential backoff for retries
- The system MUST encrypt sensitive data at rest
- The system MUST log all operations for audit purposes
- The system MUST comply with GDPR data protection requirements

### User Constraints
- The system MUST support only one user per bot instance
- The system MUST require GitHub authentication for data synchronization
- The system MUST require Deepseek API key for AI features
- The system MUST require Telegram bot token for operation

---

## Dependencies

### External Services
- **Telegram Bot API**: For user interface and message handling
- **GitHub API**: For data synchronization and version control
- **Deepseek API**: For AI analysis and intent detection
- **Obsidian**: For local vault storage (user-managed)

### Python Libraries
- `python-telegram-bot`: Telegram bot framework
- `PyGithub`: GitHub API client
- `requests`: HTTP client for API calls
- `python-dotenv`: Environment variable management
- `pydantic`: Data validation
- `aiohttp`: Async HTTP client

### Internal Components
- `config.py`: Configuration management
- `logger.py`: Logging setup
- `services/github_service.py`: GitHub integration
- `services/deepseek_service.py`: AI integration
- `services/vault_service.py`: Obsidian Vault operations
- `services/memory_service.py`: Conversation history management
- `services/router_service.py`: Smart routing logic
- `handlers/command_handler.py`: Command processing
- `handlers/message_handler.py`: Message processing
- `bot.py`: Main bot orchestration

### Data Files
- `Zefirka/tasks.md`: Task storage
- `Zefirka/finances.md`: Expense storage
- `Zefirka/projects.md`: Project storage
- `Zefirka/user_profile.md`: User preferences
- `Zefirka/daily_notes/`: Daily summaries
- `Zefirka/archive/`: Archived data

---

## Acceptance Criteria Summary

This requirements document defines 12 major requirements with 72 acceptance criteria and 36 property-based testing criteria. All requirements follow EARS patterns and comply with INCOSE quality rules. The system is designed to provide intelligent, context-aware assistance while maintaining data integrity and user privacy.

