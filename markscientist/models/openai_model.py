"""
OpenAI Model Implementation

Supports OpenAI API and compatible interfaces (e.g., Azure OpenAI, local deployments)
"""

import json
import random
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI, APIError, APIConnectionError, APITimeoutError
import tiktoken

from markscientist.models.base import BaseModel, ModelConfig


class OpenAIModel(BaseModel):
    """OpenAI model implementation"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)

        if not config.api_key:
            raise ValueError("API key is required for OpenAI backend")

        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_base,
            timeout=600.0,
        )

        # Token counter
        try:
            self._encoding = tiktoken.encoding_for_model(config.model_name)
        except KeyError:
            self._encoding = tiktoken.get_encoding("cl100k_base")

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call OpenAI API to generate response

        Args:
            messages: Message list
            tools: Tool definition list
            **kwargs: Additional parameters (max_retries, timeout, etc.)

        Returns:
            Standardized response format
        """
        max_retries = kwargs.get("max_retries", 10)
        base_sleep = 1

        last_error = "unknown error"

        for attempt in range(max_retries):
            try:
                request_kwargs = {
                    "model": self.config.model_name,
                    "messages": messages,
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "top_p": kwargs.get("top_p", self.config.top_p),
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "presence_penalty": kwargs.get("presence_penalty", self.config.presence_penalty),
                }

                if tools:
                    request_kwargs["tools"] = tools
                    request_kwargs["tool_choice"] = "auto"
                    request_kwargs["parallel_tool_calls"] = True

                response = self._client.chat.completions.create(**request_kwargs)

                choice = response.choices[0]
                message = choice.message

                # Extract tool calls
                tool_calls = []
                if message.tool_calls:
                    for tc in message.tool_calls:
                        tool_calls.append({
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            }
                        })

                content = message.content or ""

                if content.strip() or tool_calls:
                    return {
                        "status": "ok",
                        "content": content,
                        "tool_calls": tool_calls,
                        "finish_reason": choice.finish_reason,
                    }
                else:
                    last_error = "empty response from API"

            except (APIError, APIConnectionError, APITimeoutError) as e:
                last_error = str(e)

            # Wait before retry
            if attempt < max_retries - 1:
                sleep_time = base_sleep * (2 ** attempt) + random.uniform(0, 1)
                sleep_time = min(sleep_time, 30)
                time.sleep(sleep_time)

        return {
            "status": "error",
            "error": f"OpenAI API error after {max_retries} retries: {last_error}",
            "content": "",
            "tool_calls": [],
        }

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "backend": "openai",
            "model_name": self.config.model_name,
            "api_base": self.config.api_base or "https://api.openai.com/v1",
        }

    def count_tokens(self, text: str) -> int:
        """Calculate token count accurately using tiktoken"""
        return len(self._encoding.encode(text))

    def count_messages_tokens(self, messages: List[Dict]) -> int:
        """Calculate total token count for message list"""
        total = 0
        for msg in messages:
            total += len(self._encoding.encode(msg.get("role", "")))
            content = msg.get("content", "")
            if isinstance(content, str):
                total += len(self._encoding.encode(content))
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        total += len(self._encoding.encode(part.get("text", "")))

            # Tool calls
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                total += len(self._encoding.encode(json.dumps(tool_calls)))

        return total
