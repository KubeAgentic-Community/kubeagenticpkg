"""
KubeAgentic v2 - Build AI agents from YAML configuration.

A Python library for creating LangGraph agents from declarative YAML
configuration with OpenAI-compatible REST API.
"""

__version__ = "0.2.1"
__author__ = "KubeAgentic Contributors"
__license__ = "MIT"

from kubeagentic.core.agent import Agent, AgentConfig
from kubeagentic.core.manager import AgentManager
from kubeagentic.config.parser import ConfigParser
from kubeagentic.config.validator import ConfigValidator

__all__ = [
    "Agent",
    "AgentConfig",
    "AgentManager",
    "ConfigParser",
    "ConfigValidator",
    "__version__",
] 