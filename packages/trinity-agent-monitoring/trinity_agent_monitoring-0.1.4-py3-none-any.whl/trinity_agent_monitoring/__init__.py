"""
Trinity Agent Monitoring SDK

A comprehensive monitoring solution for AI agents with Langfuse integration.
"""

__version__ = "0.1.4"
__author__ = "Team Trinity"
__email__ = "support@giggso.com"

from .agent_monitor import (
    TrinityAgentMonitor,
    create_monitor,
    get_monitor,
    set_monitor,
    Agentic_wrapper,
    LANGFUSE_AVAILABLE
)

from .MCP_monitor import monitoring_wrapper

__all__ = [
    "TrinityAgentMonitor",
    "create_monitor", 
    "get_monitor",
    "set_monitor",
    "LANGFUSE_AVAILABLE",
    "__version__",
    "__author__",
    "__email__",
    "Agentic_wrapper"
]
