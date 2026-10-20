"""Shared external research module (keyless web search + extraction)."""

from ai.shared.research.research_bundle import ResearchBundle
from ai.shared.research.research_manager import ResearchManager
from ai.shared.research.research_provider import BaseResearchProvider
from ai.shared.research.web_provider import WebResearchProvider

__all__ = [
    "ResearchBundle",
    "BaseResearchProvider",
    "WebResearchProvider",
    "ResearchManager",
]
