from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

from markscientist.agents.base import BaseScientistAgent
from markscientist.prompts import JUDGE_REQUEST_TEMPLATE, JUDGE_ROLE_PROMPT

from agent_base import agent_role


@dataclass
class ReviewResult:
    overall_score: float = 0.0
    project_score: float = 0.0
    report_score: float = 0.0
    verdict: str = ""
    summary: str = ""
    next_action: str = "solver_revision"
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    checklist_scores: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    raw_output: str = ""
    termination_reason: str = ""
    trace_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "project_score": self.project_score,
            "report_score": self.report_score,
            "verdict": self.verdict,
            "summary": self.summary,
            "next_action": self.next_action,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "suggestions": self.suggestions,
            "checklist_scores": self.checklist_scores,
            "confidence": self.confidence,
            "termination_reason": self.termination_reason,
            "trace_path": self.trace_path,
        }

    @property
    def output(self) -> str:
        return self.raw_output


def _build_review_prompt(
    *,
    original_prompt: str,
    instructions_text: str,
    challenge_brief: str,
    checklist_text: str,
    judge_materials_text: str,
    report_text: str,
) -> str:
    return JUDGE_REQUEST_TEMPLATE.format(
        original_prompt=original_prompt,
        instructions_text=instructions_text,
        challenge_brief=challenge_brief,
        checklist_text=checklist_text,
        judge_materials_text=judge_materials_text or "No judge-only materials were provided.",
        report_text=report_text,
    )


def _parse_review_output(raw_output: str) -> ReviewResult:
    review = ReviewResult(raw_output=raw_output)
    json_match = re.search(r"\{[\s\S]*\}", raw_output)
    if not json_match:
        review.summary = raw_output[:500]
        return review
    try:
        data = json.loads(json_match.group())
    except (json.JSONDecodeError, ValueError):
        review.summary = raw_output[:500]
        return review
    overall_score = data.get("overall_score")
    overall_value = float(overall_score or 0)
    review.project_score = float(data.get("project_score", overall_value))
    review.report_score = float(data.get("report_score", overall_value))
    if overall_score is None and (review.project_score or review.report_score):
        review.overall_score = min(review.project_score or review.report_score, review.report_score or review.project_score)
    else:
        review.overall_score = overall_value
    review.verdict = data.get("verdict", "")
    review.summary = data.get("summary", "")
    next_action = str(data.get("next_action", "solver_revision")).strip().lower()
    review.next_action = "rechallenge" if next_action == "rechallenge" else "solver_revision"
    review.strengths = data.get("strengths", [])
    review.weaknesses = data.get("weaknesses", [])
    review.suggestions = data.get("suggestions", [])
    review.checklist_scores = data.get("checklist_scores", [])
    review.confidence = float(data.get("confidence", 0))
    return review


@agent_role(name="judge", role_prompt=JUDGE_ROLE_PROMPT, function_list=[])
class JudgeAgent(BaseScientistAgent):
    """Strict report reviewer for prepared research projects."""

    agent_type = "judge"
