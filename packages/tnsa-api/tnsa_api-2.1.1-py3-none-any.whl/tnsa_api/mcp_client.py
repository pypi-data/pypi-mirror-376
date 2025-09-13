"""
MCP (Model Context Protocol) Client for TNSA API
Provides intelligent MCP integration with Zapier's 7000+ apps
"""

from typing import Optional, Dict, Any, List, Union
import asyncio
import json
from .config import Config
from .http_client import HTTPClient, AsyncHTTPClient
from .models.mcp import MCPTool, MCPToolCall, MCPWorkflowResult, TaskType
from .exceptions import MCPError, MCPConnectionError, MCPToolNotFoundError


class MCPCompletions:
    """MCP-powered completions interface."""
    
    def __init__(self, client: HTTPClient):
        self._client = client
    
    def create(
        self,
        prompt: str,
        model: Optional[str] = None,
        mcp_server_url: Optional[str] = None,
        fast_mode: bool = False,
        max_steps: int = 5,
        demo_mode: bool = False,
        **kwargs
    ) -> MCPWorkflowResult:
        """
        Create an intelligent MCP-powered completion.
        
        Args:
            prompt: Natural language request
            model: Model to use (auto-selected if not provided)
            mcp_server_url: MCP server URL (uses default if not provided)
            fast_mode: Prioritize speed over thoroughness
            max_steps: Maximum workflow steps to execute
            demo_mode: Use demo mode for testing
            **kwargs: Additional parameters
            
        Returns:
            MCPWorkflowResult with execution details
        """
        payload = {
            "prompt": prompt,
            "fast_mode": fast_mode,
            "max_steps": max_steps,
            "demo_mode": demo_mode,
        }
        
        if model:
            payload["model"] = model
        if mcp_server_url:
            payload["mcp_server_url"] = mcp_server_url
        
        payload.update(kwargs)
        
        try:
            response_data = self._client.post("/smart-mcp", data=payload)
            return MCPWorkflowResult.from_dict(response_data)
        except Exception as e:
            raise MCPError(f"MCP workflow execution failed: {str(e)}")
    
    def get_model_recommendations(self, task_description: str) -> Dict[str, Any]:
        """Get model recommendations for a specific task."""
        try:
            response_data = self._client.get("/model-recommendations", params={
                "task": task_description
            })
            return response_data
        except Exception as e:
            raise MCPError(f"Failed to get model recommendations: {str(e)}")


class MCPTools:
    """MCP tools management interface."""
    
    def __init__(self, client: HTTPClient):
        self._client = client
        self._cached_tools: Optional[List[MCPTool]] = None
    
    def list(self, server_url: Optional[str] = None, force_refresh: bool = False) -> List[MCPTool]:
        """List available MCP tools."""
        if self._cached_tools is None or force_refresh:
            params = {}
            if server_url:
                params["server_url"] = server_url
            
            try:
                response_data = self._client.get("/mcp/tools", params=params)
                tools_list = response_data.get("tools", [])
                
                self._cached_tools = []
                for tool_data in tools_list:
                    tool = MCPTool(
                        name=tool_data.get("name", ""),
                        description=tool_data.get("description", ""),
                        parameters=tool_data.get("parameters", []),
                        server_url=server_url
                    )
                    self._cached_tools.append(tool)
            except Exception as e:
                raise MCPConnectionError(f"Failed to list MCP tools: {str(e)}")
        
        return self._cached_tools
    
    def get(self, tool_name: str, server_url: Optional[str] = None) -> MCPTool:
        """Get details about a specific MCP tool."""
        tools = self.list(server_url=server_url)
        for tool in tools:
            if tool.name == tool_name:
                return tool
        
        raise MCPToolNotFoundError(
            f"MCP tool '{tool_name}' not found",
            tool_name=tool_name,
            available_tools=[t.name for t in tools]
        )
    
    def call(
        self,
        tool_name: str,
        params: Dict[str, Any],
        server_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call a specific MCP tool directly."""
        payload = {
            "tool": tool_name,
            "params": params
        }
        
        if server_url:
            payload["server_url"] = server_url
        
        try:
            response_data = self._client.post("/mcp/call", data=payload)
            return response_data
        except Exception as e:
            raise MCPError(f"MCP tool call failed: {str(e)}")


class MCPClient:
    """
    MCP (Model Context Protocol) client for TNSA API.
    
    Provides intelligent integration with Zapier's 7000+ apps through MCP.
    
    Usage:
        mcp_client = MCPClient(api_key="your-api-key")
        
        # List available tools
        tools = mcp_client.tools.list()
        
        # Execute intelligent workflow
        result = mcp_client.completions.create(
            prompt="Find emails from john@example.com about project updates"
        )
        
        # Call specific tool
        email_result = mcp_client.tools.call(
            "gmail_find_email",
            {"query": "from:john@example.com project"}
        )
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        mcp_server_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        default_headers: Optional[Dict[str, str]] = None,
        config_file: Optional[str] = None,
    ):
        """
        Initialize MCP client.
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for API
            mcp_server_url: Default MCP server URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            default_headers: Additional headers to include
            config_file: Path to configuration file
        """
        self.config = Config(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            config_file=config_file,
        )
        
        self.mcp_server_url = mcp_server_url
        self._http_client = HTTPClient(self.config)
        
        # Initialize interfaces
        self._completions = MCPCompletions(self._http_client)
        self._tools = MCPTools(self._http_client)
    
    @property
    def completions(self) -> MCPCompletions:
        """Access to MCP-powered completions."""
        return self._completions
    
    @property
    def tools(self) -> MCPTools:
        """Access to MCP tools management."""
        return self._tools
    
    def close(self):
        """Close the client and cleanup resources."""
        if self._http_client:
            self._http_client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AsyncMCPCompletions:
    """Async MCP-powered completions interface."""
    
    def __init__(self, client: AsyncHTTPClient):
        self._client = client
    
    async def acreate(
        self,
        prompt: str,
        model: Optional[str] = None,
        mcp_server_url: Optional[str] = None,
        fast_mode: bool = False,
        max_steps: int = 5,
        demo_mode: bool = False,
        **kwargs
    ) -> MCPWorkflowResult:
        """
        Create an intelligent MCP-powered completion asynchronously.
        
        Args:
            prompt: Natural language request
            model: Model to use (auto-selected if not provided)
            mcp_server_url: MCP server URL (uses default if not provided)
            fast_mode: Prioritize speed over thoroughness
            max_steps: Maximum workflow steps to execute
            demo_mode: Use demo mode for testing
            **kwargs: Additional parameters
            
        Returns:
            MCPWorkflowResult with execution details
        """
        payload = {
            "prompt": prompt,
            "fast_mode": fast_mode,
            "max_steps": max_steps,
            "demo_mode": demo_mode,
        }
        
        if model:
            payload["model"] = model
        if mcp_server_url:
            payload["mcp_server_url"] = mcp_server_url
        
        payload.update(kwargs)
        
        try:
            response_data = await self._client.post("/smart-mcp", data=payload)
            return MCPWorkflowResult.from_dict(response_data)
        except Exception as e:
            raise MCPError(f"MCP workflow execution failed: {str(e)}")
    
    async def aget_model_recommendations(self, task_description: str) -> Dict[str, Any]:
        """Get model recommendations for a specific task asynchronously."""
        try:
            response_data = await self._client.get("/model-recommendations", params={
                "task": task_description
            })
            return response_data
        except Exception as e:
            raise MCPError(f"Failed to get model recommendations: {str(e)}")
    
    # Aliases for consistency
    create = acreate
    get_model_recommendations = aget_model_recommendations


