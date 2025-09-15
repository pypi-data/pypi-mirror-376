"""Abstract interfaces for pluggable services."""

from abc import ABC, abstractmethod
from uuid import UUID

from agentarea.agent_kit.tasks.tasks import Task, TaskStatus


class ITaskService(ABC):
    """Abstract interface for task services."""

    @abstractmethod
    def create(
        self,
        title: str,
        description: str = "",
        parent_id: UUID | None = None,
        assignee_agent_id: UUID | None = None,
        priority: int = 1,
        metadata: dict | None = None,
    ) -> Task:
        """Create a new task."""
        pass

    @abstractmethod
    def get(self, task_id: UUID) -> Task | None:
        """Get a task by ID."""
        pass

    @abstractmethod
    def update(self, task_id: UUID, **updates) -> Task | None:
        """Update a task."""
        pass

    @abstractmethod
    def delete(self, task_id: UUID) -> bool:
        """Delete a task and its subtasks."""
        pass

    @abstractmethod
    def list_assigned_tasks(self, agent_id: UUID) -> list[Task]:
        """List tasks assigned to an agent."""
        pass

    @abstractmethod
    def assign_task(self, task_id: UUID, agent_id: UUID) -> Task | None:
        """Assign a task to an agent."""
        pass

    @abstractmethod
    def list_tasks(self, parent_id: UUID | None = None) -> list[Task]:
        """List tasks, optionally by parent."""
        pass

    @abstractmethod
    def set_status(self, task_id: UUID, status: TaskStatus) -> Task | None:
        """Set task status."""
        pass

    @abstractmethod
    def search(self, text: str) -> list[Task]:
        """Search tasks by text."""
        pass

    @abstractmethod
    def to_dict(self, task: Task) -> dict:
        """Serialize task to dict."""
        pass


class IAgentRegistry(ABC):
    """Abstract interface for agent registry."""

    @abstractmethod
    def register_agent(
        self,
        agent_id: UUID,
        name: str,
        instruction: str,
        network_id: UUID | None = None,
        capabilities: list[str] = None,
    ) -> bool:
        """Register a new agent."""
        pass

    @abstractmethod
    def get_agent(self, agent_id: UUID) -> dict | None:
        """Get agent details by ID."""
        pass

    @abstractmethod
    def list_agents(
        self,
        role: str | None = None,
        network_id: UUID | None = None,
        task_filter: str | None = None,
    ) -> list[dict]:
        """List registered agents, optionally filtered by role, network, or task."""
        pass

    @abstractmethod
    def unregister_agent(self, agent_id: UUID) -> bool:
        """Unregister an agent."""
        pass

    @abstractmethod
    def get_agent_for_task(
        self, task_description: str, enable_dynamic_discovery: bool = False
    ) -> dict | None:
        """Get an entity (agent or network) suitable for the task, with optional dynamic discovery."""
        pass

    @abstractmethod
    def register_network(self, network_id: UUID, agents: list[UUID], orchestrator_id: UUID) -> bool:
        """Register a network of agents."""
        pass

    @abstractmethod
    def get_network(self, network_id: UUID) -> dict | None:
        """Get network details by ID."""
        pass

    @abstractmethod
    def list_entities(
        self,
        role: str | None = None,
        network_id: UUID | None = None,
        task_filter: str | None = None,
    ) -> list[dict]:
        """List all registered entities (agents and networks), optionally filtered."""
        pass
