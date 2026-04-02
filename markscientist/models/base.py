"""
MarkScientist Model Base Class

Provides a unified model interface supporting multiple backend implementations.
Design principle: Enable seamless switch to self-trained models in v1.0.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ModelConfig:
    """Model configuration"""
    backend: str  # "openai" | "anthropic" | "custom"
    model_name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None

    # Reserved fields for v1.0
    custom_model_path: Optional[str] = None
    adapter_path: Optional[str] = None

    # Generation parameters
    temperature: float = 0.6
    top_p: float = 0.95
    max_tokens: int = 10000
    presence_penalty: float = 1.1


class BaseModel(ABC):
    """
    Base Model Class - All models implement this interface

    The design goal of this abstraction layer is:
    1. v0.x: Use OpenAI/Anthropic APIs
    2. v1.0: Seamlessly switch to self-trained models
    """

    def __init__(self, config: ModelConfig):
        self.config = config

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response

        Args:
            messages: Message list, format [{"role": "user/assistant/system", "content": "..."}]
            tools: Tool definition list (optional)
            **kwargs: Additional parameters

        Returns:
            {
                "status": "ok" | "error",
                "content": "response text",
                "tool_calls": [...],  # if there are tool calls
                "finish_reason": "stop" | "tool_calls",
                "error": "error message"  # if status == "error"
            }
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Return model information for tracking

        Returns:
            {
                "backend": "openai" | "anthropic" | "custom",
                "model_name": "gpt-4o",
                "version": "...",
                ...
            }
        """
        pass

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count (can be overridden by subclasses for more accurate calculation)

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Default uses simple estimation: ~4 characters ≈ 1 token
        return len(text) // 4


def get_model(config: ModelConfig) -> BaseModel:
    """
    Model factory - Returns corresponding model based on configuration

    This is the single entry point for model switching.
    In v1.0, only need to add custom backend support here.
    """
    if config.backend == "openai":
        from markscientist.models.openai_model import OpenAIModel
        return OpenAIModel(config)

    elif config.backend == "anthropic":
        from markscientist.models.anthropic_model import AnthropicModel
        return AnthropicModel(config)

    elif config.backend == "custom":
        # To be implemented in v1.0
        raise NotImplementedError(
            "Custom trained model backend will be available in v1.0. "
            "Please use 'openai' or 'anthropic' backend for now."
        )

    else:
        raise ValueError(f"Unknown model backend: {config.backend}")
