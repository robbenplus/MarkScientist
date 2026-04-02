"""
MarkScientist Basic Research Workflow

v0.1 Basic research workflow:
1. Solver executes task
2. Judge evaluates result
3. (Optional) If score is low, let Solver improve
4. Evaluator performs meta-evaluation
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from markscientist.agents.solver import SolverAgent
from markscientist.agents.judge import JudgeAgent, ReviewResult
from markscientist.agents.evaluator import EvaluatorAgent, MetaEvaluationResult
from markscientist.trajectory.recorder import WorkflowTrajectoryRecorder
from markscientist.trajectory.schema import AgentType
from markscientist.config import Config, get_config


@dataclass
class WorkflowResult:
    """Workflow execution result"""
    task: str
    solver_output: str
    judge_review: Optional[ReviewResult] = None
    evaluator_assessment: Optional[MetaEvaluationResult] = None
    improved_output: Optional[str] = None
    final_score: float = 0.0
    success: bool = False
    iterations: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "solver_output": self.solver_output[:500] + "..." if len(self.solver_output) > 500 else self.solver_output,
            "judge_review": self.judge_review.to_dict() if self.judge_review else None,
            "evaluator_assessment": self.evaluator_assessment.to_dict() if self.evaluator_assessment else None,
            "final_score": self.final_score,
            "success": self.success,
            "iterations": self.iterations,
            "metadata": self.metadata,
        }

    def summary(self) -> str:
        """Generate summary"""
        lines = [
            f"Task: {self.task[:100]}...",
            f"Success: {self.success}",
            f"Final Score: {self.final_score:.1f}/10",
            f"Iterations: {self.iterations}",
        ]
        if self.judge_review:
            lines.append(f"Verdict: {self.judge_review.verdict}")
        return "\n".join(lines)


class BasicResearchWorkflow:
    """
    v0.1 Basic Research Workflow

    Orchestrates Solver-Judge-Evaluator collaboration:
    1. Solver executes task
    2. Judge evaluates result
    3. If score is low (< threshold), let Solver improve
    4. Evaluator performs meta-evaluation
    5. Record complete trajectory
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        improvement_threshold: float = 6.0,
        max_improvement_iterations: int = 2,
        enable_evaluator: bool = True,
        save_dir: Optional[Path] = None,
    ):
        """
        Initialize workflow

        Args:
            config: Configuration (optional, loads from environment by default)
            improvement_threshold: Improvement threshold, triggers improvement if below this score
            max_improvement_iterations: Maximum improvement iterations
            enable_evaluator: Whether to enable Evaluator
            save_dir: Trajectory save directory
        """
        self.config = config or get_config()
        self.improvement_threshold = improvement_threshold
        self.max_improvement_iterations = max_improvement_iterations
        self.enable_evaluator = enable_evaluator
        self.save_dir = save_dir or self.config.trajectory.save_dir

    def run(
        self,
        task: str,
        workspace_root: Optional[Path] = None,
        task_category: str = "other",
        domain: str = "",
        on_event: Optional[callable] = None,
    ) -> WorkflowResult:
        """
        Execute workflow

        Args:
            task: Task description
            workspace_root: Workspace directory
            task_category: Task type
            domain: Research domain
            on_event: Event callback

        Returns:
            WorkflowResult
        """
        workspace = workspace_root or self.config.workspace_root or Path.cwd()

        # Create workflow trajectory recorder
        trajectory_recorder = WorkflowTrajectoryRecorder(
            task=task,
            model_name=self.config.model.model_name,
            workspace_root=workspace,
            save_dir=self.save_dir,
            task_category=task_category,
            domain=domain,
        )

        # 1. Solver executes task
        print("\n" + "=" * 50)
        print("Phase 1: Solver executing task...")
        print("=" * 50)

        solver = SolverAgent(
            workspace_root=workspace,
            on_event=on_event,
        )
        solver_result = solver.run(task)
        trajectory_recorder.collect_from_recorder(solver.trajectory_recorder)

        solver_output = solver_result.output
        iterations = 1

        # 2. Judge evaluates result
        print("\n" + "=" * 50)
        print("Phase 2: Judge reviewing output...")
        print("=" * 50)

        judge = JudgeAgent(on_event=on_event)
        judge_review = judge.review(
            artifact=solver_output,
            artifact_type="research_output",
        )
        trajectory_recorder.collect_from_recorder(judge.trajectory_recorder)

        print(f"Judge Score: {judge_review.overall_score:.1f}/10")
        print(f"Verdict: {judge_review.verdict}")

        # 3. If score is low, trigger improvement
        improved_output = None
        while (judge_review.overall_score < self.improvement_threshold
               and iterations < self.max_improvement_iterations):

            print("\n" + "=" * 50)
            print(f"Phase 2.{iterations}: Improvement iteration {iterations}...")
            print("=" * 50)

            # Build improvement request
            from markscientist.prompts.v01_prompts import IMPROVEMENT_REQUEST_TEMPLATE

            improvement_task = IMPROVEMENT_REQUEST_TEMPLATE.format(
                original_output=solver_output,
                review_feedback=judge_review.raw_output,
            )

            # Create new Solver for improvement
            improvement_solver = SolverAgent(
                workspace_root=workspace,
                on_event=on_event,
            )
            improvement_result = improvement_solver.run(improvement_task)
            trajectory_recorder.collect_from_recorder(improvement_solver.trajectory_recorder)

            improved_output = improvement_result.output
            iterations += 1

            # Re-evaluate
            improvement_judge = JudgeAgent(on_event=on_event)
            judge_review = improvement_judge.review(
                artifact=improved_output,
                artifact_type="improved_research_output",
            )
            trajectory_recorder.collect_from_recorder(improvement_judge.trajectory_recorder)

            print(f"Improved Score: {judge_review.overall_score:.1f}/10")

            # Update output
            if judge_review.overall_score > self.improvement_threshold:
                solver_output = improved_output

        # 4. Evaluator meta-evaluation (optional)
        evaluator_assessment = None
        if self.enable_evaluator:
            print("\n" + "=" * 50)
            print("Phase 3: Evaluator meta-assessment...")
            print("=" * 50)

            evaluator = EvaluatorAgent(on_event=on_event)
            evaluator_assessment = evaluator.evaluate(
                original_task=task,
                solver_output=solver_output,
                judge_review=judge_review.raw_output,
                final_result=improved_output or solver_output,
            )
            trajectory_recorder.collect_from_recorder(evaluator.trajectory_recorder)

            print(f"Success Probability: {evaluator_assessment.success_probability:.1%}")

        # 5. Complete trajectory recording
        quality_scores = {
            "overall_score": judge_review.overall_score,
            **judge_review.dimension_scores,
        }

        trajectory_recorder.complete(
            final_output=improved_output or solver_output,
            success=judge_review.overall_score >= self.improvement_threshold,
            quality_scores=quality_scores,
        )

        # Return result
        return WorkflowResult(
            task=task,
            solver_output=solver_output,
            judge_review=judge_review,
            evaluator_assessment=evaluator_assessment,
            improved_output=improved_output,
            final_score=judge_review.overall_score,
            success=judge_review.overall_score >= self.improvement_threshold,
            iterations=iterations,
            metadata={
                "trajectory_id": trajectory_recorder.get_record().trajectory_id,
                "workspace": str(workspace),
            },
        )


def run_quick_task(
    task: str,
    workspace_root: Optional[Path] = None,
    agent_type: str = "solver",
) -> str:
    """
    Quickly execute a single task (without full workflow)

    Args:
        task: Task description
        workspace_root: Workspace directory
        agent_type: Agent type (solver | judge | evaluator)

    Returns:
        Task output
    """
    workspace = workspace_root or Path.cwd()

    if agent_type == "solver":
        agent = SolverAgent(workspace_root=workspace)
    elif agent_type == "judge":
        agent = JudgeAgent(workspace_root=workspace)
    elif agent_type == "evaluator":
        agent = EvaluatorAgent(workspace_root=workspace)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

    result = agent.run(task)
    return result.output
