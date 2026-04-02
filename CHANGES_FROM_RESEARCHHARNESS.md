# MarkScientist v0.1 - Detailed Comparison with ResearchHarness

This document details the relationship between MarkScientist v0.1 and ResearchHarness, including which parts are inherited, added, or modified.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Project Relationship Diagram                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ResearchHarness                    MarkScientist v0.1              │
│  ┌─────────────────┐               ┌─────────────────┐              │
│  │                 │   Inherit     │                 │              │
│  │  Tool System    │─────────────→│  Tool System    │              │
│  │  (16 tools)     │               │  (same)         │              │
│  │                 │               │                 │              │
│  │  Trace Format   │─────────────→│  Extended Trace │              │
│  │  (JSONL)        │               │  (compatible+)  │              │
│  │                 │               │                 │              │
│  │  Safety         │─────────────→│  Safety         │              │
│  │  Mechanisms     │               │  (same)         │              │
│  │                 │               │                 │              │
│  │  ReAct Agent    │───Modify────→│  Three Agents   │              │
│  │  (single)       │               │  (Solver/Judge/ │              │
│  │                 │               │   Evaluator)    │              │
│  │                 │               │                 │              │
│  │  Prompt         │───Rewrite───→│  Specialized    │              │
│  │  (generic)      │               │  Prompts (3)    │              │
│  └─────────────────┘               │                 │              │
│                                    │  [NEW]          │              │
│                                    │  ├─ Model Layer │              │
│                                    │  ├─ Taste System│              │
│                                    │  ├─ Workflow    │              │
│                                    │  └─ Config      │              │
│                                    └─────────────────┘              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. Unchanged Parts (Directly Inherited)

### 1.1 Tool System (agent_base/tools/)

**Fully inherited, no modifications**

| File | Function | Description |
|------|----------|-------------|
| `tool_file.py` | File tools | Glob, Grep, Read, ReadPDF, ReadImage, Write, Edit |
| `tool_runtime.py` | Execution tools | Bash, TerminalStart/Write/Read/Interrupt/Kill |
| `tool_web.py` | Web tools | WebSearch, ScholarSearch, WebFetch |
| `tooling.py` | Tool base | ToolBase, path validation, security checks |

**Usage**:
```python
# MarkScientist imports ResearchHarness tools via path
from agent_base.tools.tool_file import Glob, Grep, Read
from agent_base.react_agent import AVAILABLE_TOOLS, AVAILABLE_TOOL_MAP
```

### 1.2 Safety Mechanisms (agent_base/tools/tooling.py)

**Fully inherited**

- `SENSITIVE_FILE_NAMES`: Sensitive file name list
- `SENSITIVE_PATH_PARTS`: Sensitive path components
- `SENSITIVE_COMMAND_TOKENS`: Sensitive command keywords
- `BLOCKED_COMMAND_PATTERNS`: Blocked command patterns
- `validate_tool_path()`: Path validation function
- `command_safety_issue()`: Command safety check
- `sanitized_subprocess_env()`: Sanitized environment variables

### 1.3 Utility Functions (agent_base/utils.py)

**Fully inherited**

- `load_dotenv()`: Environment variable loading
- `env_flag()`: Environment variable boolean parsing
- `safe_jsonable()`: Safe JSON serialization
- `append_jsonl()`: JSONL append
- `read_text_lossy()`: Fault-tolerant text reading
- `PROJECT_ROOT`: Project root directory

---

## 2. New Additions

### 2.1 Model Abstraction Layer (markscientist/models/)

**Completely new** - Key for v1.0 model switching

```
models/
├── __init__.py
├── base.py           # Base model class and factory function
├── openai_model.py   # OpenAI backend implementation
└── anthropic_model.py # Anthropic backend implementation
```

**Core interface**:
```python
class BaseModel(ABC):
    @abstractmethod
    def generate(self, messages, tools=None, **kwargs) -> Dict

    @abstractmethod
    def get_model_info(self) -> Dict

def get_model(config: ModelConfig) -> BaseModel:
    """Model factory - single entry point for model switching"""
```

**Design purpose**:
- v0.x: Use OpenAI/Anthropic APIs
- v1.0: Seamless switch to self-trained models

