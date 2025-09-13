"""
TNSA API Tools Module

Global tools that can be enabled/disabled and integrated with AI models.
"""

from .web_search import (
    DuckDuckGoSearchTool,
    WebSearchError,
    web_search,
    web_search_summary,
    web_search_with_pages,
)

__all__ = [
    "DuckDuckGoSearchTool",
    "WebSearchError", 
    "web_search",
    "web_search_summary",
    "web_search_with_pages",
]