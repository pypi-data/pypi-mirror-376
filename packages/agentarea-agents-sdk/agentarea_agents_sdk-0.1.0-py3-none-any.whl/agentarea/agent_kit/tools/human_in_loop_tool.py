"""Human-in-the-loop tool for pausing agent execution for human approval."""

import asyncio
import logging
from typing import Any
from uuid import UUID

from ..interfaces import ITaskService
from ..tasks.tasks import TaskStatus
from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class HumanInLoopTool(BaseTool):
    """Tool to pause agent execution for human approval on high-stakes actions."""

    def __init__(
        self,
        task_service: ITaskService,
        name: str = "human_in_loop",
        description: str = "Pause execution for human approval on high-stakes actions",
        default_threshold: float = 100.0,
        approval_channels: list[str] = None,
    ):
        """Initialize the tool.

        Args:
            task_service: Task service for status tracking
            name: Tool name
            description: Tool description
            default_threshold: Auto-approve below this value
            approval_channels: Notification channels (e.g., ["email", "slack"])
        """
        self.task_service = task_service
        self.default_threshold = default_threshold
        self.approval_channels = approval_channels or ["console"]
        # Store name/description for BaseTool properties
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def get_schema(self) -> dict[str, Any]:
        """Return the OpenAI function schema for the tool parameters."""
        return {
            "parameters": {
                "type": "object",
                "properties": {
                    "action_description": {
                        "type": "string",
                        "description": "Description of the action requiring human approval",
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Approval threshold; actions with cost below this are auto-approved",
                    },
                    "task_id": {
                        "type": "string",
                        "description": "Optional task ID to update status during approval wait",
                    },
                    "human_input": {
                        "type": "string",
                        "description": "Optional human-provided input/context",
                    },
                },
                "required": ["action_description"],
            }
        }

    async def execute(self, **kwargs) -> dict[str, Any]:
        """Execute the HITL flow and wrap the result in standard tool response format."""
        try:
            result = await self.arun(**kwargs)
            return {
                "success": True,
                "result": result,
                "tool_name": self.name,
                "error": None,
            }
        except Exception as e:
            logger.exception("HITL execution failed")
            return {
                "success": False,
                "result": f"Execution failed: {str(e)}",
                "tool_name": self.name,
                "error": str(e),
            }

    async def arun(
        self,
        action_description: str,
        threshold: float | None = None,
        task_id: UUID | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute the tool asynchronously.

        Args:
            action_description: Description of the action requiring approval
            threshold: Override default threshold
            task_id: Optional task ID to update status
            **kwargs: Additional context

        Returns:
            Result dict with approval status and any human input
        """
        threshold = threshold or self.default_threshold

        # Auto-approve if below threshold
        if "cost" in kwargs and kwargs["cost"] < threshold:
            logger.info(f"Auto-approved low-stakes action: {action_description}")
            return {"status": "approved", "auto_approved": True}

        # High-stakes: Require human approval
        logger.warning(f"Awaiting human approval for: {action_description}")
        if task_id:
            self.task_service.set_status(task_id, TaskStatus.BLOCKED)

        # Notify human (placeholder for actual channels)
        notification = f"HUMAN APPROVAL REQUIRED: {action_description}"
        for channel in self.approval_channels:
            if channel == "console":
                print(notification)
            elif channel == "email":
                # TODO: Implement email notification
                logger.info(f"Email notification: {notification}")
            elif channel == "slack":
                # TODO: Implement Slack notification
                logger.info(f"Slack notification: {notification}")

        # Simulate async wait for human input (in real use, this would be via callback)
        # For now, simulate approval after a delay or manual intervention
        # In a real system, this would be a long-running tool with external update
        try:
            # Wait for external signal (e.g., API call to update task)
            # For demo, just wait and assume approval
            await asyncio.sleep(2)  # Simulate async wait
            logger.info("Human approval received (simulated)")
            if task_id:
                self.task_service.set_status(task_id, TaskStatus.IN_PROGRESS)
            return {
                "status": "approved",
                "human_input": kwargs.get("human_input", "Approved by human"),
            }
        except asyncio.CancelledError:
            logger.info("Human approval denied or timed out")
            if task_id:
                self.task_service.set_status(task_id, TaskStatus.FAILED)
            return {"status": "denied", "reason": "Human denied or timed out"}

    def run(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for arun."""
        import asyncio

        try:
            # Use existing event loop if available
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create new event loop for sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.arun(*args, **kwargs))
