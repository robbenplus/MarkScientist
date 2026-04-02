"""
MarkScientist Judge Agent

Evaluation Agent, responsible for evaluating the quality of research outputs.
Core innovation: Accumulate data for future self-trained Judge model.
"""

import json
import re
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, field

from markscientist.agents.base import BaseAgent, AgentResult
from markscientist.models.base import ModelConfig
from markscientist.trajectory.schema import AgentType
from markscientist.prompts import JUDGE_SYSTEM_PROMPT


# Task type to dimension mapping
TASK_TYPE_DIMENSIONS = {
    "factual_query": ["accuracy", "completeness", "clarity", "citation"],
    "literature_review": ["coverage", "synthesis", "organization", "citation"],
    "code_analysis": ["correctness", "depth", "clarity", "actionability"],
    "idea_proposal": ["novelty", "rigor", "feasibility", "clarity"],
    "experiment_design": ["methodology", "validity", "reproducibility", "ethics"],
    "writing_draft": ["structure", "clarity", "coherence", "grammar"],
    "data_analysis": ["accuracy", "interpretation", "visualization", "limitations"],
    "problem_solving": ["correctness", "efficiency", "explanation", "alternatives"],
}


@dataclass
class ReviewResult:
    """Review result"""
    task_type: str = "unknown"
    overall_score: float = 0.0
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    verdict: str = ""
    summary: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    raw_output: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_type": self.task_type,
            "overall_score": self.overall_score,
            "dimension_scores": self.dimension_scores,
            "verdict": self.verdict,
            "summary": self.summary,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "confidence": self.confidence,
        }

    def get_dimension_names(self) -> List[str]:
        """Get expected dimension names for this task type."""
        return TASK_TYPE_DIMENSIONS.get(self.task_type, ["quality"])


class JudgeAgent(BaseAgent):
    """
    Judge Agent - Evaluation Type

    Responsible for evaluating research output quality, identifying issues,
    and providing improvement suggestions.

    Key feature: Multi-type evaluation - automatically detects task type
    and applies appropriate evaluation criteria.
    """

    agent_type = AgentType.JUDGE
    default_system_prompt = JUDGE_SYSTEM_PROMPT

    def __init__(
        self,
        model_config: Optional[ModelConfig] = None,
        system_prompt: Optional[str] = None,
        max_turns: int = 5,  # Judge typically doesn't need many turns
        max_runtime_seconds: int = 300,
        workspace_root: Optional[Path] = None,
        trace_path: Optional[Path] = None,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        super().__init__(
            model_config=model_config,
            system_prompt=system_prompt,
            tools=[],  # Judge doesn't use tools
            max_turns=max_turns,
            max_runtime_seconds=max_runtime_seconds,
            workspace_root=workspace_root,
            trace_path=trace_path,
            on_event=on_event,
        )

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute review task

        Args:
            task: Content to be reviewed
            context: Additional context (e.g., review type, specific requirements)

        Returns:
            AgentResult, where output is JSON format review result
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

    def review(
        self,
        artifact: str,
        artifact_type: str = "auto",
        requirements: Optional[str] = None,
    ) -> ReviewResult:
        """
        Review research output

        Args:
            artifact: Content to be reviewed
            artifact_type: Output type hint (auto = let Judge detect)
            requirements: Specific review requirements

        Returns:
            ReviewResult
        """
        from markscientist.prompts.v01_prompts import REVIEW_REQUEST_TEMPLATE

        # Prepare type hint
        if artifact_type == "auto":
            type_hint = "Please auto-detect the task type from the content"
        else:
            type_hint = f"Task type hint: {artifact_type}"

        task = REVIEW_REQUEST_TEMPLATE.format(
            artifact_type=type_hint,
            content=artifact,
            requirements=requirements or "Evaluate based on appropriate criteria for the detected task type",
        )

        result = self.run(task)

        # Parse review result
        return self._parse_review_result(result.output)

    def _parse_review_result(self, raw_output: str) -> ReviewResult:
        """
        Parse review result

        Attempt to extract JSON format review result from output.
        """
        review = ReviewResult(raw_output=raw_output)

        # Try to extract JSON
        json_match = re.search(r'\{[\s\S]*\}', raw_output)
        if json_match:
            try:
                data = json.loads(json_match.group())

                review.task_type = data.get("task_type", "unknown")
                review.overall_score = float(data.get("overall_score", 0))
                review.dimension_scores = data.get("dimension_scores", {})
                review.verdict = data.get("verdict", "")
                review.summary = data.get("summary", "")
                review.strengths = data.get("strengths", [])
                review.weaknesses = data.get("weaknesses", [])
                review.confidence = float(data.get("confidence", 0))

            except (json.JSONDecodeError, ValueError, KeyError):
                # Parse failed, use raw output
                review.summary = raw_output[:500]

        return review

    def quick_score(self, artifact: str) -> Dict[str, Any]:
        """
        Quick scoring without detailed review.

        Args:
            artifact: Content to score

        Returns:
            Dict with task_type, score, and brief verdict
        """
        task = f"""Quickly evaluate this output. Respond in JSON only:

Content:
{artifact[:1500]}

Required JSON format:
{{"task_type": "factual_query|literature_review|code_analysis|idea_proposal|experiment_design|writing_draft|data_analysis|problem_solving", "score": 1-10, "verdict": "one sentence"}}
"""
        result = self.run(task)

        json_match = re.search(r'\{[\s\S]*?\}', result.output)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {"task_type": "unknown", "score": 5, "verdict": "Could not parse"}

    def compare(
        self,
        artifact_a: str,
        artifact_b: str,
        comparison_criteria: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compare two research outputs

        Args:
            artifact_a: First output
            artifact_b: Second output
            comparison_criteria: Comparison dimensions (auto-detected if None)

        Returns:
            Comparison result
        """
        criteria_str = ""
        if comparison_criteria:
            criteria_str = f"Compare on these dimensions: {', '.join(comparison_criteria)}"
        else:
            criteria_str = "First detect the task type, then compare on appropriate dimensions."

        task = f"""Compare these two outputs and determine which is better.

## Output A
{artifact_a[:2000]}

## Output B
{artifact_b[:2000]}

## Instructions
{criteria_str}

Output JSON:
```json
{{
  "task_type": "detected type",
  "winner": "A" or "B" or "tie",
  "dimension_comparison": {{
    "dim1": {{"winner": "A/B/tie", "reason": "..."}},
    ...
  }},
  "overall_analysis": "...",
  "confidence": 0.8
}}
```
"""
        result = self.run(task)

        # Try to parse JSON
        json_match = re.search(r'\{[\s\S]*\}', result.output)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {
            "winner": "unknown",
            "raw_output": result.output,
        }
