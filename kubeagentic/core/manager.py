"""Agent manager for handling multiple agents."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from kubeagentic.core.agent import Agent, AgentConfig
from kubeagentic.exceptions import AgentError

logger = logging.getLogger(__name__)


class AgentManager:
    """Manage multiple agent instances."""

    def __init__(self):
        """Initialize agent manager."""
        self.agents: Dict[str, Agent] = {}
        logger.info("AgentManager initialized")

    def load_agent(
        self,
        config_path: Optional[Union[str, Path]] = None,
        config_dict: Optional[Dict[str, Any]] = None,
        agent_name: Optional[str] = None,
    ) -> Agent:
        """
        Load an agent from configuration.

        Args:
            config_path: Path to YAML configuration file
            config_dict: Configuration dictionary
            agent_name: Optional agent name (uses name from config if not provided)

        Returns:
            Loaded agent instance

        Raises:
            AgentError: If agent loading fails
        """
        if config_path is None and config_dict is None:
            raise AgentError("Either config_path or config_dict must be provided")

        if config_path is not None and config_dict is not None:
            raise AgentError("Cannot provide both config_path and config_dict")

        try:
            # Create agent
            if config_path is not None:
                agent = Agent.from_config_file(config_path)
            else:
                agent = Agent.from_dict(config_dict)  # type: ignore

            # Use provided name or agent's configured name
            name = agent_name or agent.name

            # Check if agent with same name exists
            if name in self.agents:
                logger.warning(f"Agent '{name}' already loaded, replacing...")

            self.agents[name] = agent
            logger.info(f"Agent '{name}' loaded successfully")

            return agent

        except Exception as e:
            logger.error(f"Failed to load agent: {e}")
            raise AgentError(f"Failed to load agent: {e}") from e

    def get_agent(self, agent_name: str) -> Agent:
        """
        Get an agent by name.

        Args:
            agent_name: Agent name

        Returns:
            Agent instance

        Raises:
            AgentError: If agent not found
        """
        if agent_name not in self.agents:
            raise AgentError(f"Agent '{agent_name}' not found. Available: {list(self.agents.keys())}")

        return self.agents[agent_name]

    def remove_agent(self, agent_name: str) -> None:
        """
        Remove an agent.

        Args:
            agent_name: Agent name

        Raises:
            AgentError: If agent not found
        """
        if agent_name not in self.agents:
            raise AgentError(f"Agent '{agent_name}' not found")

        del self.agents[agent_name]
        logger.info(f"Agent '{agent_name}' removed")

    def list_agents(self) -> Dict[str, str]:
        """
        List all loaded agents.

        Returns:
            Dictionary of agent names and descriptions
        """
        return {
            name: agent.description
            for name, agent in self.agents.items()
        }

    async def achat(
        self,
        agent_name: str,
        message: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Asynchronously chat with an agent.

        Args:
            agent_name: Agent name
            message: User message
            session_id: Optional session ID

        Returns:
            Agent response

        Raises:
            AgentError: If agent not found or execution fails
        """
        agent = self.get_agent(agent_name)
        return await agent.ainvoke(message, session_id=session_id)

    def chat(
        self,
        agent_name: str,
        message: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synchronously chat with an agent.

        Args:
            agent_name: Agent name
            message: User message
            session_id: Optional session ID

        Returns:
            Agent response

        Raises:
            AgentError: If agent not found or execution fails
        """
        agent = self.get_agent(agent_name)
        return agent.invoke(message, session_id=session_id)

    def reload_agent(
        self,
        agent_name: str,
        config_path: Optional[Union[str, Path]] = None,
        config_dict: Optional[Dict[str, Any]] = None,
    ) -> Agent:
        """
        Reload an agent with new configuration.

        Args:
            agent_name: Agent name
            config_path: Path to YAML configuration file
            config_dict: Configuration dictionary

        Returns:
            Reloaded agent instance

        Raises:
            AgentError: If reload fails
        """
        # Remove existing agent
        if agent_name in self.agents:
            self.remove_agent(agent_name)

        # Load with new config
        return self.load_agent(
            config_path=config_path,
            config_dict=config_dict,
            agent_name=agent_name,
        )

    def __len__(self) -> int:
        """Get number of loaded agents."""
        return len(self.agents)

    def __contains__(self, agent_name: str) -> bool:
        """Check if agent is loaded."""
        return agent_name in self.agents 