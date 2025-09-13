"""
Web Search Tool using DuckDuckGo API
"""

import requests
import json
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus
import time
import logging
from bs4 import BeautifulSoup
try:
    from readability import Document
except ImportError:
    Document = None
from io import BytesIO
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams

logger = logging.getLogger(__name__)


class WebSearchError(Exception):
    """Exception raised for web search errors."""
    pass


class DuckDuckGoSearchTool:
    """
    DuckDuckGo web search tool for TNSA API.
    
    This tool provides web search capabilities using DuckDuckGo's Instant Answer API
    and HTML search when needed.
    """
    
    def __init__(self, timeout: float = 10.0, max_retries: int = 3):
        """
        Initialize the web search tool.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TNSA-API-WebSearch/1.0 (https://tnsaai.com)'
        })
    
    def search(
        self, 
        query: str, 
        max_results: int = 10,
        include_related: bool = True,
        safe_search: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Perform a web search using DuckDuckGo.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            include_related: Whether to include related topics
            safe_search: Safe search setting ("strict", "moderate", "off")
            
        Returns:
            Dictionary containing search results
        """
        if not query or not query.strip():
            raise WebSearchError("Search query cannot be empty")
        
        query = query.strip()
        logger.info(f"Performing web search for: {query}")
        
        try:
            # First try DuckDuckGo Instant Answer API
            instant_results = self._search_instant_answer(query)
            
            # If no good instant answer, try HTML search
            if not instant_results.get("abstract") and not instant_results.get("related"):
                html_results = self._search_html(query, max_results, safe_search)
                instant_results.update(html_results)
            
            # Limit related topics if requested
            if include_related and instant_results.get("related"):
                instant_results["related"] = instant_results["related"][:max_results]
            elif not include_related:
                instant_results.pop("related", None)
            
            # Add metadata
            instant_results.update({
                "query": query,
                "timestamp": int(time.time()),
                "source": "duckduckgo",
                "total_results": len(instant_results.get("web_results", [])) + len(instant_results.get("related", []))
            })
            
            logger.info(f"Search completed. Found {instant_results['total_results']} results")
            return instant_results
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            raise WebSearchError(f"Search failed: {str(e)}")
    
    def _search_instant_answer(self, query: str) -> Dict[str, Any]:
        """Search using DuckDuckGo Instant Answer API."""
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "pretty": 1,
            "no_redirect": 1,
            "no_html": 1,
            "skip_disambig": 1
        }
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                
                # Extract relevant information
                result = {
                    "heading": data.get("Heading", ""),
                    "abstract": data.get("Abstract", ""),
                    "abstract_source": data.get("AbstractSource", ""),
                    "abstract_url": data.get("AbstractURL", ""),
                    "image": data.get("Image", ""),
                    "definition": data.get("Definition", ""),
                    "definition_source": data.get("DefinitionSource", ""),
                    "definition_url": data.get("DefinitionURL", ""),
                    "answer": data.get("Answer", ""),
                    "answer_type": data.get("AnswerType", ""),
                    "related": []
                }
                
                # Process related topics
                related_topics = data.get("RelatedTopics", [])
                for topic in related_topics:
                    if isinstance(topic, dict) and "Text" in topic:
                        related_item = {
                            "text": topic.get("Text", ""),
                            "url": topic.get("FirstURL", ""),
                            "icon": topic.get("Icon", {}).get("URL", "") if topic.get("Icon") else ""
                        }
                        if related_item["text"]:  # Only add if has text
                            result["related"].append(related_item)
                    elif isinstance(topic, dict) and "Topics" in topic:
                        # Handle nested topics
                        for subtopic in topic.get("Topics", []):
                            if isinstance(subtopic, dict) and "Text" in subtopic:
                                related_item = {
                                    "text": subtopic.get("Text", ""),
                                    "url": subtopic.get("FirstURL", ""),
                                    "icon": subtopic.get("Icon", {}).get("URL", "") if subtopic.get("Icon") else ""
                                }
                                if related_item["text"]:
                                    result["related"].append(related_item)
                
                return result
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Instant Answer API attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise WebSearchError(f"Instant Answer API failed after {self.max_retries} attempts")
                time.sleep(1 * (attempt + 1))  # Exponential backoff
        
        return {}
    
    def _search_html(self, query: str, max_results: int, safe_search: str) -> Dict[str, Any]:
        """Search using DuckDuckGo HTML search (fallback)."""
        # Note: This is a simplified implementation
        # In production, you might want to use a more robust HTML parsing approach
        
        url = "https://html.duckduckgo.com/html/"
        params = {
            "q": query,
            "s": "0",  # Start from result 0
            "dc": str(max_results),  # Number of results
            "v": "l",  # Layout
            "o": "json",  # Output format
            "api": "d.js"
        }
        
        # Set safe search
        if safe_search == "strict":
            params["safe"] = "strict"
        elif safe_search == "off":
            params["safe"] = "off"
        # moderate is default
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # For now, return empty results as HTML parsing would be complex
            # In a full implementation, you'd parse the HTML response
            return {
                "web_results": [],
                "note": "HTML search results parsing not implemented in this version"
            }
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"HTML search failed: {e}")
            return {"web_results": []}
    
    def summarize_results(self, search_results: Dict[str, Any], max_length: int = 500) -> str:
        """
        Create a summary of search results for AI model consumption.
        
        Args:
            search_results: Results from search() method
            max_length: Maximum length of summary
            
        Returns:
            Formatted summary string
        """
        summary_parts = []
        
        # Add query
        if search_results.get("query"):
            summary_parts.append(f"Search Query: {search_results['query']}")
        
        # Add main answer/definition
        if search_results.get("answer"):
            summary_parts.append(f"Answer: {search_results['answer']}")
        elif search_results.get("definition"):
            summary_parts.append(f"Definition: {search_results['definition']}")
        
        # Add abstract
        if search_results.get("abstract"):
            summary_parts.append(f"Summary: {search_results['abstract']}")
            if search_results.get("abstract_source"):
                summary_parts.append(f"Source: {search_results['abstract_source']}")
        
        # Add heading if available
        if search_results.get("heading") and search_results["heading"] != search_results.get("query", ""):
            summary_parts.append(f"Topic: {search_results['heading']}")
        
        # Add related topics
        related = search_results.get("related", [])
        if related:
            summary_parts.append("Related Information:")
            for i, item in enumerate(related[:5], 1):  # Limit to 5 related items
                if item.get("text"):
                    summary_parts.append(f"{i}. {item['text']}")
        
        # Join and truncate if needed
        summary = "\n".join(summary_parts)
        
        if len(summary) > max_length:
            summary = summary[:max_length - 3] + "..."
        
        return summary

    def fetch_url_text(self, url: str, max_chars: int = 8000) -> Dict[str, Any]:
        """Fetch and extract readable text from a URL for transparency.
        Uses readability-lxml to extract main article content when HTML; if the URL
        is a PDF (based on content-type), extracts text using pdfminer.six.
        """
        try:
            if not url:
                return {"success": False, "error": "Empty URL"}
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            ctype = resp.headers.get("Content-Type", "").lower()

            # PDF handling
            if "application/pdf" in ctype or url.lower().endswith(".pdf"):
                try:
                    output = BytesIO()
                    extract_text_to_fp(BytesIO(resp.content), output, laparams=LAParams(), output_type='text', codec=None)
                    text = output.getvalue().decode(errors='ignore')
                    cleaned = " ".join(text.split())
                    excerpt = cleaned[:max_chars]
                    return {
                        "success": True,
                        "url": url,
                        "title": url,
                        "text": excerpt,
                        "length": len(excerpt),
                        "truncated": len(cleaned) > len(excerpt),
                        "content_type": "pdf"
                    }
                except Exception as pe:
                    logger.warning(f"Failed to parse PDF from {url}: {pe}")
                    return {"success": False, "url": url, "error": f"pdf_parse_error: {pe}"}

            # HTML handling with readability
            html = resp.text
            try:
                if Document is not None:
                    doc = Document(html)
                    title = (doc.short_title() or "").strip() or url
                    html_content = doc.summary(html_partial=True)
                    soup = BeautifulSoup(html_content, "html.parser")
                else:
                    # Fallback when readability not available
                    soup = BeautifulSoup(html, "html.parser")
                    title = soup.title.string.strip() if soup.title and soup.title.string else url
            except Exception:
                # Fallback to full document
                soup = BeautifulSoup(html, "html.parser")
                title = soup.title.string.strip() if soup.title and soup.title.string else url

            for tag in soup(["script", "style", "noscript"]):
                tag.extract()
            text = " ".join(soup.get_text(" ").split())
            excerpt = text[:max_chars]
            return {
                "success": True,
                "url": url,
                "title": title,
                "text": excerpt,
                "length": len(excerpt),
                "truncated": len(text) > len(excerpt),
                "content_type": "html"
            }
        except Exception as e:
            logger.warning(f"Failed to fetch page content from {url}: {e}")
            return {"success": False, "url": url, "error": str(e)}

    def search_with_pages(
        self,
        query: str,
        max_results: int = 10,
        include_related: bool = True,
        safe_search: str = "moderate",
        max_pages: int = 3,
        max_chars_per_page: int = 8000,
    ) -> Dict[str, Any]:
        """Perform search and fetch full content from top result URLs for transparency."""
        results = self.search(query, max_results=max_results, include_related=include_related, safe_search=safe_search)
        # Prefer abstract_url, then related urls
        urls: List[str] = []
        if results.get("abstract_url"):
            urls.append(results["abstract_url"])
        for item in results.get("related", []):
            if isinstance(item, dict) and item.get("url"):
                urls.append(item["url"])
        # Deduplicate and limit
        seen = set()
        unique_urls = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                unique_urls.append(u)
        unique_urls = unique_urls[:max_pages]

        fetched_pages: List[Dict[str, Any]] = []
        for u in unique_urls:
            page = self.fetch_url_text(u, max_chars=max_chars_per_page)
            fetched_pages.append(page)

        results.update({
            "fetched_pages": fetched_pages
        })
        return results
    
    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience function for quick searches
