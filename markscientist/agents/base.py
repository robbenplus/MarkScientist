"""
MarkScientist Agent Base Class

Provides common infrastructure for all agents.
"""

import json
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from markscientist.models.base import BaseModel, ModelConfig, get_model
from markscientist.trajectory.schema import AgentType, AgentEvent
from markscientist.trajectory.recorder import TrajectoryRecorder


@dataclass
class AgentResult:
    """Agent execution result"""
    output: str
    success: bool
    termination_reason: str = "completed"
    events: List[AgentEvent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "output": self.output,
            "success": self.success,
            "termination_reason": self.termination_reason,
            "events_count": len(self.events),
            "metadata": self.metadata,
        }


class BaseAgent(ABC):
    """
    Agent Base Class

    All agents inherit from this class to implement a unified interface.
    """

    # Subclasses must set these
    agent_type: AgentType = None
    default_system_prompt: str = ""

    def __init__(
        self,
        model_config: Optional[ModelConfig] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        max_turns: int = 50,
        max_runtime_seconds: int = 9000,
        workspace_root: Optional[Path] = None,
        trace_path: Optional[Path] = None,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        """
        Initialize Agent

        Args:
            model_config: Model configuration
            system_prompt: System prompt (can override default)
            tools: Tool definition list
            max_turns: Maximum turns
            max_runtime_seconds: Maximum runtime in seconds
            workspace_root: Workspace root directory
            trace_path: Trajectory save path
            on_event: Event callback
        """
        if self.agent_type is None:
            raise ValueError(f"{self.__class__.__name__} must set agent_type")

        # Model
        if model_config:
            self.model = get_model(model_config)
            self.model_config = model_config
        else:
            # Load default configuration from environment
            from markscientist.config import get_config
            config = get_config()
            self.model_config = ModelConfig(
                backend=config.model.backend,
                model_name=config.model.model_name,
                api_key=config.model.api_key,
                api_base=config.model.api_base,
                temperature=config.agent.temperature,
                top_p=config.agent.top_p,
                max_tokens=config.agent.max_output_tokens,
            )
            self.model = get_model(self.model_config)

        # Prompt
        self.system_prompt = system_prompt or self.default_system_prompt
        if not self.system_prompt:
            from markscientist.prompts import get_agent_prompt
            import datetime
            date_str = datetime.date.today().strftime("%Y-%m-%d")
            self.system_prompt = get_agent_prompt(self.agent_type.value, date_str)

        # Tools
        self.tools = tools or []

        # Limits
        self.max_turns = max_turns
        self.max_runtime_seconds = max_runtime_seconds

        # Workspace
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()

        # Trajectory
        self.trajectory_recorder = TrajectoryRecorder(
            agent_type=self.agent_type,
            model_name=self.model_config.model_name,
            workspace_root=str(self.workspace_root),
            save_path=trace_path,
            on_event=on_event,
        )

    @abstractmethod
    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute task

        Args:
            task: Task description
            context: Additional context

        Returns:
            AgentResult
        """
        pass

    def _build_messages(self, task: str, context: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """Build message list"""
        messages = [
            {"role": "system", "content": self.system_prompt},
        ]

        # User message
        user_content = f"Workspace: {self.workspace_root}\n\n"
        if context:
            user_content += f"Context:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
        user_content += f"Task:\n{task}"

        messages.append({"role": "user", "content": user_content})

        return messages

    def _record_system_and_user(self, messages: List[Dict]) -> None:
        """Record system and user messages"""
        for i, msg in enumerate(messages):
            self.trajectory_recorder.record(
                role=msg["role"],
                text=msg.get("content", ""),
                turn_index=0,
            )

    def _call_model(
        self,
        messages: List[Dict],
        **kwargs
    ) -> Dict[str, Any]:
        """Call model"""
        return self.model.generate(
            messages,
            tools=self.tools if self.tools else None,
            **kwargs
        )

    def get_trajectory(self) -> List[AgentEvent]:
        """Get trajectory"""
        return self.trajectory_recorder.get_events()


def load_tools_from_harness() -> List[Dict]:
    """
    Load tool definitions from ResearchHarness

    Returns:
        Tool definition list
    """
    # Try to import ResearchHarness
    harness_path = Path("/home/zhangwenlong/ResearchHarness")
    if harness_path.exists():
        sys.path.insert(0, str(harness_path))

    try:
        from agent_base.react_agent import AVAILABLE_TOOLS

        tools = []
        for tool in AVAILABLE_TOOLS:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            })
        return tools
    except ImportError:
        print("Warning: Could not import ResearchHarness tools. Using empty tool list.")
        return []


def get_tool_executor():
    """
    Get tool executor

    Returns:
        Tool execution function
    """
    harness_path = Path("/home/zhangwenlong/ResearchHarness")
    if harness_path.exists():
        sys.path.insert(0, str(harness_path))

    try:
        from agent_base.react_agent import AVAILABLE_TOOL_MAP

        def execute_tool(tool_name: str, tool_args: Dict, **kwargs) -> Any:
            if tool_name not in AVAILABLE_TOOL_MAP:
                return f"Error: Tool {tool_name} not found"
            tool = AVAILABLE_TOOL_MAP[tool_name]
            if tool_name == "ReadImage" and hasattr(tool, "call_for_llm"):
                return tool.call_for_llm(tool_args, **kwargs)
            return tool.call(tool_args, **kwargs)

        return execute_tool
    except ImportError:
        def execute_tool(tool_name: str, tool_args: Dict, **kwargs) -> str:
            return f"Error: Tool execution not available (ResearchHarness not found)"
        return execute_tool
