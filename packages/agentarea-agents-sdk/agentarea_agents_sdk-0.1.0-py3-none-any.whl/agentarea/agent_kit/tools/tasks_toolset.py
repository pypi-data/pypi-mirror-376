"""TasksToolset exposing task operations to the LLM."""

from __future__ import annotations

import json
from uuid import UUID

from agentarea.agent_kit.tasks import TaskStatus
from agentarea.agent_kit.tasks.task_service import InMemoryTaskService

from .decorator_tool import Toolset, tool_method


class TasksToolset(Toolset):
    """Manage tasks: create, list, update status, add subtasks, delete, and search."""

    def __init__(self, service: InMemoryTaskService | None = None):
        super().__init__()
        self.service = service or InMemoryTaskService()

    @tool_method
    async def create_task(
        self,
        title: str,
        description: str | None = "",
        parent_id: str | None = None,
        assignee_agent_id: str | None = None,
        priority: int | None = 1,
    ) -> str:
        """Create a task and return JSON of the created task."""
        parent_uuid = UUID(parent_id) if parent_id else None
        assignee_uuid = UUID(assignee_agent_id) if assignee_agent_id else None
        task = self.service.create(
            title=title,
            description=description or "",
            parent_id=parent_uuid,
            assignee_agent_id=assignee_uuid,
            priority=priority or 1,
        )
        return json.dumps(self.service.to_dict(task))

    @tool_method
    async def list_tasks(self, parent_id: str | None = None) -> str:
        """List tasks optionally under a parent. Returns JSON array of tasks."""
        parent_uuid = UUID(parent_id) if parent_id else None
        tasks = self.service.list_tasks(parent_uuid)
        return json.dumps([self.service.to_dict(t) for t in tasks])

    @tool_method
    async def set_status(self, task_id: str, status: str) -> str:
        """Set status of a task. Status must be one of: pending, in_progress, completed, cancelled, blocked."""
        status_enum = TaskStatus(status)
        updated = self.service.set_status(UUID(task_id), status_enum)
        if not updated:
            return json.dumps({"error": "Task not found"})
        return json.dumps(self.service.to_dict(updated))

    @tool_method
    async def add_subtask(
        self,
        parent_id: str,
        title: str,
        description: str | None = "",
        assignee_agent_id: str | None = None,
        priority: int | None = 1,
    ) -> str:
        """Add a subtask under a given parent task and return JSON of the created subtask."""
        assignee_uuid = UUID(assignee_agent_id) if assignee_agent_id else None
        task = self.service.add_subtask(
            UUID(parent_id),
            title=title,
            description=description or "",
            assignee_agent_id=assignee_uuid,
            priority=priority or 1,
        )
        if not task:
            return json.dumps({"error": "Parent task not found"})
        return json.dumps(self.service.to_dict(task))

    @tool_method
    async def delete_task(self, task_id: str) -> str:
        """Delete a task (and its subtasks) by id. Returns JSON {deleted: true/false}."""
        ok = self.service.delete(UUID(task_id))
        return json.dumps({"deleted": ok})

    @tool_method
    async def search_tasks(self, query: str) -> str:
        """Search tasks by text in title or description. Returns JSON array of tasks."""
        tasks = self.service.search(query)
        return json.dumps([self.service.to_dict(t) for t in tasks])

    @tool_method
    async def assign_task(self, task_id: str, agent_id: str) -> str:
        """Assign a task to an agent and return JSON of the updated task."""
        updated = self.service.assign_task(UUID(task_id), UUID(agent_id))
        if not updated:
            return json.dumps({"error": "Task not found"})
        return json.dumps(self.service.to_dict(updated))
