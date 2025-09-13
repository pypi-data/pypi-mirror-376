"""
AgentRouter SDK - A Python SDK for building scalable multi-agent applications
"""

from agentrouter.agents.manager import ManagerAgent
from agentrouter.agents.worker import WorkerAgent
from agentrouter.tools.decorator import tool
from agentrouter.plugins.base import Plugin, PluginHook
from agentrouter.exceptions import (
    AgentRouterError,
    APIError,
    ValidationError,
    ExecutionError,
    ToolError,
)

__version__ = "0.0.1b1"
__author__ = "AgentRouter Team"
__email__ = "support@us.inc"

__all__ = [
    # Agents
    "ManagerAgent",
    "WorkerAgent",
    
    # Tools
    "tool",
    
    # Plugins
    "Plugin",
    "PluginHook",
    
    # Exceptions
    "AgentRouterError",
    "APIError",
    "ValidationError",
    "ExecutionError",
    "ToolError",
]

# Configure default logging
import logging
import sys

# Create a default logger
logger = logging.getLogger("agentrouter")
logger.setLevel(logging.INFO)

# Create console handler if no handlers exist
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)