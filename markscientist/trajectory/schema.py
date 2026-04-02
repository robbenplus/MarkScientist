"""
MarkScientist Trajectory Data Schema

Define trajectory data format, compatible with ResearchHarness trace format,
while extending to support three agent types and scientific taste dimensions.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
import json


class AgentType(Enum):
    """Agent type"""
    SOLVER = "solver"
    JUDGE = "judge"
    EVALUATOR = "evaluator"


@dataclass
class AgentEvent:
    """
    Single Agent event record

    Compatible with ResearchHarness FlatTraceWriter format,
    while adding MarkScientist-specific fields.
    """
    # Basic fields (compatible with ResearchHarness)
    event_index: int
    turn_index: int
    timestamp: str
    role: str  # system | user | assistant | tool | runtime
    text: str

    # Tool call related
    tool_call_ids: List[str] = field(default_factory=list)
    tool_names: List[str] = field(default_factory=list)
    tool_arguments: List[Any] = field(default_factory=list)

    # Completion status
    finish_reason: str = ""
    termination: str = ""
    error: str = ""

    # Image related
    image_paths: List[str] = field(default_factory=list)

    # MarkScientist extended fields
    agent_type: Optional[str] = None  # solver | judge | evaluator
    model_info: Optional[Dict[str, Any]] = None

    # v0.2+ extensions (reserved)
    reasoning_trace: Optional[str] = None
    quality_signals: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class QualityScores:
    """
    Quality scores (produced by Judge Agent)
    """
    overall_score: float = 0.0
    rigor: float = 0.0
    novelty: float = 0.0
    clarity: float = 0.0
    feasibility: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class TrajectoryRecord:
    """
    Complete trajectory record

    Contains a complete Solver-Judge-Evaluator interaction.
    """
    # Unique identifier
    trajectory_id: str = field(default_factory=lambda: uuid4().hex)
    version: str = "0.1"

    # Time information
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    # Task information
    task: str = ""
    task_category: str = ""  # idea | experiment | review | writing | analysis | other
    domain: str = ""
    sub_domain: str = ""

    # Context
    workspace_root: str = ""
    model_name: str = ""

    # Agent trajectories
    solver_events: List[AgentEvent] = field(default_factory=list)
    judge_events: List[AgentEvent] = field(default_factory=list)
    evaluator_events: List[AgentEvent] = field(default_factory=list)

    # Results
    final_output: str = ""
    quality_scores: Optional[QualityScores] = None
    success: bool = False
    termination_reason: str = ""

    # User feedback (v0.2+ collection)
    user_feedback: Optional[Dict[str, Any]] = None

    # External validation (v0.3+ collection)
    external_validation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            "trajectory_id": self.trajectory_id,
            "version": self.version,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "task": self.task,
            "task_category": self.task_category,
            "domain": self.domain,
            "sub_domain": self.sub_domain,
            "workspace_root": self.workspace_root,
            "model_name": self.model_name,
            "solver_events": [e.to_dict() for e in self.solver_events],
            "judge_events": [e.to_dict() for e in self.judge_events],
            "evaluator_events": [e.to_dict() for e in self.evaluator_events],
            "final_output": self.final_output,
            "quality_scores": self.quality_scores.to_dict() if self.quality_scores else None,
            "success": self.success,
            "termination_reason": self.termination_reason,
            "user_feedback": self.user_feedback,
            "external_validation": self.external_validation,
        }
        return result

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def add_solver_event(self, event: AgentEvent) -> None:
        """Add Solver event"""
        event.agent_type = AgentType.SOLVER.value
        self.solver_events.append(event)

    def add_judge_event(self, event: AgentEvent) -> None:
        """Add Judge event"""
        event.agent_type = AgentType.JUDGE.value
        self.judge_events.append(event)

    def add_evaluator_event(self, event: AgentEvent) -> None:
        """Add Evaluator event"""
        event.agent_type = AgentType.EVALUATOR.value
        self.evaluator_events.append(event)

    def complete(self,
                 final_output: str,
                 success: bool,
                 termination_reason: str = "completed",
                 quality_scores: Optional[QualityScores] = None) -> None:
        """Mark trajectory as completed"""
        self.final_output = final_output
        self.success = success
        self.termination_reason = termination_reason
        self.quality_scores = quality_scores
        self.completed_at = datetime.now().isoformat()


# =============================================================================
# ResearchHarness compatible format
# =============================================================================

TRACE_FIELD_NAMES = [
    "run_id",
    "event_index",
    "turn_index",
    "timestamp",
    "model_name",
    "workspace_root",
    "role",
    "text",
    "tool_call_ids",
    "tool_names",
    "tool_arguments",
    "finish_reason",
    "termination",
    "error",
    "image_paths",
    # MarkScientist extensions
    "agent_type",
    "model_info",
    "reasoning_trace",
    "quality_signals",
]


def event_to_flat_trace(event: AgentEvent, run_id: str, model_name: str, workspace_root: str) -> Dict[str, Any]:
    """
    Convert AgentEvent to ResearchHarness-compatible flat trace format
    """
    return {
        "run_id": run_id,
        "event_index": event.event_index,
        "turn_index": event.turn_index,
        "timestamp": event.timestamp,
        "model_name": model_name,
        "workspace_root": workspace_root,
        "role": event.role,
        "text": event.text,
        "tool_call_ids": event.tool_call_ids,
        "tool_names": event.tool_names,
        "tool_arguments": event.tool_arguments,
        "finish_reason": event.finish_reason,
        "termination": event.termination,
        "error": event.error,
        "image_paths": event.image_paths,
        # MarkScientist extensions
        "agent_type": event.agent_type,
        "model_info": event.model_info,
        "reasoning_trace": event.reasoning_trace,
        "quality_signals": event.quality_signals,
    }