### 2.2 Three Agent Types (markscientist/agents/)

**Completely new** - Core innovation

```
agents/
├── __init__.py
├── base.py           # Agent base class
├── solver.py         # Solver Agent (execution type)
├── judge.py          # Judge Agent (evaluation type)
└── evaluator.py      # Evaluator Agent (meta-evaluation type)
```

| Agent | Responsibility | Tool Usage |
|-------|----------------|------------|
| **Solver** | Execute research tasks | Uses all 16 tools |
| **Judge** | Evaluate research quality | Does not use tools |
| **Evaluator** | Meta-evaluate system performance | Does not use tools |

### 2.3 Specialized Prompts (markscientist/prompts/)

**Completely new**

```
prompts/
├── __init__.py
└── v01_prompts.py    # v0.1 prompt definitions
```

Design goals for three prompt types:
- **SOLVER_SYSTEM_PROMPT**: Emphasizes evidence-first, scientific rigor, reproducibility
- **JUDGE_SYSTEM_PROMPT**: Defines evaluation dimensions, scoring criteria, output format
- **EVALUATOR_SYSTEM_PROMPT**: Defines meta-evaluation dimensions, system improvement directions

### 2.4 Trajectory Data System (markscientist/trajectory/)

**New** - Extends ResearchHarness trace format

```
trajectory/
├── __init__.py
├── schema.py         # Data schema definitions
└── recorder.py       # Trajectory recorder
```

**Extended fields** (on top of ResearchHarness):
```python
# New fields
agent_type: str       # solver | judge | evaluator
model_info: Dict      # Model information
reasoning_trace: str  # Reasoning trace (v0.2+)
quality_signals: Dict # Quality signals (v0.2+)
```

### 2.5 Workflow Orchestration (markscientist/workflow/)

**Completely new**

```
workflow/
├── __init__.py
└── basic.py          # Basic research workflow
```

**BasicResearchWorkflow** process:
1. Solver executes task
2. Judge evaluates result
3. If score is low, trigger improvement loop
4. Evaluator performs meta-evaluation
5. Save complete trajectory

### 2.6 Configuration System (markscientist/config.py)

**Completely new**

```python
@dataclass
class Config:
    model: ModelConfig        # Model configuration
    agent: AgentConfig        # Agent configuration
    trajectory: TrajectoryConfig  # Trajectory configuration
    workspace_root: Path      # Workspace
    harness_path: Path        # ResearchHarness path
```

### 2.7 CLI Entry Point (markscientist/cli.py)

**Completely new**

```bash
# Usage
python -m markscientist.cli "task description"
python -m markscientist.cli "task" --agent judge
python -m markscientist.cli "task" --workflow
```

---

## 3. Modified/Refactored Parts

### 3.1 ReAct Agent → Three Agent Types

**Original** (ResearchHarness):
```python
# agent_base/react_agent.py
class MultiTurnReactAgent:
    def run(self, user_input, workspace_dir=None) -> str
```

**Refactored** (MarkScientist):
```python
# markscientist/agents/base.py
class BaseAgent(ABC):
    agent_type: AgentType

    @abstractmethod
    def run(self, task, context=None) -> AgentResult

# markscientist/agents/solver.py
class SolverAgent(BaseAgent):
    agent_type = AgentType.SOLVER
    # Inherits ReAct loop, adds trajectory recording

# markscientist/agents/judge.py
class JudgeAgent(BaseAgent):
    agent_type = AgentType.JUDGE
    # Dedicated to evaluation, does not use tools

# markscientist/agents/evaluator.py
class EvaluatorAgent(BaseAgent):
    agent_type = AgentType.EVALUATOR
    # Dedicated to meta-evaluation
```

### 3.2 Extended Trace Format

**Original** (ResearchHarness - trace_utils.py):
```python
TRACE_FIELD_NAMES = [
    "run_id",
    "event_index",
    "turn_index",
    "timestamp",
    "model_name",
    "workspace_root",
    "role",
    "text",
    "tool_call_ids",
    "tool_names",
    "tool_arguments",
    "finish_reason",
    "termination",
    "error",
    "image_paths",
]
```

