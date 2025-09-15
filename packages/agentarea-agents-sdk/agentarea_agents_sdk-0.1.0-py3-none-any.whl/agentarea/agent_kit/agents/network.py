"""AgentNetwork class for grouping agents in a network."""

from ..interfaces import ITaskService
from ..tasks.task_service import InMemoryTaskService
from ..tasks.tasks import TaskStatus
from .agent import Agent
from .multi_agent import MultiAgent


class AgentNetwork:
    """AgentNetwork for managing a group of agents with an orchestrator."""

    def __init__(
        self,
        name: str,
        agents: list[Agent] = None,
        orchestrator: MultiAgent | None = None,
        task_service: ITaskService | None = None,
        enable_dynamic_discovery: bool = False,
    ):
        self.name = name
        self.agents = agents or []
        self.connected_networks = []
        self.orchestrator = orchestrator
        self.task_service = task_service or InMemoryTaskService()
        self.enable_dynamic_discovery = enable_dynamic_discovery

        if orchestrator:
            self.agents.append(orchestrator)

    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the network."""
        if agent not in self.agents:
            self.agents.append(agent)

    def remove_agent(self, agent: Agent) -> None:
        """Remove an agent from the network."""
        self.agents = [a for a in self.agents if a != agent]

    async def process_request(self, task_description: str, goal: str = None) -> str:
        """Process an incoming request by routing to orchestrator and tracking via task_service."""
        if not self.orchestrator:
            raise ValueError("No orchestrator set for this network")

        # If dynamic discovery is enabled, orchestrator will use registry
        # Otherwise, it uses its local agent list
        # The orchestrator's route_request now handles both cases via registry

        # Create task for tracking
        task = self.task_service.create(
            title=goal or "Network Request",
            description=task_description,
            assignee_agent_id=self.orchestrator.agent_id,
        )
        self.task_service.set_status(task.id, TaskStatus.IN_PROGRESS)

        try:
            result = await self.orchestrator.run(task_description, goal=goal)
            self.task_service.set_status(task.id, TaskStatus.COMPLETED)
            return result
        except Exception as e:
            self.task_service.set_status(task.id, TaskStatus.BLOCKED)
            raise e

    def build_dynamic_network(self, task_description: str) -> list[Agent]:
        """Build a temporary network of agents based on task capabilities."""
        if not self.orchestrator or not self.orchestrator.registry:
            return []
        entities = self.orchestrator.registry.list_entities(task_filter=task_description)
        # For now, return agents only. Networks within networks is future work.
        agent_entities = [e for e in entities if e["type"] == "agent"]
        # Convert to Agent objects if needed (requires registry to store Agent instances or a lookup)
        # Placeholder: return IDs for now
        return [e["id"] for e in agent_entities]

    def connect_to(self, other_network: "AgentNetwork") -> None:
        """Connect this network to another for cross-delegation by sharing services."""
        if other_network not in self.connected_networks:
            self.connected_networks.append(other_network)
            other_network.connected_networks.append(self)
        # Share task_service and registry for cross-polling and discovery
        # Runners can poll shared service for assigned tasks across networks
        # For registry, use union in list_agents if needed (extend in MultiAgent route_request)

    def set_orchestrator(self, orchestrator: MultiAgent) -> None:
        """Set the orchestrator for request processing."""
        self.orchestrator = orchestrator
        if orchestrator not in self.agents:
            self.add_agent(orchestrator)
