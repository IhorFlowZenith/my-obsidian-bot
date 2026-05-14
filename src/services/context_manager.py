"""Context Manager - conversation history + action log"""

from typing import List, Dict, Any
from datetime import datetime

from src.logger import setup_logger

logger = setup_logger(__name__)


class ContextManager:
    """Manages conversation history and action log"""

    def __init__(self):
        self.history: List[Dict[str, str]] = []
        self.actions: List[Dict[str, Any]] = []

    def add_to_history(self, role: str, content: str):
        self.history.append({
            "role": role, "content": content, "time": datetime.now().isoformat(),
        })
        if len(self.history) > 30:
            self.history = self.history[-30:]

    def add_action(self, action: str, target: str, result: bool):
        self.actions.append({
            "action": action, "target": target, "ok": result, "time": datetime.now().isoformat(),
        })
        if len(self.actions) > 15:
            self.actions = self.actions[-15:]

    def get_conversation_context(self) -> str:
        lines = ["=== CONVERSATION ==="]
        for msg in self.history[-8:]:
            label = "User" if msg["role"] == "user" else "Bot"
            lines.append(f"{label}: {msg['content'][:300]}")
        return "\n".join(lines)

    def get_recent_topics(self) -> List[str]:
        return [m["content"][:100] for m in self.history[-6:] if m["role"] == "user"]
