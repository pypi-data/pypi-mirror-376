# Trinity Agent Monitoring SDK

A comprehensive Python SDK for monitoring AI agents with advanced tracing, metrics collection, and observability capabilities powered by Langfuse.

## Features

- **Comprehensive Agent Monitoring**: Track agent execution, tool usage, and performance metrics
- **Rich Metrics Collection**: Monitor tokens, costs, latency, and tool utilization
- **Tool Usage Analytics**: Detailed analysis of which tools your agents use and how often
- **Easy Integration**: Simple decorator-based monitoring with minimal code changes


## Installation

```bash
pip install trinity-agent-monitoring
```

## Quick Start

### 1. Initialize the Monitor

```python
from trinity_agent_monitoring import create_monitor, set_monitor

# Create and set up the global monitor
monitor = create_monitor(
    public_key="your_trinity_public_key",
    secret_key="your_trinity_secret_key"
)

# Set as global monitor for easy access
set_monitor(monitor)
```

### 2. Monitor Your Agent

```python
from trinity_agent_monitoring import get_monitor

# Get the global monitor
monitor = get_monitor()

# Use the decorator to monitor your agent
@monitor.monitor_agent(agent_name="my_ai_agent")
def my_agent_function(agent_executor,user_input):
    # Your agent logic here
    response = process_user_input(user_input)
    return response

# Call your monitored function
result = my_agent_function(agent_executor, "Hello, agent!")
```

### 3. Instance-based Monitoring

```python
from trinity_agent_monitoring import TrinityAgentMonitor

# Create a dedicated monitor instance
monitor = TrinityAgentMonitor(
    public_key="your_public_key",
    secret_key="your_secret_key"
)

# Use with your agent
@monitor.monitor_agent("custom_agent")
def custom_agent_function():
    # Agent logic
    pass
```

### Get Callback Handler for LangChain

```python
# Get the callback handler for LangChain integration
callback_handler = monitor.get_callback_handler()

# Use with your LangChain agent
from langchain.agents import AgentExecutor
from langchain.llms import OpenAI

agent = AgentExecutor.from_agent_and_tools(
    agent=your_agent,
    tools=your_tools,
    callbacks=[callback_handler]
)
```

## API Reference

### TrinityAgentMonitor

Main monitoring class that provides comprehensive agent monitoring capabilities.

### Utility Functions

- `create_monitor(public_key, secret_key, host)`: Create a new monitor instance
- `get_monitor()`: Get the global monitor instance
- `set_monitor(monitor)`: Set the global monitor instance

## Metrics Collected

The SDK automatically collects the following metrics:

- **Token Usage**: Input, output, and total tokens
- **Cost Analysis**: Calculated costs for each operation
- **Latency**: Start time, end time, and duration
- **Tool Usage**: Which tools were used and how many times
- **Input/Output**: Raw input and output data for analysis
- **Metadata**: Custom metadata for additional context

## Support

For support and questions, contact us at support@giggso.com
