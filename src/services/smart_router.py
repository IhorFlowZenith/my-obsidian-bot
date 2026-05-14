"""Smart Router - purely descriptive, no hardcoded rules"""

from src.services.vault_scanner import VaultScanner
from src.logger import setup_logger

logger = setup_logger(__name__)


class SmartRouter:
    """Provides vault structure to AI — AI decides everything itself"""

    def __init__(self):
        self.scanner = VaultScanner()

    def get_routing_guide(self) -> str:
        """Just the raw vault structure — no rules, no hints, no SKILL.md"""
        return self.scanner.get_context_for_ai()