**Extended** (MarkScientist - trajectory/schema.py):
```python
TRACE_FIELD_NAMES = [
    # Original fields (all preserved)
    "run_id",
    "event_index",
    # ... (same as above)

    # New fields
    "agent_type",       # solver | judge | evaluator
    "model_info",       # Detailed model information
    "reasoning_trace",  # Reasoning process (v0.2+)
    "quality_signals",  # Quality signals (v0.2+)
]
```

### 3.3 Prompt Design

**Original** (ResearchHarness - prompt.py):
- Generic `SYSTEM_PROMPT`
- Primarily focused on tool usage specifications

**Refactored** (MarkScientist - prompts/v01_prompts.py):
- Three specialized prompts
- Added scientific taste dimensions
- Added output format specifications (for future training)

---

## 4. File Mapping Table

### ResearchHarness File Usage

| ResearchHarness File | Usage in MarkScientist |
|----------------------|------------------------|
| `agent_base/__init__.py` | Used via path import |
| `agent_base/react_agent.py` | Inherits tool system, refactors agent logic |
| `agent_base/trace_utils.py` | Inherits format, extends fields |
| `agent_base/prompt.py` | Rewritten as three specialized prompts |
| `agent_base/console_utils.py` | Referenced but reimplemented |
| `agent_base/utils.py` | Used directly |
| `agent_base/tools/` | Fully inherited, no modifications |

### MarkScientist New Files

| File | Description |
|------|-------------|
| `markscientist/__init__.py` | Package entry |
| `markscientist/config.py` | Configuration system |
| `markscientist/cli.py` | CLI entry point |
| `markscientist/models/*.py` | Model abstraction layer |
| `markscientist/agents/*.py` | Three agent types |
| `markscientist/prompts/*.py` | Specialized prompts |
| `markscientist/trajectory/*.py` | Trajectory system |
| `markscientist/workflow/*.py` | Workflow orchestration |

---

## 5. Dependencies

### MarkScientist → ResearchHarness

```
MarkScientist
├── Runtime Dependencies
│   ├── agent_base/tools/*.py (tool implementations)
│   ├── agent_base/react_agent.py (AVAILABLE_TOOLS)
│   └── agent_base/utils.py (utility functions)
│
└── Design References
    ├── agent_base/trace_utils.py (trace format)
    └── agent_base/prompt.py (prompt structure)
```

### Configuration

```bash
# Configure ResearchHarness path in .env
RESEARCHHARNESS_PATH=/home/zhangwenlong/ResearchHarness
```

Or in code:
```python
import sys
sys.path.insert(0, "/home/zhangwenlong/ResearchHarness")
from agent_base.react_agent import AVAILABLE_TOOLS
```

---

## 6. Future Version Plans

### v0.2 - Enhanced Data Collection
- Complete `reasoning_trace` field
- Add `quality_signals` automatic annotation
- User feedback collection system

### v0.3 - Workflow Enhancement
- More workflow templates
- Prompt A/B testing framework
- Workflow visualization

### v0.4 - User Adaptation
- User profiling system
- Personalized prompt injection
- Preference learning engine

### v0.5 - Taste System
- Complete rule library
- Hybrid scoring engine
- v1.0 preparation check

### v1.0 - Self-trained Models
- Add `custom_model.py` in `models/`
- Model switching without modifying other code
- User LoRA adapter support

---

## 7. Code Examples

### Minimal Usage

```python
from markscientist.agents import SolverAgent

# Use Solver to execute task
solver = SolverAgent()
result = solver.run("Analyze the time complexity of this code")
print(result.output)
```

### Using Judge for Review

```python
from markscientist.agents import JudgeAgent

judge = JudgeAgent()
review = judge.review(
    artifact="...",  # Content to review
    artifact_type="research_output"
)
print(f"Score: {review.overall_score}")
print(f"Weaknesses: {review.weaknesses}")
```

### Complete Workflow

```python
from markscientist.workflow import BasicResearchWorkflow

workflow = BasicResearchWorkflow()
result = workflow.run("Write a literature review on reinforcement learning")

print(f"Final Score: {result.final_score}")
print(f"Output: {result.solver_output}")
```

---

*Document version: 1.0*
*Created: 2026-04-02*
*Applicable to: MarkScientist v0.1*
