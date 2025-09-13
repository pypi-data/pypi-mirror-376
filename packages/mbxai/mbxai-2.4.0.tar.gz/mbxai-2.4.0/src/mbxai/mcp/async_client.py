"""Async MCP client implementation."""

from typing import Any, TypeVar, Callable
import httpx
import logging
import json
from pydantic import BaseModel, Field

from ..tools.async_client import AsyncToolClient, Tool, convert_to_strict_schema
from ..openrouter.async_client import AsyncOpenRouterClient

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AsyncMCPTool(Tool):
    """A tool from the MCP server for async operations."""
    inputSchema: dict[str, Any]
    internal_url: str
    strict: bool = True
    function: Callable[..., Any] | None = None  # Make function optional during initialization

    def to_openai_function(self) -> dict[str, Any]:
        """Convert the tool to an OpenAI function definition."""
        # Convert schema to strict format, keeping input wrapper
        strict_schema = convert_to_strict_schema(self.inputSchema, strict=self.strict, keep_input_wrapper=True)
        
        function_def = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": strict_schema,
                "strict": True
            }
        }
        
        logger.debug(f"(async_client) Created function definition for {self.name}: {json.dumps(function_def, indent=2)}")
        return function_def


class AsyncMCPClient(AsyncToolClient):
    """Async MCP client that extends AsyncToolClient to support MCP tool servers."""

    def __init__(self, async_openrouter_client: AsyncOpenRouterClient):
        """Initialize the async MCP client."""
        super().__init__(async_openrouter_client)
        self._mcp_servers: dict[str, str] = {}
        self._async_http_client = httpx.AsyncClient()

    async def __aenter__(self):
        """Enter the async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context."""
        await self._async_http_client.aclose()

    def _create_tool_function(self, tool: AsyncMCPTool) -> Callable[..., Any]:
        """Create a function that invokes an MCP tool (async version)."""
        async def async_tool_function(**kwargs: Any) -> Any:
            # If kwargs has input wrapper, unwrap it
            if "input" in kwargs:
                kwargs = kwargs["input"]

            # Get the URL to use for the tool
            url = tool.internal_url
            if url is None:
                # Use the MCP server URL as fallback
                server_url = self._mcp_servers.get(tool.service)
                if server_url is None:
                    raise ValueError(f"No MCP server found for service {tool.service}")
                url = f"{server_url}/tools/{tool.name}/invoke"

            # Make the async HTTP request to the tool's URL
            response = await self._async_http_client.post(
                url,
                json={"input": kwargs} if tool.strict else kwargs,
                timeout=300.0  # 5 minutes timeout
            )
            
            # Log response details for debugging
            logger.debug(f"Tool {tool.name} async response status: {response.status_code}")
            logger.debug(f"Tool {tool.name} async response headers: {response.headers}")
            
            try:
                result = response.json()
                logger.debug(f"Tool {tool.name} async response parsed successfully")
                return result
            except Exception as e:
                logger.error(f"Failed to parse tool {tool.name} async response: {str(e)}")
                logger.error(f"Response content: {response.text[:1000]}...")  # Log first 1000 chars
                raise
        
        return async_tool_function

    async def register_mcp_server(self, name: str, base_url: str) -> None:
        """Register an MCP server and load its tools (async version)."""
        self._mcp_servers[name] = base_url.rstrip("/")
        
        # Fetch tools from the server
        response = await self._async_http_client.get(f"{base_url}/tools")
        response_data = response.json()
        
        # Extract tools array from response
        tools_data = response_data.get("tools", [])
        logger.debug(f"Received {len(tools_data)} tools from server {name}")
        
        # Register each tool
        for idx, tool_data in enumerate(tools_data):
            logger.debug(f"Processing tool {idx}: {json.dumps(tool_data, indent=2)}")
            
            # Ensure tool_data is a dictionary
            if not isinstance(tool_data, dict):
                logger.error(f"Invalid tool data type: {type(tool_data)}. Expected dict, got {tool_data}")
                continue
                
            try:
                # Create AsyncMCPTool instance with proper dictionary unpacking
                tool = AsyncMCPTool(**tool_data)
                
                # Create the async tool function
                tool_function = self._create_tool_function(tool)
                
                # Set the function after creation
                tool.function = tool_function
                
                # Register the tool with AsyncToolClient
                self._tools[tool.name] = tool
                logger.debug(f"Successfully registered async tool: {tool.name}")
            except Exception as e:
                logger.error(f"Failed to register async tool: {str(e)}")
                logger.error(f"Tool data that caused the error: {json.dumps(tool_data, indent=2)}")
