"""Agentic AI components for agent execution.

This module contains all AI-specific components:
- High-level Agent class for simplified usage
- LLM clients and interactions
- Agent tools and completion detection
- Goal progress evaluation
- Tool management and execution

This module is framework-agnostic and focuses on pragmatic agent execution patterns.
"""

# High-level Agent class (recommended for most users)
from .agents.agent import Agent, create_agent
from .agents.basic_agent import run_agent
from .context.context_service import (
    ContextEvent,
    ContextService,
    InMemoryContextService,
    events_to_messages,
)

# Services
from .goal.goal_progress_evaluator import GoalProgressEvaluator

# LLM Model
from .models.llm_model import LLMModel, LLMRequest, LLMResponse, LLMUsage

# Prompts
from .prompts import MessageTemplates, PromptBuilder

# Runners
from .runners import (
    BaseAgentRunner,
    ExecutionResult,
    RunnerConfig,
)
from .tasks.task_service import InMemoryTaskService

# Tools
from .tools.base_tool import BaseTool, ToolExecutionError, ToolRegistry
from .tools.completion_tool import CompletionTool
from .tools.mcp_tool import MCPTool, MCPToolFactory
from .tools.tasks_toolset import TasksToolset
from .tools.tool_executor import ToolExecutor
from .tools.tool_manager import ToolManager

__all__ = [
    # High-level Agent (recommended)
    "Agent",
    "create_agent",
    "run_agent",
    # LLM Components
    "LLMModel",
    "LLMRequest",
    "LLMResponse",
    "LLMUsage",
    # Tools
    "BaseTool",
    "CompletionTool",
    "MCPTool",
    "MCPToolFactory",
    "ToolExecutionError",
    "ToolRegistry",
    "ToolExecutor",
    "ToolManager",
    "TasksToolset",
    # Services
    "GoalProgressEvaluator",
    "InMemoryTaskService",
    "ContextService",
    "InMemoryContextService",
    "ContextEvent",
    "events_to_messages",
    # Prompts
    "MessageTemplates",
    "PromptBuilder",
    # Runners
    "BaseAgentRunner",
    "ExecutionResult",
    "RunnerConfig",
]