class AsyncMCPTools:
    """Async MCP tools management interface."""
    
    def __init__(self, client: AsyncHTTPClient):
        self._client = client
        self._cached_tools: Optional[List[MCPTool]] = None
    
    async def alist(self, server_url: Optional[str] = None, force_refresh: bool = False) -> List[MCPTool]:
        """List available MCP tools asynchronously."""
        if self._cached_tools is None or force_refresh:
            params = {}
            if server_url:
                params["server_url"] = server_url
            
            try:
                response_data = await self._client.get("/mcp/tools", params=params)
                tools_list = response_data.get("tools", [])
                
                self._cached_tools = []
                for tool_data in tools_list:
                    tool = MCPTool(
                        name=tool_data.get("name", ""),
                        description=tool_data.get("description", ""),
                        parameters=tool_data.get("parameters", []),
                        server_url=server_url
                    )
                    self._cached_tools.append(tool)
            except Exception as e:
                raise MCPConnectionError(f"Failed to list MCP tools: {str(e)}")
        
        return self._cached_tools
    
    async def aget(self, tool_name: str, server_url: Optional[str] = None) -> MCPTool:
        """Get details about a specific MCP tool asynchronously."""
        tools = await self.alist(server_url=server_url)
        for tool in tools:
            if tool.name == tool_name:
                return tool
        
        raise MCPToolNotFoundError(
            f"MCP tool '{tool_name}' not found",
            tool_name=tool_name,
            available_tools=[t.name for t in tools]
        )
    
    async def acall(
        self,
        tool_name: str,
        params: Dict[str, Any],
        server_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call a specific MCP tool directly asynchronously."""
        payload = {
            "tool": tool_name,
            "params": params
        }
        
        if server_url:
            payload["server_url"] = server_url
        
        try:
            response_data = await self._client.post("/mcp/call", data=payload)
            return response_data
        except Exception as e:
            raise MCPError(f"MCP tool call failed: {str(e)}")
    
    # Aliases for consistency
    list = alist
    get = aget
    call = acall


class AsyncMCPClient:
    """
    Asynchronous MCP (Model Context Protocol) client for TNSA API.
    
    Provides intelligent integration with Zapier's 7000+ apps through MCP.
    
    Usage:
        async with AsyncMCPClient(api_key="your-api-key") as mcp_client:
            # List available tools
            tools = await mcp_client.tools.list()
            
            # Execute intelligent workflow
            result = await mcp_client.completions.create(
                prompt="Find emails from john@example.com about project updates"
            )
            
            # Call specific tool
            email_result = await mcp_client.tools.call(
                "gmail_find_email",
                {"query": "from:john@example.com project"}
            )
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        mcp_server_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        default_headers: Optional[Dict[str, str]] = None,
        config_file: Optional[str] = None,
    ):
        """
        Initialize async MCP client.
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for API
            mcp_server_url: Default MCP server URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            default_headers: Additional headers to include
            config_file: Path to configuration file
        """
        self.config = Config(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            config_file=config_file,
        )
        
        self.mcp_server_url = mcp_server_url
        self._http_client = AsyncHTTPClient(self.config)
        
        # Initialize interfaces
        self._completions = AsyncMCPCompletions(self._http_client)
        self._tools = AsyncMCPTools(self._http_client)
    
    @property
    def completions(self) -> AsyncMCPCompletions:
        """Access to MCP-powered completions."""
        return self._completions
    
    @property
    def tools(self) -> AsyncMCPTools:
        """Access to MCP tools management."""
        return self._tools
    
    async def aclose(self):
        """Close the client and cleanup resources."""
        if self._http_client:
            await self._http_client.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()