def web_search(
    query: str, 
    max_results: int = 10, 
    include_related: bool = True,
    timeout: float = 10.0
) -> Dict[str, Any]:
    """
    Perform a quick web search.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        include_related: Include related topics
        timeout: Request timeout
        
    Returns:
        Search results dictionary
    """
    with DuckDuckGoSearchTool(timeout=timeout) as search_tool:
        return search_tool.search(query, max_results, include_related)


def web_search_summary(query: str, max_length: int = 500) -> str:
    """
    Perform a web search and return a summary suitable for AI models.
    
    Args:
        query: Search query
        max_length: Maximum summary length
        
    Returns:
        Formatted summary string
    """
    with DuckDuckGoSearchTool() as search_tool:
        results = search_tool.search(query)
        return search_tool.summarize_results(results, max_length)


def web_search_with_pages(
    query: str,
    max_results: int = 10,
    include_related: bool = True,
    timeout: float = 10.0,
    max_pages: int = 3,
    max_chars_per_page: int = 8000,
) -> Dict[str, Any]:
    """Convenience function to perform search and fetch full page contents for transparency."""
    with DuckDuckGoSearchTool(timeout=timeout) as search_tool:
        return search_tool.search_with_pages(
            query,
            max_results=max_results,
            include_related=include_related,
            safe_search="moderate",
            max_pages=max_pages,
            max_chars_per_page=max_chars_per_page,
        )