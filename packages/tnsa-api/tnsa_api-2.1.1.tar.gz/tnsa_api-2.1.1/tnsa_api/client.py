"""
Main TNSA API client implementation.
"""

from typing import Optional, Dict, Any, List, Union, Iterator
from .config import Config
from .http_client import HTTPClient
from .models.chat import (
    ChatMessage,
    ChatCompletion,
    ChatCompletionChunk,
)
from .models.common import (
    Model,
    Usage,
    Conversation,
)
from .models.streaming import ChatCompletionStream
from .exceptions import TNSAError, ModelNotFoundError
from .mcp_client import MCPClient
from .web_search_client import WebSearchClient


class ChatCompletions:
    """Chat completions interface."""
    
    def __init__(self, client: HTTPClient, config: Config, web_search_client: Optional[WebSearchClient] = None):
        self._client = client
        self._config = config
        self._web_search_client = web_search_client
        # Add completions property for OpenAI compatibility
        self.completions = self
    
    def create(
        self,
        model: str,
        messages: List[Union[Dict[str, str], ChatMessage]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
        stop: Optional[Union[str, List[str]]] = None,
        conversation_id: Optional[str] = None,
        enable_web_search: Optional[bool] = None,
        **kwargs
    ) -> Union[ChatCompletion, ChatCompletionStream]:
        """
        Create a chat completion.
        
        Args:
            model: Model to use for completion
            messages: List of messages in the conversation
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            stream: Whether to stream the response
            stop: Stop sequences
            conversation_id: ID for conversation tracking
            enable_web_search: Enable web search for this request (overrides global setting)
            **kwargs: Additional parameters
            
        Returns:
            ChatCompletion or ChatCompletionStream
        """
        # Convert messages to proper format
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                    "name": msg.name
                })
            elif isinstance(msg, dict):
                formatted_messages.append(msg)
            else:
                raise ValueError(f"Invalid message type: {type(msg)}")
        
        # Check if web search should be enabled for this request
        web_search_enabled = (
            enable_web_search if enable_web_search is not None 
            else self._config.web_search_enabled
        )
        
        # Enhance prompt with web search if enabled and available
        original_prompt = self._format_messages_as_prompt(formatted_messages)
        enhanced_prompt = original_prompt
        
        if (web_search_enabled and 
            self._web_search_client and 
            formatted_messages and 
            formatted_messages[-1].get("role") == "user"):
            
            # Try to enhance the last user message with web search
            last_message = formatted_messages[-1]["content"]
            try:
                enhanced_content = self._web_search_client.auto_search_from_prompt(last_message)
                if enhanced_content:
                    # Replace the last user message with enhanced version
                    formatted_messages[-1]["content"] = enhanced_content
                    enhanced_prompt = self._format_messages_as_prompt(formatted_messages)
            except Exception as e:
                # Log the error but continue with original prompt
                import logging
                logging.warning(f"Web search enhancement failed: {e}")
        
        # Build request payload - TNSA API expects 'prompt' field
        payload = {
            "model": model,
            "prompt": enhanced_prompt,
            "format": "html",  # TNSA API format
        }
        
        # Add optional parameters
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if top_p is not None:
            payload["top_p"] = top_p
        if stop is not None:
            payload["stop"] = stop
        if conversation_id is not None:
            payload["chat_id"] = conversation_id
        
        # Add any additional kwargs
        payload.update(kwargs)
        
        if stream:
            # Return streaming response
            stream_iterator = self._client.post("/infer", data=payload, stream=True)
            return ChatCompletionStream(
                stream_iterator=stream_iterator,
                response_id=f"chatcmpl-{conversation_id or 'stream'}",
                model=model,
            )
        else:
            # Return regular response
            response_data = self._client.post("/infer", data=payload)
            return self._parse_chat_completion(response_data, model)
    
    def _format_messages_as_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format messages as a single prompt for models that expect it."""
        prompt_parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        return "\n".join(prompt_parts)
    
    def _parse_chat_completion(self, response_data: Dict[str, Any], model: str) -> ChatCompletion:
        """Parse TNSA API response into ChatCompletion."""
        # Handle TNSA API response format
        if "response" in response_data:
            # TNSA format
            message = ChatMessage(
                role="assistant",
                content=response_data["response"]
            )
            
            from .models.chat import ChatCompletionChoice
            choice = ChatCompletionChoice(
                index=0,
                message=message,
                finish_reason="stop"
            )
            
            usage = Usage(
                prompt_tokens=response_data.get("prompt_tokens", 0),
                completion_tokens=response_data.get("completion_tokens", 0),
                total_tokens=response_data.get("prompt_tokens", 0) + response_data.get("completion_tokens", 0),
                estimated_cost=response_data.get("cost", 0.0)
            )
            
            return ChatCompletion(
                id=response_data.get("chat_id", "chatcmpl-unknown"),
                model=model,
                choices=[choice],
                usage=usage,
                conversation_id=response_data.get("chat_id")
            )
        else:
            # OpenAI-compatible format
            return ChatCompletion.from_dict(response_data)


class Models:
    """Models interface."""
    
    def __init__(self, client: HTTPClient, config: Config):
        self._client = client
        self._config = config
        self._cached_models: Optional[List[Model]] = None
        self._cache_timestamp: Optional[float] = None
        self._cache_ttl = 300  # 5 minutes cache TTL
    
    def list(self) -> List[Model]:
        """List available models with caching."""
        import time
        
        # Check cache validity
        if (self._config.cache_models and 
            self._cached_models is not None and 
            self._cache_timestamp is not None and 
            time.time() - self._cache_timestamp < self._cache_ttl):
            return self._cached_models
        
        # Fetch fresh data
        response_data = self._client.get("/models")
        models_list = response_data.get("models", [])
        
        self._cached_models = []
        for model_id in models_list:
            model = Model(
                id=model_id,
                object="model",
                created=0,
                owned_by="tnsa",
                capabilities=self._get_model_capabilities(model_id),
                context_length=self._get_model_context_length(model_id),
            )
            self._cached_models.append(model)
        
        self._cache_timestamp = time.time()
        return self._cached_models
    
    def retrieve(self, model_id: str) -> Model:
        """Get details about a specific model."""
        models = self.list()
        for model in models:
            if model.id == model_id:
                return model
        
        raise ModelNotFoundError(
            f"Model '{model_id}' not found",
            model_name=model_id,
            available_models=[m.id for m in models]
        )
    
    def _get_model_capabilities(self, model_id: str) -> List[str]:
        """Get capabilities for a model."""
        if "Pro" in model_id:
            return ["chat", "completion", "reasoning"]
        elif "Lite" in model_id:
            return ["chat", "completion"]
        elif "Farmvaidya" in model_id:
            return ["chat", "agriculture"]
        else:
            return ["chat", "completion"]
    
    def _get_model_context_length(self, model_id: str) -> int:
        """Get context length for a model."""
        if "NGen3.9" in model_id:
            return 40000
        elif "NGen3-7B" in model_id:
            return 4096
        else:
            return 4096


class Conversations:
    """Conversations interface."""
    
    def __init__(self, client: HTTPClient):
        self._client = client
        self._conversations: Dict[str, Conversation] = {}
    
    def create(
        self,
        model: str,
        system_prompt: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation."""
        import uuid
        from .models.base import current_timestamp
        
        conversation_id = str(uuid.uuid4())
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt,
                "timestamp": current_timestamp()
            })
        
        conversation = Conversation(
            id=conversation_id,
            model=model,
            created=current_timestamp(),
            messages=messages
        )
        
        self._conversations[conversation_id] = conversation
        return conversation
    
    def get(self, conversation_id: str) -> Conversation:
        """Retrieve an existing conversation."""
        if conversation_id not in self._conversations:
            raise TNSAError(f"Conversation '{conversation_id}' not found")
        
        return self._conversations[conversation_id]
    
    def list(self, limit: int = 20) -> List[Conversation]:
        """List user's conversations."""
        conversations = list(self._conversations.values())
        conversations.sort(key=lambda c: c.created, reverse=True)
        return conversations[:limit]
    
    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False


