"""
MarkScientist Prompts Module

v0.1 uses carefully designed prompts to simulate three agent types' behaviors.
"""

from markscientist.prompts.v01_prompts import (
    SOLVER_SYSTEM_PROMPT,
    JUDGE_SYSTEM_PROMPT,
    EVALUATOR_SYSTEM_PROMPT,
    get_agent_prompt,
)

__all__ = [
    "SOLVER_SYSTEM_PROMPT",
    "JUDGE_SYSTEM_PROMPT",
    "EVALUATOR_SYSTEM_PROMPT",
    "get_agent_prompt",
]
