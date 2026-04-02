"""
MarkScientist Agents Module

Three specialized agent types:
- SolverAgent: Execution type, responsible for completing specific research tasks
- JudgeAgent: Evaluation type, responsible for evaluating research output quality
- EvaluatorAgent: Meta-evaluation type, responsible for evaluating system performance
"""

from markscientist.agents.base import BaseAgent, AgentResult
from markscientist.agents.solver import SolverAgent
from markscientist.agents.judge import JudgeAgent
from markscientist.agents.evaluator import EvaluatorAgent

__all__ = [
    "BaseAgent",
    "AgentResult",
    "SolverAgent",
    "JudgeAgent",
    "EvaluatorAgent",
]
