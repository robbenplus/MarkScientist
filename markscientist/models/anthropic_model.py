"""
Anthropic Model Implementation

Supports Anthropic Claude API
"""

import time
import random
from typing import Any, Dict, List, Optional

from markscientist.models.base import BaseModel, ModelConfig


class AnthropicModel(BaseModel):
    """Anthropic Claude model implementation"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)

        if not config.api_key:
            raise ValueError("API key is required for Anthropic backend")

        try:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=config.api_key)
        except ImportError:
            raise ImportError("Please install anthropic package: pip install anthropic")

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call Anthropic API to generate response

        Needs to convert OpenAI format to Anthropic format
        """
        max_retries = kwargs.get("max_retries", 10)
        base_sleep = 1
        last_error = "unknown error"

        # Extract system prompt
        system_prompt = ""
        anthropic_messages = []

        for msg in messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
            else:
                anthropic_messages.append(msg)

        # Convert tool format (OpenAI -> Anthropic)
        anthropic_tools = None
        if tools:
            anthropic_tools = []
            for tool in tools:
                func = tool.get("function", {})
                anthropic_tools.append({
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {}),
                })

        for attempt in range(max_retries):
            try:
                request_kwargs = {
                    "model": self.config.model_name,
                    "messages": anthropic_messages,
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                }

                if system_prompt:
                    request_kwargs["system"] = system_prompt

                if anthropic_tools:
                    request_kwargs["tools"] = anthropic_tools

                response = self._client.messages.create(**request_kwargs)

                # Parse response
                content = ""
                tool_calls = []

                for block in response.content:
                    if block.type == "text":
                        content += block.text
                    elif block.type == "tool_use":
                        tool_calls.append({
                            "id": block.id,
                            "type": "function",
                            "function": {
                                "name": block.name,
                                "arguments": str(block.input) if isinstance(block.input, dict)
                                             else block.input,
                            }
                        })

                if content.strip() or tool_calls:
                    return {
                        "status": "ok",
                        "content": content,
                        "tool_calls": tool_calls,
                        "finish_reason": response.stop_reason,
                    }
                else:
                    last_error = "empty response from API"

            except Exception as e:
                last_error = str(e)

            if attempt < max_retries - 1:
                sleep_time = base_sleep * (2 ** attempt) + random.uniform(0, 1)
                sleep_time = min(sleep_time, 30)
                time.sleep(sleep_time)

        return {
            "status": "error",
            "error": f"Anthropic API error after {max_retries} retries: {last_error}",
            "content": "",
            "tool_calls": [],
        }

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "backend": "anthropic",
            "model_name": self.config.model_name,
        }

    def count_tokens(self, text: str) -> int:
        """Estimate token count (Anthropic's accurate calculation requires API call)"""
        # Claude's tokenizer is similar to GPT, using approximation
        return len(text) // 4
