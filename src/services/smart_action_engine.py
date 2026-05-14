"""Smart Action Engine — executes AI decisions on the vault"""

from typing import Tuple
from datetime import datetime
import requests

from src.services.github_service import GitHubService
from src.services.search_service import SearchService
from src.services.weather_service import WeatherService
from src.config import get_config
from src.logger import setup_logger

logger = setup_logger(__name__)
config = get_config()


class SmartActionEngine:
    """Executes AI decisions on vault files"""

    def __init__(self):
        self.github = GitHubService()

    def execute(self, decision: dict) -> Tuple[bool, str]:
        action = decision.get("action", "query")
        data = decision.get("data", {})
        target = decision.get("target", {})
        folder = target.get("folder", "Zefirka")
        filename = target.get("filename", "note.md")
        write_mode = target.get("write_mode", "append_section")

        if action == "add_task":
            return self._append_task(data, folder, filename)
        elif action == "add_expense":
            return self._append_expense(data)
        elif action == "add_project":
            return self._append_project(data)
        elif action == "set_reminder":
            return self._add_reminder(data)
        elif action in ("write_note", "create_file"):
            return self._write_or_append(data, folder, filename, write_mode)
        elif action == "complete_task":
            return self._complete_task(data, folder, filename)
        elif action == "read_file":
            return self._read_file(data, folder, filename)
        elif action == "delete_file":
            return self._delete_file(data, folder, filename)
        elif action == "edit_task":
            return self._edit_task(data, folder, filename)
        elif action == "delete_task":
            return self._delete_task(data, folder, filename)
        elif action == "delete_expense":
            return self._delete_expense(data)
        elif action == "delete_reminder":
            return self._delete_reminder(data)
        elif action == "update_progress":
            return self._update_progress(data)
        elif action == "log_mood":
            return self._log_mood(data)
        elif action == "search":
            return self._search(data)
        elif action == "get_weather":
            return self._get_weather()
        elif action == "fetch_url":
            return self._fetch_url(data)
        elif action == "update_content":
            return self._update_content(data, folder, filename)
        else:
            return True, decision.get("response", "OK")

    def _append_task(self, data: dict, folder: str, filename: str) -> Tuple[bool, str]:
        title = data.get("title", "Untitled")
        priority = data.get("priority", "normal")
        file_path = f"{folder}/{filename}"

        content = self.github.read_file_content(file_path)
        if not content:
            content = "# Tasks\n\n## Active Tasks\n\n### Urgent\n\n### Important\n\n### Normal\n\n## Completed\n"

        cap = priority.capitalize()
        section = f"### {cap}"
        task_line = f"- [ ] {title}"

        if section in content:
            content = content.replace(section, f"{section}\n{task_line}")
        else:
            content = content.rstrip() + f"\n\n{section}\n{task_line}\n"

        sha = (self.github.get_file(file_path) or {}).get("sha")
        ok = self.github.create_or_update_file(file_path, content, f"Task: {title}", sha=sha)
        return (True, f"✅ Task added: {title} ({priority})") if ok else (False, "❌ Task failed")

    def _append_expense(self, data: dict) -> Tuple[bool, str]:
        title = data.get("title", "Expense")
        amount = data.get("amount", 0)
        category = data.get("category", "other")
        file_path = "Zefirka/finances.md"

        content = self.github.read_file_content(file_path)
        if not content:
            content = "# Finances\n\n| Date | Category | Amount | Description |\n|------|----------|--------|-------------|\n"

        today = datetime.now().strftime("%Y-%m-%d")
        row = f"| {today} | {category} | {amount} | {title} |"
        if "| Date |" in content:
            content = content.replace("| Date |", f"| Date |\n{row}")
        else:
            content = content.rstrip() + f"\n{row}\n"

        sha = (self.github.get_file(file_path) or {}).get("sha")
        ok = self.github.create_or_update_file(file_path, content, f"Expense: {amount} UAH", sha=sha)
        return (True, f"💰 {amount} UAH — {title}") if ok else (False, "❌ Expense failed")

    def _append_project(self, data: dict) -> Tuple[bool, str]:
        title = data.get("title", "Project")
        desc = data.get("description", "")
        file_path = "Zefirka/projects.md"

        content = self.github.read_file_content(file_path)
        if not content:
            content = "# Projects\n\n## Active Projects\n\n## Ideas\n"

        entry = f"\n### {title}\n- **Status:** Planning\n- **Description:** {desc}\n"
        if "## Active Projects" in content:
            content = content.replace("## Active Projects", f"## Active Projects{entry}")
        else:
            content = content.rstrip() + entry

        sha = (self.github.get_file(file_path) or {}).get("sha")
        ok = self.github.create_or_update_file(file_path, content, f"Project: {title}", sha=sha)
        return (True, f"🚀 Project: {title}") if ok else (False, "❌ Project failed")

    def _add_reminder(self, data: dict) -> Tuple[bool, str]:
        title = data.get("title", "Reminder")
        rem_time = data.get("time", "")
        rem_date = data.get("date", "")
        file_path = "Zefirka/reminders.md"

        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        # Parse relative dates
        if rem_date:
            rem_date_lower = rem_date.strip().lower()
            if rem_date_lower in ("today", "сьогодні", "сегодня", ""):
                rem_date = today
            elif rem_date_lower in ("tomorrow", "завтра", "tomorrow"):
                from datetime import timedelta
                rem_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            elif rem_date_lower in ("day after tomorrow", "післязавтра"):
                from datetime import timedelta
                rem_date = (now + timedelta(days=2)).strftime("%Y-%m-%d")
            elif rem_date_lower.startswith("+") and rem_date_lower[1:].isdigit():
                from datetime import timedelta
                days = int(rem_date_lower[1:])
                rem_date = (now + timedelta(days=days)).strftime("%Y-%m-%d")
            # else: keep as-is (e.g. "2026-05-22")

        if not rem_date:
            rem_date = today

        if rem_date and rem_time:
            dt_str = f"{rem_date} {rem_time}"
        elif rem_time:
            dt_str = f"{today} {rem_time}"
        else:
            dt_str = now.strftime("%Y-%m-%d %H:%M")

        try:
            dt_parsed = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except ValueError:
            return False, f"❌ Неправильний формат: {dt_str}. Використовуй: YYYY-MM-DD HH:MM"

        if dt_parsed < now:
            from datetime import timedelta
            tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            tomorrow_str = f"{tomorrow} {rem_time}" if rem_time else tomorrow
            return False, (
                f"⏰ Час {dt_parsed.strftime('%H:%M')} вже пройшов. "
                f"Поставити на завтра ({tomorrow_str})? Напиши 'так' або вкажи інший час."
            )

        content = self.github.read_file_content(file_path)
        if not content:
            content = "# Reminders\n\n## Pending\n\n## Sent\n"

        if "## Pending" in content:
            content = content.replace("## Pending", f"## Pending\n- [ ] {dt_str} | {title}")
        else:
            content = content.rstrip() + f"\n\n## Pending\n- [ ] {dt_str} | {title}\n"

        sha = (self.github.get_file(file_path) or {}).get("sha")
        ok = self.github.create_or_update_file(file_path, content, f"Reminder: {title}", sha=sha)
        return (True, f"🔔 Reminder set: {title} at {dt_str}") if ok else (False, "❌ Reminder failed")

    def _write_or_append(self, data: dict, folder: str, filename: str, mode: str) -> Tuple[bool, str]:
        file_path = f"{folder}/{filename}"
        title = data.get("title", "Note")
        body = data.get("description", "")

        existing = self.github.read_file_content(file_path)
        sha = (self.github.get_file(file_path) or {}).get("sha")

        if existing and mode in ("append_section", "append_table"):
            new = f"\n\n---\n### {title}\n\n{body}\n\n*Added {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
            content = existing.rstrip() + new
            msg = f"Updated: {filename}"
        elif existing and mode == "overwrite":
            content = f"# {title}\n\n{body}\n\n---\n*Updated {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
            msg = f"Overwritten: {filename}"
        else:
            content = f"# {title}\n\n{body}\n\n---\n*Created {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
            msg = f"Created: {filename}"

        ok = self.github.create_or_update_file(file_path, content, msg, sha=sha)
        return (True, f"📝 {file_path} saved") if ok else (False, f"❌ {file_path} failed")

    def _update_content(self, data: dict, folder: str, filename: str) -> Tuple[bool, str]:
        file_path = f"{folder}/{filename}"
        content = self.github.read_file_content(file_path)
        if not content:
            return False, "❌ File not found"

        old = data.get("old_text", "")
        new = data.get("new_text", "")
        if old:
            content = content.replace(old, new, 1)
        else:
            content = content.rstrip() + f"\n{new}\n"

        sha = (self.github.get_file(file_path) or {}).get("sha")
        ok = self.github.create_or_update_file(file_path, content, f"Updated: {filename}", sha=sha)
        return (True, f"✅ {filename} updated") if ok else (False, "❌ Update failed")

    def _complete_task(self, data: dict, folder: str, filename: str) -> Tuple[bool, str]:
        title = data.get("title", "")
        file_path = f"{folder}/{filename}"
        content = self.github.read_file_content(file_path)
        if not content:
            return False, "❌ File not found"

        lines = content.split("\n")
        found = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("- [ ]") and title.lower() in stripped.lower():
                lines[i] = line.replace("- [ ]", "- [x]", 1)
                found = True
                break

        if not found:
            return False, f"❌ Не знайдено задачу: {title}"

        sha = (self.github.get_file(file_path) or {}).get("sha")
        new_content = "\n".join(lines)
        ok = self.github.create_or_update_file(file_path, new_content, f"Completed: {title}", sha=sha)
        return (True, f"✅ Task completed: {title}") if ok else (False, "❌ Failed to complete task")

    def _read_file(self, data: dict, folder: str, filename: str) -> Tuple[bool, str]:
        file_path = f"{folder}/{filename}"
        content = self.github.read_file_content(file_path)
        if not content:
            return False, f"❌ File not found: {file_path}"
        return True, f"__FILE_CONTENT__:{file_path}:{content}"

    def _edit_task(self, data: dict, folder: str, filename: str) -> Tuple[bool, str]:
        title = data.get("title", "")
        new_priority = data.get("priority", "")
        file_path = f"{folder}/{filename}"
        content = self.github.read_file_content(file_path)
        if not content:
            return False, "❌ File not found"

        lines = content.split("\n")
        found = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("- [") and title.lower() in stripped.lower():
                if new_priority:
                    for old_section in ["### Urgent", "### Important", "### Normal"]:
                        if old_section in lines:
                            lines[i] = line.replace(stripped, f"- [ ] {title}")
                            lines.insert(lines.index(old_section) + 1, lines.pop(i))
                    found = True
                    break
                found = True
                break

        if not found:
            return False, f"❌ Task not found: {title}"

        sha = (self.github.get_file(file_path) or {}).get("sha")
        ok = self.github.create_or_update_file(file_path, "\n".join(lines), f"Edited: {title}", sha=sha)
        return (True, f"✅ Task edited: {title}") if ok else (False, "❌ Edit failed")

    def _delete_task(self, data: dict, folder: str, filename: str) -> Tuple[bool, str]:
        if not data.get("confirmed"):
            return False, "⚠️ Ти впевнений? Напиши 'так, видали' або 'підтверджую'"
        title = data.get("title", "")
        file_path = f"{folder}/{filename}"
        content = self.github.read_file_content(file_path)
        if not content:
            return False, "❌ File not found"

        lines = content.split("\n")
        new_lines = []
        found = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("- [") and title.lower() in stripped.lower():
                found = True
                continue
            new_lines.append(line)

        if not found:
            return False, f"❌ Task not found: {title}"

        sha = (self.github.get_file(file_path) or {}).get("sha")
        ok = self.github.create_or_update_file(file_path, "\n".join(new_lines), f"Deleted: {title}", sha=sha)
        return (True, f"🗑 Task deleted: {title}") if ok else (False, "❌ Delete failed")

    def _delete_expense(self, data: dict) -> Tuple[bool, str]:
        if not data.get("confirmed"):
            return False, "⚠️ Ти впевнений? Напиши 'так' для підтвердження"
        title = data.get("title", "")
        file_path = "Zefirka/finances.md"
        content = self.github.read_file_content(file_path)
        if not content:
            return False, "❌ File not found"

        lines = content.split("\n")
        new_lines = []
        found = False
        for line in lines:
            if title.lower() in line.lower() and line.strip().startswith("|"):
                found = True
                continue
            new_lines.append(line)

        if not found:
            return False, f"❌ Expense not found: {title}"

        sha = (self.github.get_file(file_path) or {}).get("sha")
        ok = self.github.create_or_update_file(file_path, "\n".join(new_lines), f"Deleted expense: {title}", sha=sha)
        return (True, f"🗑 Expense deleted: {title}") if ok else (False, "❌ Delete failed")

    def _delete_reminder(self, data: dict) -> Tuple[bool, str]:
        if not data.get("confirmed"):
            return False, "⚠️ Ти впевнений? Напиши 'так' для підтвердження"
        title = data.get("title", "")
        file_path = "Zefirka/reminders.md"
        content = self.github.read_file_content(file_path)
        if not content:
            return False, "❌ File not found"

        lines = content.split("\n")
        new_lines = []
        found = False
        for line in lines:
            if title.lower() in line.lower() and line.strip().startswith("- ["):
                found = True
                continue
            new_lines.append(line)

        if not found:
            return False, f"❌ Reminder not found: {title}"

        sha = (self.github.get_file(file_path) or {}).get("sha")
        ok = self.github.create_or_update_file(file_path, "\n".join(new_lines), f"Deleted reminder: {title}", sha=sha)
        return (True, f"🗑 Reminder deleted: {title}") if ok else (False, "❌ Delete failed")

    def _update_progress(self, data: dict) -> Tuple[bool, str]:
        title = data.get("title", "")
        progress = data.get("progress", "")
        description = data.get("description", "")
        file_path = "Zefirka/projects.md"
        content = self.github.read_file_content(file_path)
        if not content:
            return False, "❌ File not found"

        lines = content.split("\n")
        found = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("###") and title.lower() in stripped.lower():
                found = True
                if progress:
                    for j in range(i, min(i + 10, len(lines))):
                        if lines[j].strip().startswith("- **Progress:**"):
                            lines[j] = f"- **Progress:** {progress}%"
                if description:
                    for j in range(i, min(i + 10, len(lines))):
                        if lines[j].strip().startswith("- **Description:**"):
                            lines[j] = f"- **Description:** {description}"
                            break
                    else:
                        lines.insert(i + 3, f"- **Description:** {description}")
                break

        if not found:
            return False, f"❌ Project not found: {title}"

        sha = (self.github.get_file(file_path) or {}).get("sha")
        ok = self.github.create_or_update_file(file_path, "\n".join(lines), f"Updated: {title}", sha=sha)
        return (True, f"📊 Project updated: {title} ({progress}%)") if ok else (False, "❌ Update failed")

    def _log_mood(self, data: dict) -> Tuple[bool, str]:
        mood = data.get("mood", "neutral")
        note = data.get("description", "")
        file_path = "Zefirka/daily_plans.md"
        today = datetime.now().strftime("%Y-%m-%d")

        content = self.github.read_file_content(file_path)
        entry = f"\n| {today} | {mood} | {note} |\n"

        if content and "## Mood Log" in content:
            content = content.replace("## Mood Log", f"## Mood Log{entry}")
        elif content:
            content = content.rstrip() + f"\n\n## Mood Log\n| Date | Mood | Note |\n|------|------|------|{entry}"
        else:
            content = f"# Daily Plans\n\n## Mood Log\n| Date | Mood | Note |\n|------|------|------|{entry}"

        sha = (self.github.get_file(file_path) or {}).get("sha")
        ok = self.github.create_or_update_file(file_path, content, f"Mood: {mood}", sha=sha)
        return (True, f"😊 Mood logged: {mood}") if ok else (False, "❌ Mood log failed")

    def _search(self, data: dict) -> Tuple[bool, str]:
        query = data.get("query", data.get("title", ""))
        if not query:
            return False, "❌ Немає запиту для пошуку"
        searcher = SearchService()
        result = searcher.search_formatted(query)
        return True, result

    def _get_weather(self) -> Tuple[bool, str]:
        w = WeatherService()
        text = w.get_weather_text()
        if text:
            return True, text
        return False, "❌ Не вдалося отримати погоду"

    def _fetch_url(self, data: dict) -> Tuple[bool, str]:
        url = data.get("url", data.get("description", ""))
        if not url:
            return False, "❌ Немає URL для читання"
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "ZefirkaBot/1.0"})
            if resp.status_code != 200:
                return False, f"❌ HTTP {resp.status_code} для {url}"
            text = resp.text[:4000]
            return True, f"__URL_CONTENT__:{url}:{text}"
        except Exception as e:
            return False, f"❌ Помилка читання {url}: {e}"

    def _delete_file(self, data: dict, folder: str, filename: str) -> Tuple[bool, str]:
        file_path = f"{folder}/{filename}"
        if not data.get("confirmed"):
            return False, "⚠️ Ти впевнений? Це незворотна дія. Напиши 'так' для підтвердження."

        file_data = self.github.get_file(file_path)
        if not file_data:
            return False, "❌ File not found"

        # If it's a directory, delete all files inside
        if isinstance(file_data, list):
            deleted = 0
            for item in file_data:
                if item["type"] == "file":
                    self.github.delete_file(
                        f"{file_path}/{item['name']}",
                        f"Deleted: {item['name']}",
                        item["sha"],
                    )
                    deleted += 1
            return True, f"🗑 Папка '{file_path}' видалена ({deleted} файлів)"

        # Regular file
        sha = file_data.get("sha")
        ok = self.github.delete_file(file_path, f"Deleted: {filename}", sha)
        return (True, f"🗑 Deleted: {file_path}") if ok else (False, "❌ Delete failed")
