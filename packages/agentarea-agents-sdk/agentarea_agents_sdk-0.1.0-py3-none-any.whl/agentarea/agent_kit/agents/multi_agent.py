"""MultiAgent class for multiagentic workflows."""

import asyncio
import uuid

from ..interfaces import ITaskService
from ..tasks.task_service import InMemoryTaskService
from ..tasks.tasks import TaskStatus
from ..tools.handoff_tool import AgentHandoffTool as HandoffTool
from ..tools.tasks_toolset import TasksToolset
from .agent import Agent


class MultiAgent(Agent):
    """MultiAgent extending Agent for task delegation and polling assigned tasks."""

    def __init__(
        self,
        name: str,
        instruction: str,
        model_provider: str,
        model_name: str,
        task_service: ITaskService | None = None,
        enable_dynamic_discovery: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(
            name=name,
            instruction=instruction,
            model_provider=model_provider,
            model_name=model_name,
            *args,
            **kwargs,
        )
        self.task_service = task_service or InMemoryTaskService()
        self.enable_dynamic_discovery = enable_dynamic_discovery

        # Add multi-agent tools
        task_toolset = TasksToolset(self.task_service)
        self.add_tool(task_toolset)
        self.add_tool(HandoffTool())

    async def delegate_task(
        self, title: str, description: str, assignee_agent_id: uuid.UUID
    ) -> dict | None:
        """Delegate a task to another agent using TasksToolset."""
        toolset = TasksToolset(self.task_service)
        result_str = await toolset.create_task(
            title=title,
            description=description,
            assignee_agent_id=str(assignee_agent_id),
        )
        import json

        result = json.loads(result_str)
        return result

    async def poll_and_execute_assigned_tasks(self, poll_interval: float = 5.0):
        """Poll for assigned tasks and execute them."""
        while True:
            assigned_tasks = self.task_service.list_assigned_tasks(self.agent_id)
            for task in assigned_tasks:
                if task.status == TaskStatus.PENDING:
                    print(f"Executing assigned task: {task.title}")
                    self.task_service.set_status(task.id, TaskStatus.IN_PROGRESS)
                    await self.run(task.description, goal=task.title)
                    self.task_service.set_status(task.id, TaskStatus.COMPLETED)
            await asyncio.sleep(poll_interval)

    async def route_request(
        self,
        task_description: str,
        goal: str = None,
        required_capabilities: list[str] | None = None,
    ) -> dict:
        """Route a request to an appropriate agent based on capabilities."""
        if not self.registry:
            raise ValueError("No registry provided for routing")

        # Use registry to get suitable entity (agent or network) for the task
        suitable_entity = self.registry.get_agent_for_task(
            task_description, enable_dynamic_discovery=self.enable_dynamic_discovery
        )

        if not suitable_entity:
            raise ValueError("No suitable entity found for task")

        # Extract ID for delegation (use id for both types)
        assignee_id = suitable_entity["id"]

        # Delegate task
        task_title = goal or "Routed Task"
        result = await self.delegate_task(task_title, task_description, assignee_id)
        return result
