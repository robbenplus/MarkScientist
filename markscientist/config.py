"""
MarkScientist Configuration Management
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
import json


def _load_dotenv(path: Path) -> None:
    """Load environment variables from .env file."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass
class ModelConfig:
    """Model configuration"""
    backend: str = "openai"  # openai | anthropic | custom
    model_name: str = "gpt-4o"
    api_key: Optional[str] = None
    api_base: Optional[str] = None

    # Reserved fields for v1.0
    custom_model_path: Optional[str] = None
    adapter_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backend": self.backend,
            "model_name": self.model_name,
            "api_base": self.api_base,
            "custom_model_path": self.custom_model_path,
            "adapter_path": self.adapter_path,
        }


@dataclass
class AgentConfig:
    """Agent configuration"""
    max_llm_calls: int = 100
    max_runtime_seconds: int = 9000
    max_output_tokens: int = 10000
    max_input_tokens: int = 320000
    temperature: float = 0.6
    top_p: float = 0.95
    presence_penalty: float = 1.1


@dataclass
class TrajectoryConfig:
    """Trajectory configuration"""
    auto_save: bool = True
    save_dir: Path = field(default_factory=lambda: Path("./data/trajectories"))

    def __post_init__(self):
        if isinstance(self.save_dir, str):
            self.save_dir = Path(self.save_dir)


@dataclass
class Config:
    """MarkScientist main configuration"""

    model: ModelConfig = field(default_factory=ModelConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    trajectory: TrajectoryConfig = field(default_factory=TrajectoryConfig)
    workspace_root: Optional[Path] = None

    # ResearchHarness path (for importing tools)
    harness_path: Optional[Path] = None

    @classmethod
    def from_env(cls, env_path: Optional[Path] = None) -> "Config":
        """Load configuration from environment variables"""
        if env_path:
            _load_dotenv(env_path)
        else:
            # Try to load default .env
            default_env = Path(__file__).parent.parent / ".env"
            if default_env.exists():
                _load_dotenv(default_env)

        model = ModelConfig(
            backend=os.getenv("MODEL_BACKEND", "openai"),
            model_name=os.getenv("MODEL_NAME", "gpt-4o"),
            api_key=os.getenv("API_KEY"),
            api_base=os.getenv("API_BASE"),
        )

        agent = AgentConfig(
            max_llm_calls=int(os.getenv("MAX_LLM_CALL_PER_RUN", "100")),
            max_runtime_seconds=int(os.getenv("MAX_AGENT_RUNTIME_SECONDS", "9000")),
            max_output_tokens=int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "10000")),
            max_input_tokens=int(os.getenv("MAX_INPUT_TOKENS", "320000")),
            temperature=float(os.getenv("TEMPERATURE", "0.6")),
            top_p=float(os.getenv("TOP_P", "0.95")),
            presence_penalty=float(os.getenv("PRESENCE_PENALTY", "1.1")),
        )

        trajectory = TrajectoryConfig(
            auto_save=os.getenv("TRAJECTORY_AUTO_SAVE", "true").lower() == "true",
            save_dir=Path(os.getenv("TRAJECTORY_DIR", "./data/trajectories")),
        )

        workspace = os.getenv("WORKSPACE_ROOT")
        harness = os.getenv("RESEARCHHARNESS_PATH", "/home/zhangwenlong/ResearchHarness")

        return cls(
            model=model,
            agent=agent,
            trajectory=trajectory,
            workspace_root=Path(workspace) if workspace else None,
            harness_path=Path(harness) if harness else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model.to_dict(),
            "agent": {
                "max_llm_calls": self.agent.max_llm_calls,
                "max_runtime_seconds": self.agent.max_runtime_seconds,
                "temperature": self.agent.temperature,
            },
            "trajectory": {
                "auto_save": self.trajectory.auto_save,
                "save_dir": str(self.trajectory.save_dir),
            },
            "workspace_root": str(self.workspace_root) if self.workspace_root else None,
        }


# Global configuration instance
_global_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration"""
    global _global_config
    if _global_config is None:
        _global_config = Config.from_env()
    return _global_config


def set_config(config: Config) -> None:
    """Set global configuration"""
    global _global_config
    _global_config = config
