"""Search Service — search across all vault files"""

from typing import List, Tuple

from src.services.github_service import GitHubService
from src.services.vault_scanner import VaultScanner
from src.logger import setup_logger

logger = setup_logger(__name__)


class SearchService:
    """Search for keywords in all vault files"""

    def __init__(self):
        self.github = GitHubService()
        self.scanner = VaultScanner()

    def search(self, keyword: str, max_results: int = 5) -> List[Tuple[str, str, int]]:
        """Search keyword in all files. Returns [(filepath, context_line, line_number), ...]"""
        keyword_lower = keyword.lower()
        results = []
        all_files = self._collect_files()

        for filepath in all_files:
            content = self.github.read_file_content(filepath)
            if not content:
                continue
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if keyword_lower in line.lower():
                    context = line.strip()[:150]
                    results.append((filepath, context, i + 1))
                    if len(results) >= max_results:
                        return results
        return results

    def search_formatted(self, keyword: str) -> str:
        """Search and return formatted result string"""
        results = self.search(keyword)
        if not results:
            return f"🔍 Нічого не знайдено за запитом: {keyword}"

        lines = [f"🔍 Результати пошуку: <b>{keyword}</b>\n"]
        for filepath, context, line_num in results:
            lines.append(f"📄 <b>{filepath}</b> (рядок {line_num}):")
            lines.append(f"   <code>{context}</code>\n")
        return "\n".join(lines)

    def _collect_files(self) -> List[str]:
        """Collect all file paths from vault structure"""
        struct = self.scanner.get_structure()
        files = []
        for fname, info in struct.get("folders", {}).items():
            for f in info.get("files", []):
                files.append(f"{fname}/{f}")
        return files
