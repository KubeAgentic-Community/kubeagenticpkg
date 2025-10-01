"""Tool registry for managing and discovering tools."""

import logging
from typing import Dict, List, Optional
from kubeagentic.config.schema import ToolConfig

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, ToolConfig] = {}
        logger.info("ToolRegistry initialized")
    
    def register(self, tool: ToolConfig) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool configuration to register
        """
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def register_many(self, tools: List[ToolConfig]) -> None:
        """
        Register multiple tools.
        
        Args:
            tools: List of tool configurations to register
        """
        for tool in tools:
            self.register(tool)
    
    def get(self, name: str) -> Optional[ToolConfig]:
        """
        Get tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool configuration or None if not found
        """
        return self._tools.get(name)
    
    def list_all(self) -> List[ToolConfig]:
        """
        List all registered tools.
        
        Returns:
            List of all tool configurations
        """
        return list(self._tools.values())
    
    def list_enabled(self) -> List[ToolConfig]:
        """
        List all enabled tools.
        
        Returns:
            List of enabled tool configurations
        """
        return [tool for tool in self._tools.values() if tool.enabled]
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            name: Tool name
            
        Returns:
            True if tool was unregistered, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        logger.info("Cleared all tools from registry")
    
    def __len__(self) -> int:
        """Get number of registered tools."""
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        """Check if tool is registered."""
        return name in self._tools 