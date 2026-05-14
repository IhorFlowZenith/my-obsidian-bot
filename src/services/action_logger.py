"""Action Logger — logs all bot actions to Zefirka/action_log.md"""

from datetime import datetime

from src.services.github_service import GitHubService
from src.logger import setup_logger

logger = setup_logger(__name__)


class ActionLogger:
    """Appends structured action logs to Zefirka/action_log.md"""

    def __init__(self):
        self.github = GitHubService()

    def log(self, action: str, target: str, success: bool, details: str = ""):
        """Log an action to the vault log file"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        status = "✅" if success else "❌"
        entry = f"| {now} | {status} | {action} | {target} | {details} |\n"

        content = self.github.read_file_content("Zefirka/action_log.md")
        if not content:
            content = (
                "# Action Log\n\n"
                "Автоматичний лог всіх дій бота.\n\n"
                "| Час | Статус | Дія | Ціль | Деталі |\n"
                "|------|--------|-----|------|--------|\n"
            )

        if "| Час | Статус |" in content:
            content = content.replace("| Час | Статус |", f"| Час | Статус |{entry}")
        else:
            content = content.rstrip() + f"\n{entry}"

        sha = (self.github.get_file("Zefirka/action_log.md") or {}).get("sha")
        self.github.create_or_update_file(
            "Zefirka/action_log.md",
            content,
            f"Action: {action} — {now}",
            sha=sha,
        )
        logger.debug(f"Logged action: {action} -> {target}")
