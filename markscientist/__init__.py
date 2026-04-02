"""
MarkScientist v0.1 - Self-evolving Research Agent with Built-in Scientific Taste

Core modules:
- agents: Three specialized agent types
- prompts: Role-prompt definitions layered on top of ResearchHarness
- trajectory: Workflow-level trajectory wrappers around ResearchHarness traces
- workflow: Research workflows
"""

from typing import TYPE_CHECKING

__version__ = "0.1.0"
__author__ = "MarkScientist Team"

from markscientist.config import Config

if TYPE_CHECKING:
    from markscientist.agents.evaluator import EvaluatorAgent
    from markscientist.agents.judge import JudgeAgent
    from markscientist.agents.solver import SolverAgent


def __getattr__(name: str):
    if name == "SolverAgent":
        from markscientist.agents.solver import SolverAgent

        return SolverAgent
    if name == "JudgeAgent":
        from markscientist.agents.judge import JudgeAgent

        return JudgeAgent
    if name == "EvaluatorAgent":
        from markscientist.agents.evaluator import EvaluatorAgent

        return EvaluatorAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "Config",
    "SolverAgent",
    "JudgeAgent",
    "EvaluatorAgent",
    "__version__",
]
