"""Tool executor for calling REST APIs and executing tools."""

import httpx
import logging
from typing import Dict, Any, Optional, List
from kubeagentic.config.schema import ToolConfig
from kubeagentic.exceptions import ToolError

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes tools defined in agent configuration."""
    
    def __init__(self, tools: List[ToolConfig], timeout: int = 30):
        """
        Initialize tool executor.
        
        Args:
            tools: List of tool configurations
            timeout: Default timeout for HTTP requests
        """
        self.tools = {tool.name: tool for tool in tools if tool.enabled}
        self.timeout = timeout
        self.http_client = httpx.Client(timeout=timeout)
        logger.info(f"ToolExecutor initialized with {len(self.tools)} enabled tools")
    
    def get_tool(self, name: str) -> Optional[ToolConfig]:
        """Get tool configuration by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all available tool names."""
        return list(self.tools.keys())
    
    def execute(self, tool_name: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a tool with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            
        Returns:
            Tool execution result
            
        Raises:
            ToolError: If tool execution fails
        """
        parameters = parameters or {}
        
        # Get tool configuration
        tool = self.get_tool(tool_name)
        if not tool:
            raise ToolError(f"Tool '{tool_name}' not found or not enabled")
        
        logger.info(f"Executing tool: {tool_name} with parameters: {parameters}")
        
        # Execute based on tool type
        if tool.type == "rest_api":
            return self._execute_rest_api(tool, parameters)
        elif tool.type == "builtin":
            return self._execute_builtin(tool, parameters)
        elif tool.type == "custom":
            return self._execute_custom(tool, parameters)
        else:
            raise ToolError(f"Unsupported tool type: {tool.type}")
    
    def _execute_rest_api(self, tool: ToolConfig, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a REST API tool."""
        try:
            config = tool.config or {}
            url = config.get("url", "")
            method = config.get("method", "GET").upper()
            headers = config.get("headers", {})
            query_params = config.get("query_params", {})
            body = config.get("body", {})
            
            # Substitute parameters in URL
            final_url = url.format(**parameters) if parameters else url
            
            # Substitute parameters in query params
            final_query_params = {}
            for key, value in query_params.items():
                if isinstance(value, str) and "{" in value:
                    # Extract parameter name from {param_name}
                    param_name = value.strip("{}").strip()
                    if param_name in parameters:
                        final_query_params[key] = parameters[param_name]
                else:
                    final_query_params[key] = value
            
            # Substitute parameters in body
            final_body = {}
            for key, value in body.items():
                if isinstance(value, str) and "{" in value:
                    param_name = value.strip("{}").strip()
                    if param_name in parameters:
                        final_body[key] = parameters[param_name]
                else:
                    final_body[key] = value
            
            # Make HTTP request
            logger.debug(f"Making {method} request to {final_url}")
            logger.debug(f"Query params: {final_query_params}")
            logger.debug(f"Headers: {headers}")
            
            response = self.http_client.request(
                method=method,
                url=final_url,
                params=final_query_params,
                headers=headers,
                json=final_body if final_body and method in ["POST", "PUT", "PATCH"] else None
            )
            
            response.raise_for_status()
            
            # Parse response
            try:
                result_data = response.json()
            except Exception:
                result_data = {"text": response.text}
            
            logger.info(f"Tool '{tool.name}' executed successfully")
            
            return {
                "success": True,
                "tool": tool.name,
                "result": result_data,
                "status_code": response.status_code
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error executing tool '{tool.name}': {e}")
            return {
                "success": False,
                "tool": tool.name,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "status_code": e.response.status_code
            }
        except Exception as e:
            logger.error(f"Error executing tool '{tool.name}': {e}")
            return {
                "success": False,
                "tool": tool.name,
                "error": str(e)
            }
    
    def _execute_builtin(self, tool: ToolConfig, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a built-in tool."""
        # Placeholder for built-in tools
        logger.warning(f"Built-in tool '{tool.name}' not yet implemented")
        return {
            "success": False,
            "tool": tool.name,
            "error": "Built-in tools not yet implemented"
        }
    
    def _execute_custom(self, tool: ToolConfig, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a custom tool."""
        # Placeholder for custom tools
        logger.warning(f"Custom tool '{tool.name}' not yet implemented")
        return {
            "success": False,
            "tool": tool.name,
            "error": "Custom tools not yet implemented"
        }
    
    def close(self):
        """Close HTTP client."""
        self.http_client.close()
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.close()
        except Exception:
            pass 