"""Vault Scanner — pure file listing, no content reads"""

from typing import Optional
from datetime import datetime

from src.services.github_service import GitHubService
from src.config import get_config
from src.logger import setup_logger

logger = setup_logger(__name__)
config = get_config()


class VaultScanner:
    """Scans vault folder structure — no file content is ever read here"""

    def __init__(self):
        self.github = GitHubService()
        self._cache: Optional[dict] = None
        self._cache_time: Optional[datetime] = None
        self.cache_ttl = getattr(config, "VAULT_CACHE_TTL", 300)

    def get_structure(self, force: bool = False) -> dict:
        now = datetime.now()
        if not force and self._cache and self._cache_time:
            if (now - self._cache_time).total_seconds() < self.cache_ttl:
                return self._cache
        logger.info("Scanning vault...")
        items = self.github.list_folder("")
        folders = {}
        if items:
            for item in items:
                name = item["name"]
                if name.startswith(".") or item["type"] != "dir":
                    continue
                folders[name] = self._scan_folder(name)
        self._cache = {"folders": folders, "scanned_at": now.isoformat()}
        self._cache_time = now
        logger.info(f"Vault: {len(folders)} folders")
        return self._cache

    def _scan_folder(self, path: str) -> dict:
        items = self.github.list_folder(path)
        files, dirs = [], []
        if items:
            for item in items:
                name = item["name"]
                if name.startswith("."):
                    continue
                if item["type"] == "dir":
                    dirs.append(name)
                elif item["type"] == "file":
                    files.append(name)
        return {"files": sorted(files), "dirs": sorted(dirs)}

    def invalidate_cache(self):
        self._cache = self._cache_time = None

    def get_context_for_ai(self) -> str:
        """Pure folder/file listing — no content, no pre-reads"""
        struct = self.get_structure()
        lines = ["=== VAULT STRUCTURE ==="]
        for fname, info in struct.get("folders", {}).items():
            lines.append(f"\n📁 {fname}/")
            for f in info.get("files", [])[:12]:
                lines.append(f"   📄 {f}")
            for d in info.get("dirs", [])[:6]:
                lines.append(f"   📁 {d}/")
        if len(lines) == 1:
            lines.append("\n(Vault is empty — you can create anything)")
        return "\n".join(lines)
