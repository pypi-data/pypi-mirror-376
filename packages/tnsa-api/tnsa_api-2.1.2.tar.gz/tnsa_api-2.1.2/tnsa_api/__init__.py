"""
TNSA API Python Client

A powerful, OpenAI-compatible Python SDK for TNSA NGen3 Pro and Lite Models with MCP Integration.
"""

from .client import TNSA
from .async_client import AsyncTNSA
from .mcp_client import MCPClient, AsyncMCPClient
from .exceptions import (
    TNSAError,
    AuthenticationError,
    RateLimitError,
    ModelNotFoundError,
    InvalidRequestError,
    APIConnectionError,
    APITimeoutError,
    MCPError,
    MCPConnectionError,
    MCPToolNotFoundError,
)
from .models.chat import (
    ChatMessage,
    ChatCompletion,
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionDelta,
)
from .models.common import (
    Usage,
    Model,
    ModelPricing,
    Conversation,
)
from .models.mcp import (
    MCPTool,
    MCPToolCall,
    MCPWorkflowResult,
    TaskType,
)
from .tools import (
    DuckDuckGoSearchTool,
    WebSearchError,
    web_search,
    web_search_summary,
    web_search_with_pages,
)
from .web_search_client import WebSearchClient

__version__ = "2.1.2"
__author__ = "TNSA AI"
__email__ = "info@tnsaai.com"

__all__ = [
    "TNSA",
    "AsyncTNSA",
    "MCPClient",
    "AsyncMCPClient",
    "TNSAError",
    "AuthenticationError", 
    "RateLimitError",
    "ModelNotFoundError",
    "InvalidRequestError",
    "APIConnectionError",
    "APITimeoutError",
    "MCPError",
    "MCPConnectionError",
    "MCPToolNotFoundError",
    "ChatMessage",
    "ChatCompletion",
    "ChatCompletionChoice",
    "Usage",
    "Model",
    "ModelPricing",
    "Conversation",
    "MCPTool",
    "MCPToolCall",
    "MCPWorkflowResult",
    "TaskType",
    "DuckDuckGoSearchTool",
    "WebSearchError",
    "web_search",
    "web_search_summary",
    "web_search_with_pages",
    "WebSearchClient",
]