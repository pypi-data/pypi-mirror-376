<div align="center">
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-0-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

# AgentArea Agents SDK

[![PyPI](https://img.shields.io/pypi/v/agentarea-agents-sdk?label=PyPI&color=brightgreen&logo=python)](https://pypi.org/project/agentarea-agents-sdk/)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg?logo=python&label=Python)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg?logo=mit&label=License)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-black.svg?logo=python&label=CodeStyle)](https://github.com/psf/black)
[![GitHub Stars](https://img.shields.io/github/stars/agentarea/agentarea-agents-sdk?style=flat&logo=github&color=yellow&label=Stars)](https://github.com/agentarea/agentarea-agents-sdk/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/agentarea/agentarea-agents-sdk?style=flat&logo=github&color=purple&label=Forks)](https://github.com/agentarea/agentarea-agents-sdk/network)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg?logo=githubactions&label=Build)](https://github.com/agentarea/agentarea-agents-sdk/actions)
[![Discord](https://img.shields.io/badge/Discord-Join_Us-blueviolet.svg?logo=discord)](https://discord.gg/your-discord-invite) <!-- Update with actual if available -->
[![MCP](https://img.shields.io/badge/MCP-Model_Context_Protocol-purple.svg?logo=plug&label=MCP)](https://modelcontextprotocol.io/)

[[Documentation]](docs/) <!-- If docs exist -->
[[Examples]](examples/)

**Independent SDK for Agent Networks, Task Orchestration, and Distributed Runners**

*AgentArea Agents SDK enables building scalable agent networks with task-driven workflows, featuring zero dependencies, multi-provider LLM support, extensible tools, and integration with independent runners like Temporal, Restate, or Dapr for distributed execution.*

</div>

---

## ✨ Key Features

- **🌐 Agent Networks**: Multi-agent collaboration with event-driven communication and orchestration
- **📋 Task Management**: Comprehensive task creation, assignment, progress tracking, and evaluation
- **🏃 Independent Runners**: Extensible base for distributed execution using Temporal, Restate, Dapr, or custom runners
- **🤖 Multi-Provider LLM Support**: Unified interface for OpenAI, Claude, Ollama, and 100+ models via LiteLLM
- **🛠️ Extensible Tool System**: Built-in tools for calculations, MCP integration, human-in-loop, and task operations
- **⚡ ReAct Framework**: Structured reasoning and acting with streaming support for networked agents
- **🔒 Type Safety**: Comprehensive Pydantic models and type hints throughout
- **🚀 Async/Await Ready**: Full asynchronous support for efficient, distributed execution
- **📊 Comprehensive Testing**: Unit, integration, and distributed workflow tests with 50%+ coverage
- **📚 Developer Friendly**: Clean architecture, detailed docs, and easy integration for scalable systems

---

## 💬 Contact

Welcome to join our community on

| [Discord](https://discord.gg/your-discord-invite) <!-- Update --> | Email |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| <img src="https://gw.alicdn.com/imgextra/i1/O1CN01hhD1mu1Dd3BWVUvxN_!!6000000000238-2-tps-400-400.png" width="100" height="100"> | opensource@agentarea.ai |

---

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [🌐 Agent Networks](#-agent-networks)
- [📋 Task Management](#-task-management)
- [🏃 Distributed Runners](#-distributed-runners)
- [📚 Examples](#-examples)
- [🏗️ Architecture](#️-architecture)
- [🔌 Components](#-components)
- [📖 Supported LLM Providers](#-supported-llm-providers)
- [🧪 Testing](#-testing)
- [💻 Development](#-development)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [👥 Contributors](#-contributors)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Installation

From PyPI (when published):

```bash
pip install agentarea-agents-sdk
```

From source (development):

```bash
# Clone the repository
git clone https://github.com/agentarea/agentarea-agents-sdk.git
cd agentarea-agents-sdk

# Install in editable mode with dev dependencies
pip install -e .[dev]
```

### Basic Agent Network Example

Create a simple agent network with task assignment.

```python
import asyncio
from agentarea.agent_kit.agents.network import AgentNetwork
from agentarea.agent_kit.agents import create_agent
from agentarea.agent_kit.tasks.tasks import create_task

async def main():
    # Create agents in a network
    network = AgentNetwork()
    math_agent = create_agent(
        name="Math Agent",
        instruction="You are a math specialist.",
        model="ollama_chat/qwen2.5"
    )
    coordinator = create_agent(
        name="Coordinator",
        instruction="Assign tasks to specialists.",
        model="ollama_chat/qwen2.5"
    )
    network.add_agent(math_agent)
    network.add_agent(coordinator)

    # Create and assign a task
    task = create_task(
        description="Calculate 25 * 4 + 15",
        assignee="Math Agent"
    )
    network.assign_task(task)

    # Run the network
    async for event in network.run():
        print(f"Network event: {event}")

asyncio.run(main())
```

### Task Orchestration Example

Manage tasks across agents.

```python
import asyncio
from agentarea.agent_kit.tasks.task_service import TaskService
from agentarea.agent_kit.agents import create_agent

async def task_example():
    service = TaskService()
    agent = create_agent(
        name="Task Agent",
        instruction="Handle assigned tasks.",
        model="openai/gpt-4"
    )

    # Create task
    task_id = await service.create_task(
        description="Research AI trends",
        agent=agent
    )

    # Monitor progress
    progress = await service.get_task_progress(task_id)
    print(f"Task progress: {progress}")

    # Complete task
    await service.complete_task(task_id, result="AI trends summary")

asyncio.run(task_example())
```

---

## 🌐 Agent Networks

The SDK provides `AgentNetwork` for building multi-agent systems:

- Event-driven communication between agents
- Role-based agent assignment
- Network orchestration for complex workflows
- Integration with tasks for distributed processing

Example: See basic network example above. For advanced setups, use `network.py` for custom topologies.

---

## 📋 Task Management

Robust task system via `tasks/` module:

- `Task` creation with descriptions, assignees, and goals
- `TaskService` for CRUD operations (create, read, update, delete)
- Progress evaluation with `GoalProgressEvaluator`
- Human-in-loop integration for oversight
- Toolset for task-related operations (e.g., `TasksToolset`)

Supports hierarchical tasks and dependencies for orchestration.

---

## 🏃 Distributed Runners

Extensible runner system for independent deployment:

- `BaseAgentRunner`: Abstract base for custom runners
- Integration points for Temporal (workflow orchestration), Restate (stateful workflows), Dapr (service invocation)
- Async execution with state persistence
- Scalable for cloud-native environments

Example integration (Temporal):

```python
from temporalio import workflow
from agentarea.agent_kit.runners import BaseAgentRunner

class TemporalRunner(BaseAgentRunner):
    @workflow.defn
    async def run_workflow(self, agent, task):
        # Implement Temporal workflow
        return await self.execute_agent(agent, task)
```

Adapt for Restate or Dapr via service calls and state management.

---

## 📚 Examples

Run built-in examples:

```bash
# Network example
python examples/test_agentic_network.py

# Task example (adapt from tests)
python -m agentarea.agent_kit.example
```

Examples demonstrate:
- Agent networks and communication
- Task creation and assignment
- Distributed runner stubs
- Tool usage in networked contexts

See [examples/](examples/) for more.

---

## 🏗️ Architecture

Modular design focused on networks, tasks, and runners:

```
agentarea-agents-sdk/
├── src/
│   └── agentarea.agent_kit/
│       ├── agents/          # Agents and networks
│       │   ├── agent.py     # Base Agent
│       │   ├── network.py   # AgentNetwork
│       │   └── multi_agent.py
│       ├── tasks/           # Task management
│       │   ├── tasks.py     # Task models
│       │   └── task_service.py
│       ├── runners/         # Execution engines
│       │   └── base.py      # BaseAgentRunner
│       ├── models/          # LLM integration
│       ├── tools/           # Tool system (incl. tasks_toolset)
│       ├── context/         # Context for networks
│       ├── goal/            # Task evaluation
│       └── prompts.py
├── tests/                   # Tests for networks/tasks/runners
├── examples/                # Network and task examples
├── docs/
├── README.md
├── LICENSE
└── pyproject.toml
```

---

## 🔌 Components

### Agent Networks (`agents/network.py`)

- `AgentNetwork`: Orchestrate multiple agents
- Event handling and inter-agent messaging
- Task routing and coordination

### Task Management (`tasks/`)

- `Task`: Core task entity
- `TaskService`: Service layer for operations
- Integration with agents and tools

### Distributed Runners (`runners/`)

- `BaseAgentRunner`: For custom implementations
- Support for stateful, distributed execution

### Other Components

- LLM Models: Provider-agnostic
- Tools: Extensible with task-specific tools
- Prompts: ReAct for networked reasoning

---

## 📖 Supported LLM Providers

Via LiteLLM (100+ models). See examples above for usage.

### OpenAI
```python
model = LLMModel(provider_type="openai", model_name="gpt-4", api_key="your-key")
```

### Anthropic
```python
model = LLMModel(provider_type="anthropic", model_name="claude-3-opus-20240229", api_key="your-key")
```

### Ollama
```python
model = LLMModel(provider_type="ollama_chat", model_name="qwen2.5")
```

Full list: [LiteLLM docs](https://litellm.ai/).

---

## 🧪 Testing

```bash
pip install -e .[dev]
pytest -q

# Network and task tests
pytest tests/test_agent.py -v
pytest tests/test_task_orchestration.py -v
pytest --cov=src/agentarea.agent_kit --cov-report=term-missing
```

Includes tests for networks, tasks, and runner integrations.

---

## 💻 Development

Setup:

```bash
git clone https://github.com/agentarea/agentarea-agents-sdk.git
cd agentarea-agents-sdk
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]

# Lint, type check, test
ruff check src tests
mypy src
pytest
```

Uses Ruff, MyPy, Pytest. Focus on network/task coverage.

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/network-enhancement`
3. Commit: `git commit -m 'Enhance agent networks'`
4. Push: `git push origin feature/network-enhancement`
5. Open PR

Emphasize contributions to networks, tasks, runners. Guidelines: PEP 8, types, tests.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## 📄 License

MIT License - see [LICENSE](LICENSE).

---

## 👥 Contributors ✨

Thanks to these wonderful people:

<!-- ALL-CONTRIBUTORS-LIST:START -->
<!-- Add contributors here when available -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://all-contributors.org/docs/en/bot/usage) specification.
