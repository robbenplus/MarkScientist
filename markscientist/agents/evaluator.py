"""
MarkScientist Evaluator Agent

Meta-evaluation Agent, responsible for evaluating the performance of Solver and Judge.
Used to form a closed loop for system improvement.
"""

import json
import re
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, field

from markscientist.agents.base import BaseAgent, AgentResult
from markscientist.models.base import ModelConfig
from markscientist.trajectory.schema import AgentType
from markscientist.prompts import EVALUATOR_SYSTEM_PROMPT


@dataclass
class MetaEvaluationResult:
    """Meta-evaluation result"""
    solver_assessment: Dict[str, Any] = field(default_factory=dict)
    judge_assessment: Dict[str, Any] = field(default_factory=dict)
    system_insights: Dict[str, Any] = field(default_factory=dict)
    success_probability: float = 0.0
    confidence: float = 0.0
    meta_summary: str = ""
    raw_output: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "solver_assessment": self.solver_assessment,
            "judge_assessment": self.judge_assessment,
            "system_insights": self.system_insights,
            "success_probability": self.success_probability,
            "confidence": self.confidence,
            "meta_summary": self.meta_summary,
        }


class EvaluatorAgent(BaseAgent):
    """
    Evaluator Agent - Meta-evaluation Type

    Responsible for evaluating the performance of the entire system,
    identifying systematic issues, and proposing improvement suggestions.
    """

    agent_type = AgentType.EVALUATOR
    default_system_prompt = EVALUATOR_SYSTEM_PROMPT

    def __init__(
        self,
        model_config: Optional[ModelConfig] = None,
        system_prompt: Optional[str] = None,
        max_turns: int = 3,
        max_runtime_seconds: int = 300,
        workspace_root: Optional[Path] = None,
        trace_path: Optional[Path] = None,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        super().__init__(
            model_config=model_config,
            system_prompt=system_prompt,
            tools=[],  # Evaluator doesn't use tools
            max_turns=max_turns,
            max_runtime_seconds=max_runtime_seconds,
            workspace_root=workspace_root,
            trace_path=trace_path,
            on_event=on_event,
        )

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute meta-evaluation task

        Args:
            task: Evaluation content
            context: Additional context

        Returns:
            AgentResult
        """
        messages = self._build_messages(task, context)
        self._record_system_and_user(messages)

        response = self._call_model(messages)

        if response.get("status") == "error":
            error_msg = response.get("error", "Unknown error")
            self.trajectory_recorder.record(
                role="runtime",
                text=error_msg,
                turn_index=1,
                error=error_msg,
            )
            return AgentResult(
                output=error_msg,
                success=False,
                termination_reason="model_error",
                events=self.get_trajectory(),
            )

        content = response.get("content", "")

        self.trajectory_recorder.record(
            role="assistant",
            text=content,
            turn_index=1,
            finish_reason=response.get("finish_reason", ""),
        )

        return AgentResult(
            output=content,
            success=True,
            termination_reason="completed",
            events=self.get_trajectory(),
        )

    def evaluate(
        self,
        original_task: str,
        solver_output: str,
        judge_review: str,
        solver_trajectory_summary: Optional[str] = None,
        final_result: Optional[str] = None,
    ) -> MetaEvaluationResult:
        """
        Conduct meta-evaluation on Solver-Judge interaction

        Args:
            original_task: Original task
            solver_output: Solver's output
            judge_review: Judge's review
            solver_trajectory_summary: Solver trajectory summary
            final_result: Final result

        Returns:
            MetaEvaluationResult
        """
        from markscientist.prompts.v01_prompts import META_EVALUATION_TEMPLATE

        task = META_EVALUATION_TEMPLATE.format(
            original_task=original_task,
            solver_output=solver_output[:2000] if len(solver_output) > 2000 else solver_output,
            solver_trajectory_summary=solver_trajectory_summary or "Not provided",
            judge_review=judge_review,
            final_result=final_result or solver_output[:500],
        )

        result = self.run(task)

        return self._parse_evaluation_result(result.output)

    def _parse_evaluation_result(self, raw_output: str) -> MetaEvaluationResult:
        """Parse meta-evaluation result"""
        evaluation = MetaEvaluationResult(raw_output=raw_output)

        # Try to extract JSON
        json_match = re.search(r'\{[\s\S]*\}', raw_output)
        if json_match:
            try:
                data = json.loads(json_match.group())

                evaluation.solver_assessment = data.get("solver_assessment", {})
                evaluation.judge_assessment = data.get("judge_assessment", {})
                evaluation.system_insights = data.get("system_insights", {})
                evaluation.success_probability = float(data.get("success_probability", 0))
                evaluation.confidence = float(data.get("confidence", 0))
                evaluation.meta_summary = data.get("meta_summary", "")

            except (json.JSONDecodeError, ValueError, KeyError):
                evaluation.meta_summary = raw_output[:500]

        return evaluation

    def assess_solver(
        self,
        task: str,
        solver_output: str,
        solver_trajectory: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate Solver's performance separately

        Args:
            task: Original task
            solver_output: Solver output
            solver_trajectory: Solver trajectory

        Returns:
            Evaluation result
        """
        trajectory_summary = ""
        if solver_trajectory:
            # Brief trajectory summary
            tool_calls = []
            for event in solver_trajectory:
                if event.get("tool_names"):
                    tool_calls.extend(event["tool_names"])
            trajectory_summary = f"Tool calls: {', '.join(tool_calls[:10])}"
            if len(tool_calls) > 10:
                trajectory_summary += f" ... and {len(tool_calls) - 10} more"

        eval_task = f"""Please evaluate the following Solver Agent's performance:

## Original Task
{task}

## Solver Output
{solver_output[:2000]}

## Execution Summary
{trajectory_summary or "Not available"}

Please evaluate Solver's:
1. Task completion quality
2. Execution efficiency
3. Reasoning quality
4. Error handling

Output evaluation result in JSON format.
"""

        result = self.run(eval_task)

        json_match = re.search(r'\{[\s\S]*\}', result.output)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {"raw_output": result.output}

    def assess_judge(
        self,
        artifact: str,
        judge_review: str,
        ground_truth: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate Judge's review quality

        Args:
            artifact: Reviewed content
            judge_review: Judge's review
            ground_truth: Ground truth evaluation (if available)

        Returns:
            Evaluation result
        """
        eval_task = f"""Please evaluate the following Judge Agent's review quality:

## Reviewed Content (Summary)
{artifact[:1000]}

## Judge Review
{judge_review}

{f"## Reference Standard {json.dumps(ground_truth, ensure_ascii=False)}" if ground_truth else ""}

Please evaluate Judge's:
1. Scoring accuracy
2. Issue identification coverage
3. Suggestion actionability
4. Evaluation consistency

Output evaluation result in JSON format.
"""

        result = self.run(eval_task)

        json_match = re.search(r'\{[\s\S]*\}', result.output)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {"raw_output": result.output}
