from __future__ import annotations

from markscientist.agents.base import BaseScientistAgent
from markscientist.prompts import CHALLENGER_ROLE_PROMPT

from agent_base import agent_role


@agent_role(
    name="challenger",
    role_prompt=CHALLENGER_ROLE_PROMPT,
    function_list=["Glob", "Grep", "Read", "ReadPDF", "Write", "Edit", "Bash", "WebSearch", "ScholarSearch"],
)
class ChallengerAgent(BaseScientistAgent):
    """Project-scoping agent that prepares a research workspace."""

    agent_type = "challenger"
    max_llm_calls_override = 8
    max_runtime_seconds_override = 1200


@agent_role(
    name="challenger",
    role_prompt=CHALLENGER_ROLE_PROMPT,
    function_list=["Glob", "Grep", "Read", "ReadPDF", "Write", "Edit", "Bash"],
)
class ChallengerPackagingAgent(BaseScientistAgent):
    """Restricted challenge-packaging agent that cannot continue web discovery."""

    agent_type = "challenger_packaging"
    max_llm_calls_override = 10
    max_runtime_seconds_override = 600
