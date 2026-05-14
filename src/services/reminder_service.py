"""Reminder Service — checks reminders.md and marks sent reminders as [x]"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from src.services.github_service import GitHubService
from src.logger import setup_logger

logger = setup_logger(__name__)
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
STATE_FILE = os.path.join(DATA_DIR, "scheduler_state.json")


class ReminderService:
    def __init__(self):
        self.github = GitHubService()

    def check(self) -> List[str]:
        content = self.github.read_file_content("Zefirka/reminders.md")
        if not content:
            return []

        reminders = self._parse(content)
        now = datetime.now()
        window_start = now - timedelta(seconds=90)
        sent_ids = self._load_sent_ids()
        messages = []
        lines_to_mark = []  # (line_index_in_original_file, new_line_text)

        lines = content.split("\n")
        for r in reminders:
            rid = r["id"]
            if rid in sent_ids:
                continue
            if window_start <= r["dt"] <= now:
                messages.append(f"🔔 Нагадування: {r['text']}")
                sent_ids.add(rid)
                lines_to_mark.append(r["line"])
                logger.info(f"Reminder triggered: {r['text']}")

        # Update reminders.md: mark [ ] → [x] for fired reminders
        if lines_to_mark:
            for idx in lines_to_mark:
                if idx < len(lines):
                    lines[idx] = lines[idx].replace("- [ ]", "- [x]", 1)
            sha = (self.github.get_file("Zefirka/reminders.md") or {}).get("sha")
            self.github.create_or_update_file(
                "Zefirka/reminders.md",
                "\n".join(lines),
                f"Marked {len(lines_to_mark)} reminder(s) as sent",
                sha=sha,
            )

        self._save_sent_ids(sent_ids)
        return messages

    def _parse(self, content: str) -> List[Dict]:
        """Parse reminders.md. Returns list with id, dt, text, line (index)"""
        reminders = []
        in_pending = False
        lines = content.split("\n")

        for i, line in enumerate(lines):
            stripped = line.strip()

            if "## Pending" in stripped:
                in_pending = True
                continue
            if stripped.startswith("##") and "Pending" not in stripped:
                in_pending = False
                continue

            if not in_pending or not stripped.startswith("- [ ]"):
                continue

            text = stripped[5:].strip()
            match = re.match(
                r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s*[|\-]\s*(.+)",
                text,
            )
            if match:
                dt_str = f"{match.group(1)} {match.group(2)}"
                reminder_text = match.group(3)
            else:
                match2 = re.match(r"(\d{2}:\d{2})\s+(.+)", text)
                if match2:
                    today = datetime.now().strftime("%Y-%m-%d")
                    dt_str = f"{today} {match2.group(1)}"
                    reminder_text = match2.group(2)
                else:
                    continue

            try:
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            except ValueError:
                continue

            reminders.append({
                "id": dt_str + "|" + reminder_text,
                "dt": dt,
                "text": reminder_text,
                "line": i,
            })

        return reminders

    def _load_sent_ids(self) -> set:
        try:
            with open(STATE_FILE) as f:
                data = json.load(f)
            return set(data.get("sent_reminders", []))
        except (FileNotFoundError, json.JSONDecodeError):
            return set()

    def _save_sent_ids(self, ids: set):
        data = {}
        try:
            with open(STATE_FILE) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        data["sent_reminders"] = sorted(ids)
        with open(STATE_FILE, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
