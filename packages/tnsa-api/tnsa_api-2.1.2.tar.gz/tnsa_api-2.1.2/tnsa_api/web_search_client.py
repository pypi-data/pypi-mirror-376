"""
Web Search Client for TNSA API

Integrates web search capabilities with AI models for enhanced responses.
"""

from typing import Dict, List, Optional, Any, Union
import logging
from .tools.web_search import DuckDuckGoSearchTool, WebSearchError
from .config import Config
from .exceptions import TNSAError

logger = logging.getLogger(__name__)


class WebSearchClient:
    """
    Web search client that integrates with TNSA AI models.
    
    This client can automatically perform web searches when needed and
    integrate the results with AI model responses.
    """
    
    def __init__(self, config: Config):
        """
        Initialize web search client.
        
        Args:
            config: TNSA configuration object
        """
        self.config = config
        self._search_tool = None
        
        if not config.web_search_enabled:
            logger.info("Web search is disabled")
        else:
            logger.info("Web search is enabled")
    
    @property
    def search_tool(self) -> DuckDuckGoSearchTool:
        """Get or create the search tool instance."""
        if not self.config.web_search_enabled:
            raise TNSAError("Web search is disabled. Set TNSA_WEB_SEARCH_ENABLED=true to enable.")
        
        if self._search_tool is None:
            self._search_tool = DuckDuckGoSearchTool(
                timeout=self.config.web_search_timeout,
                max_retries=3
            )
        
        return self._search_tool
    
    def search(
        self, 
        query: str, 
        max_results: Optional[int] = None,
        include_related: bool = True,
        safe_search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform a web search.
        
        Args:
            query: Search query
            max_results: Maximum results (uses config default if None)
            include_related: Include related topics
            safe_search: Safe search setting (uses config default if None)
            
        Returns:
            Search results dictionary
        """
        if not self.config.web_search_enabled:
            raise TNSAError("Web search is disabled. Set TNSA_WEB_SEARCH_ENABLED=true to enable.")
        
        max_results = max_results or self.config.web_search_max_results
        safe_search = safe_search or self.config.web_search_safe_search
        
        try:
            return self.search_tool.search(
                query=query,
                max_results=max_results,
                include_related=include_related,
                safe_search=safe_search
            )
        except WebSearchError as e:
            logger.error(f"Web search failed: {e}")
            raise TNSAError(f"Web search failed: {str(e)}")
    
    def search_and_summarize(
        self, 
        query: str, 
        max_summary_length: int = 500,
        max_results: Optional[int] = None
    ) -> str:
        """
        Perform a web search and return a summary suitable for AI models.
        
        Args:
            query: Search query
            max_summary_length: Maximum summary length
            max_results: Maximum search results
            
        Returns:
            Formatted summary string
        """
        results = self.search(query, max_results=max_results)
        return self.search_tool.summarize_results(results, max_summary_length)
    
    def enhance_prompt_with_search(
        self, 
        prompt: str, 
        search_queries: List[str],
        max_summary_length: int = 300
    ) -> str:
        """
        Enhance a prompt with web search results.
        
        Args:
            prompt: Original prompt
            search_queries: List of search queries to perform
            max_summary_length: Maximum length for each search summary
            
        Returns:
            Enhanced prompt with search results
        """
        if not self.config.web_search_enabled:
            logger.warning("Web search is disabled, returning original prompt")
            return prompt
        
        if not search_queries:
            return prompt
        
        enhanced_parts = [prompt]
        enhanced_parts.append("\n--- Web Search Results ---")
        
        for i, query in enumerate(search_queries, 1):
            try:
                summary = self.search_and_summarize(
                    query, 
                    max_summary_length=max_summary_length
                )
                enhanced_parts.append(f"\nSearch {i}: {query}")
                enhanced_parts.append(summary)
            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {e}")
                enhanced_parts.append(f"\nSearch {i}: {query}")
                enhanced_parts.append("Search failed - no results available")
        
        enhanced_parts.append("\n--- End Search Results ---\n")
        enhanced_parts.append("Please use the above search results to provide a comprehensive and up-to-date response.")
        
        return "\n".join(enhanced_parts)
    
    def auto_search_from_prompt(
        self, 
        prompt: str, 
        keywords: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Automatically determine if a prompt needs web search and perform it.
        
        Args:
            prompt: User prompt to analyze
            keywords: Optional keywords that trigger search
            
        Returns:
            Enhanced prompt with search results, or None if no search needed
        """
        if not self.config.web_search_enabled:
            return None
        
        # Default keywords that suggest web search is needed
        default_keywords = [
            "latest", "recent", "current", "today", "news", "update",
            "what's new", "happening now", "breaking", "trending",
            "2024", "2025", "this year", "this month", "this week",
            "search for", "look up", "find information", "research"
        ]
        
        search_keywords = keywords or default_keywords
        prompt_lower = prompt.lower()
        
        # Check if prompt contains search-triggering keywords
        needs_search = any(keyword in prompt_lower for keyword in search_keywords)
        
        if not needs_search:
            return None
        
        # Extract potential search queries from the prompt
        # This is a simple implementation - could be enhanced with NLP
        search_queries = []
        
        # Look for question patterns
        if "what is" in prompt_lower or "what are" in prompt_lower:
            # Extract the subject after "what is/are"
            for phrase in ["what is", "what are"]:
                if phrase in prompt_lower:
                    start = prompt_lower.find(phrase) + len(phrase)
                    end = prompt_lower.find("?", start)
                    if end == -1:
                        end = len(prompt)
                    subject = prompt[start:end].strip()
                    if subject:
                        search_queries.append(subject)
        
        # Look for "tell me about" patterns
        if "tell me about" in prompt_lower:
            start = prompt_lower.find("tell me about") + len("tell me about")
            end = prompt_lower.find("?", start)
            if end == -1:
                end = len(prompt)
            subject = prompt[start:end].strip()
            if subject:
                search_queries.append(subject)
        
        # If no specific queries found, use the whole prompt as search
        if not search_queries:
            # Clean up the prompt for search
            search_query = prompt.replace("?", "").strip()
            if len(search_query) > 100:
                search_query = search_query[:100] + "..."
            search_queries.append(search_query)
        
        # Limit to 2 searches to avoid overwhelming the response
        search_queries = search_queries[:2]
        
        try:
            return self.enhance_prompt_with_search(prompt, search_queries)
        except Exception as e:
            logger.warning(f"Auto-search failed: {e}")
            return None
    
    def close(self):
        """Close the web search client and cleanup resources."""
        if self._search_tool:
            self._search_tool.close()
            self._search_tool = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()