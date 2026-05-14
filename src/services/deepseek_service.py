"""Deepseek AI Service - fully autonomous decision engine"""

import json
from typing import Dict, Any, Optional, List
import requests

from src.config import get_config
from src.logger import setup_logger

logger = setup_logger(__name__)
config = get_config()


class DeepseekService:
    """Calls Deepseek API — AI decides everything itself"""

    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.api_url = config.DEEPSEEK_API_URL
        self.model = config.DEEPSEEK_MODEL
        self.timeout = config.DEEPSEEK_TIMEOUT
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def analyze_request(
        self,
        user_message: str,
        vault_context: str,
        conversation_context: str,
        language: str = "uk"
    ) -> Dict[str, Any]:
        """AI decides everything: action, target, content"""

        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        system_prompt = f"""You are Zefirka, an autonomous AI assistant that manages an Obsidian vault.

You decide EVERYTHING yourself:
- What action to take
- Which folder to use
- What filename to create/update
- What content to write
- How to format it

Current time: {current_date}

=== VAULT STRUCTURE ===
{vault_context}

=== CONVERSATION ===
{conversation_context}

=== AVAILABLE ACTIONS ===
1. "add_task" — add a task to Zefirka/tasks.md
2. "add_expense" — add an expense to Zefirka/finances.md  
3. "add_project" — add a project to Zefirka/projects.md
4. "set_reminder" — set a reminder. data: title, time, date (optional)
5. "complete_task" — mark task done. target: folder=Zefirka, filename=tasks.md. data: title
6. "edit_task" — edit task priority. data: title, priority (urgent|important|normal)
7. "delete_task" — delete a task. data: title. FIRST ask confirmation via "query"!
8. "delete_expense" — delete an expense. data: title. Ask confirmation first!
9. "delete_reminder" — delete a reminder. data: title. Ask confirmation first!
10. "update_progress" — update project progress. data: title, progress (0-100), description (optional)
11. "log_mood" — log mood. data: mood (good|neutral|bad), description
12. "read_file" — read file for analysis. target: folder, filename
13. "write_note" — APPEND to existing file or create new
14. "create_file" — create a brand new file in the best folder
15. "update_content" — replace specific text in a file
16. "delete_file" — delete file. ALWAYS ask confirmation first!
17. "query" — answer a question (no file changes)
18. "get_weather" — get current weather for your city
19. "reflection" — ask about the user's day
20. "search" — search vault. data: query (search keyword)
21. "fetch_url" — fetch a URL and return its content for summarization. data: url
22. "help" — show help

=== WRITE MODES ===
- "append_section" — add new section to existing file (default)
- "append_table" — add a row to an existing table  
- "overwrite" — replace entire file content
- "create_file" — only if file doesn't exist yet

=== CRITICAL: action = "query" IS FOR CASUAL CHAT ONLY ===
Do NOT use "query" when the user asks about their DATA (tasks, reminders, finances, projects).
When user asks about data → ALWAYS use "read_file" to read the file, then analyze it.

Examples:
- "В мене є нагадування?" → read_file Zefirka/reminders.md
- "Які задачі?" → read_file Zefirka/tasks.md
- "Що заплановано?" → read_file reminders.md + tasks.md
- "Покажи бюджет" → read_file Zefirka/finances.md
- "Привіт" → query (casual chat, no data needed)
- "Як справи?" → query

=== RULES ===
- Current date: {current_date}. Use this for calculating relative dates.
- Use language: {language}. Always respond in this language.
- You see only file NAMES, not contents. Use read_file/search to read content.
- If user wants to see ANY stored data → use "read_file"
- If user wants to ADD/CREATE → use add_task / add_expense / set_reminder / write_note
- If user wants to CHANGE → use complete_task / edit_task / update_progress
- If user wants to DELETE a REMINDER → use "delete_reminder" (NOT delete_file)
- If user wants to DELETE a TASK → use "delete_task" (NOT delete_file)
- If user wants to DELETE an EXPENSE → use "delete_expense" (NOT delete_file)
- If user wants to DELETE an ENTIRE FILE → use "delete_file"
- If user wants to DELETE an ENTIRE FOLDER → use "delete_file" with target folder and filename="*" (engine handles it)
- delete_file also works for folders: set target.folder="Zefirka", target.filename="Коледж"
- For ALL deletes: use "query" to ask confirmation first, then set confirmed=true
- If user has a URL → "fetch_url"
- If casual chat (hello, greetings, opinions) → "query"

=== RESPONSE FORMAT (JSON ONLY) ===
{{
    "action": "<action>",
    "data": {{
        "title": "Short title",
        "description": "Content or details",
        "priority": "urgent|important|normal",
        "category": "work|study|personal|project|food|transport|entertainment|shopping|other",
        "amount": 0,
        "time": "HH:MM (for reminders)",
        "date": "YYYY-MM-DD (for reminders, optional)",
        "old_text": "exact text to replace (for update_content)",
        "new_text": "replacement text (for update_content)"
    }},
    "target": {{
        "folder": "Zefirka",
        "filename": "tasks.md",
        "write_mode": "append_section|append_table|create_file|overwrite"
    }},
    "response": "Your response to user in {language}",
    "reasoning": "Brief explanation of your decision"
}}"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        try:
            resp = requests.post(self.api_url, headers=self.headers, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                logger.error(f"API error {resp.status_code}: {resp.text[:200]}")
                return self._error("API error")

            raw = resp.json()["choices"][0]["message"]["content"]
            return self._parse(raw, user_message)

        except requests.Timeout:
            logger.error("API timeout")
            return self._error("API timeout")
        except Exception as e:
            logger.error(f"Error: {e}")
            return self._error(str(e))

    def _parse(self, raw: Optional[str], fallback_msg: str) -> dict:
        if not raw or not isinstance(raw, str):
            logger.warning(f"AI returned non-string: {type(raw).__name__}")
            return self._fallback(fallback_msg)

        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start == -1 or end <= start:
                logger.warning(f"No JSON in AI response: {raw[:200]}")
                return self._fallback(raw[:500])

            parsed = json.loads(raw[start:end])
            if not isinstance(parsed, dict):
                logger.warning(f"AI returned non-dict JSON: {type(parsed).__name__}")
                return self._fallback(str(parsed)[:500])

            logger.info(f"AI: {parsed.get('action', '?')} -> {parsed.get('target', {}).get('filename', '?')}")
            return parsed

        except json.JSONDecodeError:
            logger.warning(f"JSON parse failed on: {raw[:200]}")
            return self._fallback(raw[:500])

    def _fallback(self, text: str) -> dict:
        return {
            "action": "query", "data": {},
            "target": {"folder": "Zefirka", "filename": "notes.md"},
            "response": text, "reasoning": "fallback_parse",
        }

    def _error(self, msg: str) -> dict:
        return {"action": "error", "data": {}, "target": {}, "response": f"❌ {msg}", "reasoning": "error"}
