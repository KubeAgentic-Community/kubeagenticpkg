"""Core Agent implementation with LangGraph integration."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from kubeagentic.config.parser import ConfigParser
from kubeagentic.config.schema import AgentConfigSchema
from kubeagentic.config.validator import ConfigValidator
from kubeagentic.exceptions import AgentError
from kubeagentic.llm.providers import get_llm_provider, get_llm_with_fallback
from kubeagentic.utils.logging import setup_logging
from kubeagentic.tools.executor import ToolExecutor

logger = logging.getLogger(__name__)


class AgentConfig:
    """Agent configuration wrapper."""

    def __init__(self, config: AgentConfigSchema):
        """
        Initialize agent configuration.

        Args:
            config: Validated configuration schema
        """
        self.config = config
        self.agent = config.agent

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> "AgentConfig":
        """
        Load configuration from file.

        Args:
            file_path: Path to YAML configuration file

        Returns:
            AgentConfig instance
        """
        config = ConfigParser.parse_file(file_path)
        return cls(config)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "AgentConfig":
        """
        Load configuration from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            AgentConfig instance
        """
        config = ConfigParser.parse_dict(config_dict)
        return cls(config)

    def validate(self) -> List[str]:
        """
        Validate configuration.

        Returns:
            List of warning messages
        """
        return ConfigValidator.validate(self.config)


class Agent:
    """Agent built from YAML configuration using LangGraph."""

    def __init__(self, config: AgentConfig):
        """
        Initialize agent from configuration.

        Args:
            config: Agent configuration

        Raises:
            AgentError: If agent initialization fails
        """
        self.config = config
        self.agent_def = config.agent

        # Setup logging
        log_config = self.agent_def.logging
        setup_logging(
            level=log_config.level,
            log_format=log_config.format,
            output=log_config.output,
            file_path=Path(log_config.file_path) if log_config.file_path else None,
        )

        logger.info(f"Initializing agent: {self.agent_def.name}")

        # Validate configuration
        warnings = config.validate()
        for warning in warnings:
            logger.warning(warning)

        # Initialize LLM
        self.llm = self._initialize_llm()

        # Initialize tool executor if tools are configured
        self.tool_executor: Optional[ToolExecutor] = None
        if self.agent_def.tools:
            self.tool_executor = ToolExecutor(
                tools=self.agent_def.tools,
                timeout=self.agent_def.limits.timeout_seconds if self.agent_def.limits else 30
            )
            logger.info(f"Initialized tool executor with {len(self.agent_def.tools)} tools")

        # Initialize graph
        self.graph: Optional[CompiledStateGraph] = None
        self._build_graph()

        logger.info(f"Agent '{self.agent_def.name}' initialized successfully")

    def _initialize_llm(self) -> Any:
        """
        Initialize LLM from configuration.

        Returns:
            Initialized LLM instance

        Raises:
            AgentError: If LLM initialization fails
        """
        try:
            if self.agent_def.llm:
                # Single LLM
                return get_llm_provider(self.agent_def.llm)
            elif self.agent_def.llms:
                # Multiple LLMs with fallback
                return get_llm_with_fallback(self.agent_def.llms)
            else:
                raise AgentError("No LLM configuration provided")
        except Exception as e:
            raise AgentError(f"Failed to initialize LLM: {e}") from e

    def _build_graph(self) -> None:
        """Build LangGraph graph from configuration."""
        try:
            # Define the state schema
            class AgentState(Dict):
                """Agent state for LangGraph."""

                messages: List[Union[HumanMessage, AIMessage, SystemMessage]]

            # Create graph
            workflow = StateGraph(AgentState)

            # Add nodes
            workflow.add_node("agent", self._agent_node)

            # Set entry point
            workflow.set_entry_point("agent")

            # Add edges
            workflow.add_edge("agent", END)

            # Compile graph
            self.graph = workflow.compile()
            logger.info("LangGraph compiled successfully")

        except Exception as e:
            raise AgentError(f"Failed to build agent graph: {e}") from e

    def _agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent node that processes messages.

        Args:
            state: Current state with messages

        Returns:
            Updated state
        """
        messages = state.get("messages", [])

        # Add system prompt if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=self.agent_def.system_prompt)] + messages

        # Call LLM
        try:
            response = self.llm.invoke(messages)
            messages.append(response)
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            error_msg = AIMessage(content=f"Error: {str(e)}")
            messages.append(error_msg)

        return {"messages": messages}

    async def ainvoke(
        self, message: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Asynchronously invoke the agent.

        Args:
            message: User message
            session_id: Optional session ID for conversation history

        Returns:
            Agent response

        Raises:
            AgentError: If agent execution fails
        """
        try:
            logger.debug(f"Agent invoked with message: {message[:100]}...")

            # Prepare state
            state = {
                "messages": [HumanMessage(content=message)]
            }

            # Run graph
            result = await self.graph.ainvoke(state)

            # Extract response
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if isinstance(last_message, AIMessage):
                    return {
                        "content": last_message.content,
                        "role": "assistant",
                        "metadata": {
                            "agent_name": self.agent_def.name,
                            "session_id": session_id,
                        },
                    }

            return {
                "content": "No response generated",
                "role": "assistant",
                "metadata": {
                    "agent_name": self.agent_def.name,
                    "session_id": session_id,
                },
            }

        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            raise AgentError(f"Agent execution failed: {e}") from e

    def invoke(
        self, message: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synchronously invoke the agent.

        Args:
            message: User message
            session_id: Optional session ID for conversation history

        Returns:
            Agent response

        Raises:
            AgentError: If agent execution fails
        """
        try:
            logger.debug(f"Agent invoked with message: {message[:100]}...")

            # Prepare state
            state = {
                "messages": [HumanMessage(content=message)]
            }

            # Run graph
            result = self.graph.invoke(state)

            # Extract response
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if isinstance(last_message, AIMessage):
                    return {
                        "content": last_message.content,
                        "role": "assistant",
                        "metadata": {
                            "agent_name": self.agent_def.name,
                            "session_id": session_id,
                        },
                    }

            return {
                "content": "No response generated",
                "role": "assistant",
                "metadata": {
                    "agent_name": self.agent_def.name,
                    "session_id": session_id,
                },
            }

        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            raise AgentError(f"Agent execution failed: {e}") from e

    @property
    def name(self) -> str:
        """Get agent name."""
        return self.agent_def.name

    @property
    def description(self) -> str:
        """Get agent description."""
        return self.agent_def.description

    @property
    def has_tools(self) -> bool:
        """Check if agent has tools configured."""
        return self.tool_executor is not None and len(self.tool_executor.tools) > 0

    def get_available_tools(self) -> List[str]:
        """
        Get list of available tool names.
        
        Returns:
            List of tool names
        """
        if self.tool_executor:
            return self.tool_executor.list_tools()
        return []

    def execute_tool(self, tool_name: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a tool with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            
        Returns:
            Tool execution result
            
        Raises:
            AgentError: If tool executor is not available or execution fails
        """
        if not self.tool_executor:
            raise AgentError("No tools configured for this agent")
        
        try:
            return self.tool_executor.execute(tool_name, parameters)
        except Exception as e:
            raise AgentError(f"Tool execution failed: {e}") from e

    @classmethod
    def from_config_file(cls, file_path: Union[str, Path]) -> "Agent":
        """
        Create agent from configuration file.

        Args:
            file_path: Path to YAML configuration file

        Returns:
            Agent instance
        """
        config = AgentConfig.from_file(file_path)
        return cls(config)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Agent":
        """
        Create agent from configuration dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Agent instance
        """
        config = AgentConfig.from_dict(config_dict)
        return cls(config) 