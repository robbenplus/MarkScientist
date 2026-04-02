"""
MarkScientist Trajectory Recorder

Trajectory recorder, responsible for recording and saving Agent interactions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from markscientist.trajectory.schema import (
    AgentEvent,
    TrajectoryRecord,
    AgentType,
    event_to_flat_trace,
)


class TrajectoryRecorder:
    """
    Trajectory Recorder

    Supports two output formats:
    1. Flat JSONL (compatible with ResearchHarness)
    2. Complete TrajectoryRecord JSON
    """

    def __init__(
        self,
        *,
        agent_type: AgentType,
        model_name: str,
        workspace_root: str,
        save_path: Optional[Path] = None,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.agent_type = agent_type
        self.model_name = model_name
        self.workspace_root = str(workspace_root)
        self.save_path = Path(save_path) if save_path else None
        self.on_event = on_event

        self.run_id = uuid4().hex
        self.event_index = 0
        self.events: List[AgentEvent] = []

    def record(
        self,
        *,
        role: str,
        text: str = "",
        turn_index: int = 0,
        tool_call_ids: Optional[List[str]] = None,
        tool_names: Optional[List[str]] = None,
        tool_arguments: Optional[List[Any]] = None,
        finish_reason: str = "",
        termination: str = "",
        error: str = "",
        image_paths: Optional[List[str]] = None,
        reasoning_trace: Optional[str] = None,
        quality_signals: Optional[Dict[str, float]] = None,
    ) -> AgentEvent:
        """
        Record an event

        Args:
            role: Role (system | user | assistant | tool | runtime)
            text: Text content
            turn_index: Turn index
            tool_call_ids: Tool call ID list
            tool_names: Tool name list
            tool_arguments: Tool argument list
            finish_reason: Finish reason
            termination: Termination reason
            error: Error message
            image_paths: Image path list
            reasoning_trace: Reasoning trace (v0.2+)
            quality_signals: Quality signals (v0.2+)

        Returns:
            Created AgentEvent
        """
        self.event_index += 1

        event = AgentEvent(
            event_index=self.event_index,
            turn_index=turn_index,
            timestamp=datetime.now().astimezone().isoformat(timespec="seconds"),
            role=role,
            text=text,
            tool_call_ids=tool_call_ids or [],
            tool_names=tool_names or [],
            tool_arguments=tool_arguments or [],
            finish_reason=finish_reason,
            termination=termination,
            error=error,
            image_paths=image_paths or [],
            agent_type=self.agent_type.value,
            model_info={"model_name": self.model_name},
            reasoning_trace=reasoning_trace,
            quality_signals=quality_signals,
        )

        self.events.append(event)

        # Save to file (flat format)
        if self.save_path:
            flat_trace = event_to_flat_trace(
                event, self.run_id, self.model_name, self.workspace_root
            )
            self._append_jsonl(flat_trace)

        # Callback
        if self.on_event:
            self.on_event(event.to_dict())

        return event

    def _append_jsonl(self, record: Dict[str, Any]) -> None:
        """Append a line to JSONL file"""
        if not self.save_path:
            return

        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        with self.save_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def get_events(self) -> List[AgentEvent]:
        """Get all recorded events"""
        return self.events.copy()

    def get_summary(self) -> Dict[str, Any]:
        """Get recording summary"""
        return {
            "run_id": self.run_id,
            "agent_type": self.agent_type.value,
            "model_name": self.model_name,
            "workspace_root": self.workspace_root,
            "total_events": len(self.events),
            "save_path": str(self.save_path) if self.save_path else None,
        }


class WorkflowTrajectoryRecorder:
    """
    Workflow-level trajectory recorder

    Manages a complete Solver-Judge-Evaluator interaction flow.
    """

    def __init__(
        self,
        *,
        task: str,
        model_name: str,
        workspace_root: str,
        save_dir: Optional[Path] = None,
        task_category: str = "other",
        domain: str = "",
        sub_domain: str = "",
    ):
        self.record = TrajectoryRecord(
            task=task,
            task_category=task_category,
            domain=domain,
            sub_domain=sub_domain,
            workspace_root=str(workspace_root),
            model_name=model_name,
        )

        self.save_dir = Path(save_dir) if save_dir else None
        self._event_index = 0

    def create_agent_recorder(
        self,
        agent_type: AgentType,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> TrajectoryRecorder:
        """
        Create recorder for specific Agent

        Args:
            agent_type: Agent type
            on_event: Event callback

        Returns:
            TrajectoryRecorder instance
        """
        save_path = None
        if self.save_dir:
            save_path = self.save_dir / f"{self.record.trajectory_id}_{agent_type.value}.jsonl"

        return TrajectoryRecorder(
            agent_type=agent_type,
            model_name=self.record.model_name,
            workspace_root=self.record.workspace_root,
            save_path=save_path,
            on_event=on_event,
        )

    def collect_from_recorder(self, recorder: TrajectoryRecorder) -> None:
        """
        Collect events from Agent recorder

        Args:
            recorder: TrajectoryRecorder instance
        """
        events = recorder.get_events()

        if recorder.agent_type == AgentType.SOLVER:
            self.record.solver_events.extend(events)
        elif recorder.agent_type == AgentType.JUDGE:
            self.record.judge_events.extend(events)
        elif recorder.agent_type == AgentType.EVALUATOR:
            self.record.evaluator_events.extend(events)

    def complete(
        self,
        final_output: str,
        success: bool,
        termination_reason: str = "completed",
        quality_scores: Optional[Dict[str, float]] = None,
    ) -> TrajectoryRecord:
        """
        Complete trajectory recording

        Args:
            final_output: Final output
            success: Whether successful
            termination_reason: Termination reason
            quality_scores: Quality scores

        Returns:
            Completed TrajectoryRecord
        """
        from markscientist.trajectory.schema import QualityScores

        scores = None
        if quality_scores:
            scores = QualityScores(
                overall_score=quality_scores.get("overall_score", 0),
                rigor=quality_scores.get("rigor", 0),
                novelty=quality_scores.get("novelty", 0),
                clarity=quality_scores.get("clarity", 0),
                feasibility=quality_scores.get("feasibility", 0),
            )

        self.record.complete(
            final_output=final_output,
            success=success,
            termination_reason=termination_reason,
            quality_scores=scores,
        )

        # Save complete trajectory
        if self.save_dir:
            self._save_full_trajectory()

        return self.record

    def _save_full_trajectory(self) -> None:
        """Save complete trajectory record"""
        if not self.save_dir:
            return

        self.save_dir.mkdir(parents=True, exist_ok=True)
        save_path = self.save_dir / f"{self.record.trajectory_id}_full.json"

        with save_path.open("w", encoding="utf-8") as f:
            f.write(self.record.to_json())

    def get_record(self) -> TrajectoryRecord:
        """Get trajectory record"""
        return self.record
