"""
MarkScientist Models Module

Provides model abstraction layer supporting multiple backends:
- OpenAI (GPT-4, etc.)
- Anthropic (Claude)
- Custom (v1.0 self-trained models)
"""

from markscientist.models.base import BaseModel, ModelConfig, get_model
from markscientist.models.openai_model import OpenAIModel

__all__ = [
    "BaseModel",
    "ModelConfig",
    "get_model",
    "OpenAIModel",
]
