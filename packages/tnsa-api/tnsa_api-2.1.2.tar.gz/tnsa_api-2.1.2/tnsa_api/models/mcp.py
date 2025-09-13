"""
MCP (Model Context Protocol) data models
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from .base import BaseModel


class TaskType(Enum):
    """Task types for MCP operations"""
    # Communication & Email
    GMAIL_SEND = "gmail_send"
    GMAIL_FIND = "gmail_find"
    GMAIL_MANAGE = "gmail_manage"
    OUTLOOK_SEND = "outlook_send"
    SLACK_MESSAGE = "slack_message"
    
    # Productivity & Notes
    NOTION_CREATE = "notion_create"
    NOTION_UPDATE = "notion_update"
    NOTION_QUERY = "notion_query"
    
    # Project Management
    TRELLO_CREATE = "trello_create"
    ASANA_CREATE = "asana_create"
    JIRA_CREATE = "jira_create"
    
    # CRM & Sales
    SALESFORCE_CREATE = "salesforce_create"
    HUBSPOT_CREATE = "hubspot_create"
    AIRTABLE_CREATE = "airtable_create"
    
    # Social Media
    TWITTER_POST = "twitter_post"
    LINKEDIN_POST = "linkedin_post"
    
    # Cloud Storage
    GOOGLE_DRIVE_UPLOAD = "google_drive_upload"
    DROPBOX_UPLOAD = "dropbox_upload"
    
    # General
    GENERAL_CHAT = "general_chat"
    AUTOMATION_WORKFLOW = "automation_workflow"


@dataclass
class MCPTool(BaseModel):
    """Represents an MCP tool"""
    name: str
    description: str
    parameters: List[Dict[str, Any]]
    server_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPTool":
        """Create MCPTool from dictionary."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            parameters=data.get("parameters", []),
            server_url=data.get("server_url")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "server_url": self.server_url
        }


@dataclass
class MCPToolCall(BaseModel):
    """Represents an MCP tool call"""
    step: int
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    success: bool = False
    error: Optional[str] = None
    execution_time: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPToolCall":
        """Create MCPToolCall from dictionary."""
        return cls(
            step=data.get("step", 0),
            tool_name=data.get("tool_name", ""),
            parameters=data.get("params", {}),
            result=data.get("tool_result"),
            success=data.get("success", False),
            error=data.get("error"),
            execution_time=data.get("execution_time")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step": self.step,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "result": self.result,
            "success": self.success,
            "error": self.error,
            "execution_time": self.execution_time
        }


@dataclass
class MCPWorkflowResult(BaseModel):
    """Represents the result of an MCP workflow execution"""
    success: bool
    task_type: str
    selected_model: str
    steps: List[MCPToolCall]
    final_response: Optional[str] = None
    execution_time: Optional[float] = None
    tools_available: Optional[int] = None
    error: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPWorkflowResult":
        """Create MCPWorkflowResult from dictionary."""
        steps = []
        for step_data in data.get("steps", []):
            steps.append(MCPToolCall.from_dict(step_data))
        
        return cls(
            success=data.get("success", False),
            task_type=data.get("task_type", "unknown"),
            selected_model=data.get("selected_model", "unknown"),
            steps=steps,
            final_response=data.get("final_response"),
            execution_time=data.get("execution_time"),
            tools_available=data.get("tools_available"),
            error=data.get("error")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "task_type": self.task_type,
            "selected_model": self.selected_model,
            "steps": [step.to_dict() for step in self.steps],
            "final_response": self.final_response,
            "execution_time": self.execution_time,
            "tools_available": self.tools_available,
            "error": self.error
        }
    
    @property
    def tool_calls(self) -> List[MCPToolCall]:
        """Get successful tool calls."""
        return [step for step in self.steps if step.success and step.tool_name != "none"]
    
    @property
    def failed_calls(self) -> List[MCPToolCall]:
        """Get failed tool calls."""
        return [step for step in self.steps if not step.success]
    
    def get_results_by_tool(self, tool_name: str) -> List[Dict[str, Any]]:
        """Get results from specific tool calls."""
        results = []
        for step in self.steps:
            if step.tool_name == tool_name and step.success and step.result:
                results.append(step.result)
        return results