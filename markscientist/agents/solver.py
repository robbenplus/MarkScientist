"""
MarkScientist Solver Agent

Execution-type agent, responsible for completing specific research tasks.
Based on ResearchHarness's ReAct pattern, with added trajectory recording.
"""

import json
import time
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path

from markscientist.agents.base import (
    BaseAgent,
    AgentResult,
    load_tools_from_harness,
    get_tool_executor,
)
from markscientist.models.base import ModelConfig
from markscientist.trajectory.schema import AgentType
from markscientist.prompts import SOLVER_SYSTEM_PROMPT


class SolverAgent(BaseAgent):
    """
    Solver Agent - Execution Type

    Responsible for understanding user requirements and using tools to complete research tasks.
    """

    agent_type = AgentType.SOLVER
    default_system_prompt = SOLVER_SYSTEM_PROMPT

    def __init__(
        self,
        model_config: Optional[ModelConfig] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        max_turns: int = 50,
        max_runtime_seconds: int = 9000,
        workspace_root: Optional[Path] = None,
        trace_path: Optional[Path] = None,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        # If no tools provided, load from ResearchHarness
        if tools is None:
            tools = load_tools_from_harness()

        super().__init__(
            model_config=model_config,
            system_prompt=system_prompt,
            tools=tools,
            max_turns=max_turns,
            max_runtime_seconds=max_runtime_seconds,
            workspace_root=workspace_root,
            trace_path=trace_path,
            on_event=on_event,
        )

        # Tool executor
        self._execute_tool = get_tool_executor()

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute task

        Implements ReAct loop:
        1. Think (done by model)
        2. Act (tool call)
        3. Observe (tool result)
        4. Repeat until complete
        """
        start_time = time.time()
        deadline = start_time + self.max_runtime_seconds

        # Build initial messages
        messages = self._build_messages(task, context)

        # Record initial messages
        self._record_system_and_user(messages)

        turn = 0
        final_output = ""
        termination_reason = "completed"

        while turn < self.max_turns:
            # Check timeout
            if time.time() > deadline:
                termination_reason = "timeout"
                break

            turn += 1

            # Call model
            response = self._call_model(messages)

            if response.get("status") == "error":
                termination_reason = "model_error"
                final_output = response.get("error", "Unknown model error")
                self.trajectory_recorder.record(
                    role="runtime",
                    text=final_output,
                    turn_index=turn,
                    error=final_output,
                )
                break

            content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])
            finish_reason = response.get("finish_reason", "")

            # Record assistant response
            tool_call_ids = [tc.get("id", "") for tc in tool_calls]
            tool_names = [tc.get("function", {}).get("name", "") for tc in tool_calls]
            tool_arguments = [
                json.loads(tc.get("function", {}).get("arguments", "{}"))
                if isinstance(tc.get("function", {}).get("arguments"), str)
                else tc.get("function", {}).get("arguments", {})
                for tc in tool_calls
            ]

            self.trajectory_recorder.record(
                role="assistant",
                text=content,
                turn_index=turn,
                tool_call_ids=tool_call_ids,
                tool_names=tool_names,
                tool_arguments=tool_arguments,
                finish_reason=finish_reason,
            )

            # Handle tool calls
            if tool_calls:
                # Add assistant message (with tool calls)
                messages.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls,
                })

                # Execute tools and collect results
                for tool_call in tool_calls:
                    tool_call_id = tool_call.get("id", "")
                    func = tool_call.get("function", {})
                    tool_name = func.get("name", "")
                    tool_args_raw = func.get("arguments", "{}")

                    try:
                        tool_args = json.loads(tool_args_raw) if isinstance(tool_args_raw, str) else tool_args_raw
                    except json.JSONDecodeError:
                        tool_args = {}

                    # Execute tool
                    try:
                        result = self._execute_tool(
                            tool_name,
                            tool_args,
                            workspace_root=self.workspace_root,
                        )
                    except Exception as e:
                        result = f"Error executing {tool_name}: {str(e)}"

                    # Format result
                    if isinstance(result, dict):
                        result_text = json.dumps(result, ensure_ascii=False)
                    else:
                        result_text = str(result)

                    # Record tool result
                    self.trajectory_recorder.record(
                        role="tool",
                        text=result_text,
                        turn_index=turn,
                        tool_call_ids=[tool_call_id],
                        tool_names=[tool_name],
                        tool_arguments=[tool_args],
                    )

                    # Add tool result message
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": result_text,
                    })

            elif content.strip():
                # No tool calls, has text output -> complete
                final_output = content.strip()
                messages.append({
                    "role": "assistant",
                    "content": final_output,
                })
                break

            else:
                # Empty response, request retry
                self.trajectory_recorder.record(
                    role="runtime",
                    text="Empty response, requesting retry",
                    turn_index=turn,
                    error="empty_response",
                )
                messages.append({
                    "role": "user",
                    "content": "Your previous response was empty. Please continue with the task.",
                })

        # If loop ends without output
        if not final_output and turn >= self.max_turns:
            termination_reason = "max_turns_reached"
            final_output = "Task could not be completed within the maximum number of turns."

        # Record final state
        self.trajectory_recorder.record(
            role="runtime",
            text=final_output,
            turn_index=turn,
            termination=termination_reason,
        )

        return AgentResult(
            output=final_output,
            success=termination_reason == "completed",
            termination_reason=termination_reason,
            events=self.get_trajectory(),
            metadata={
                "turns": turn,
                "duration_seconds": time.time() - start_time,
            },
        )