class TNSA:
    """
    Main TNSA API client.
    
    Usage:
        client = TNSA(api_key="your-api-key")
        
        # List models
        models = client.models.list()
        
        # Create chat completion
        response = client.chat.completions.create(
            model="NGen3.9-Pro",
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        default_headers: Optional[Dict[str, str]] = None,
        config_file: Optional[str] = None,
    ):
        """
        Initialize TNSA client.
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for API (default: https://api.tnsaai.com)
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
        
        self._http_client = HTTPClient(self.config)
        
        # Initialize web search client if enabled
        if self.config.web_search_enabled:
            self._web_search = WebSearchClient(self.config)
        else:
            self._web_search = None
        
        # Initialize interfaces
        self._chat = ChatCompletions(self._http_client, self.config, self._web_search)
        self._models = Models(self._http_client, self.config)
        self._conversations = Conversations(self._http_client)
        
        # Initialize MCP client if enabled
        if self.config.mcp_enabled:
            self._mcp = MCPClient(
                api_key=api_key,
                base_url=base_url,
                timeout=self.config.mcp_timeout,
                max_retries=max_retries,
                config_file=config_file,
            )
        else:
            self._mcp = None
    
    @property
    def chat(self) -> ChatCompletions:
        """Access to chat completion endpoints."""
        return self._chat
    
    @property
    def models(self) -> Models:
        """Access to model management endpoints."""
        return self._models
    
    @property
    def conversations(self) -> Conversations:
        """Access to conversation management."""
        return self._conversations
    
    @property
    def mcp(self) -> Optional[MCPClient]:
        """Access to MCP (Model Context Protocol) features."""
        if not self.config.mcp_enabled:
            raise TNSAError("MCP is disabled. Set TNSA_MCP_ENABLED=true to enable.")
        return self._mcp
    
    @property
    def web_search(self) -> Optional[WebSearchClient]:
        """Access to web search features."""
        if not self.config.web_search_enabled:
            raise TNSAError("Web search is disabled. Set TNSA_WEB_SEARCH_ENABLED=true to enable.")
        return self._web_search
    
    def close(self):
        """Close the client and cleanup resources."""
        if self._http_client:
            self._http_client.close()
        if self._web_search:
            self._web_search.close()
        if self._mcp:
            self._mcp.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.close()
        except:
            pass  # Ignore errors during cleanup