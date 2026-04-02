<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-blue.svg" alt="version">
  <img src="https://img.shields.io/badge/python-3.10+-green.svg" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="license">
</p>

<h1 align="center">🔬 MarkScientist</h1>

<p align="center">
  <b>Self-evolving Research Agent with Built-in Scientific Taste</b>
</p>

<p align="center">
  <code>Solver</code> executes → <code>Judge</code> reviews → <code>Evaluator</code> improves
</p>

---

## ✨ Features

- **🤖 Three-Agent System** — Solver, Judge, Evaluator working together
- **🎯 Auto-Review** — Judge automatically scores Solver's output
- **🐾 Reviewer Buddies** — Fun ASCII characters for different task types
- **📊 8 Task Types** — Each with appropriate scoring dimensions
- **💾 Trajectory Recording** — Collect data for future model training

## 🚀 Quick Start

```bash
pip install -e .
markscientist
```

## 💬 Usage

### Interactive REPL

```bash
markscientist          # Start REPL (Solver + auto Judge review)
```

### 1. Solver Mode (Default, with Auto-Review)

```
[solver+judge] > What is the transformer architecture?

╭──────────────── Solver Output ────────────────╮
│ The Transformer was proposed in "Attention   │
│ Is All You Need" by Vaswani et al. in 2017...│
╰──────────────────────────────────────────────╯

((•)(•)) =•ω•= [•=•] /• •\ Summoning reviewer...

[•=•] EVAL-9000 appears! "Computing evaluation scores..."

╭─────────── The Objective Analyzer ───────────╮
│  Reaction   ✓ Excellent!                     │
│  Type       factual_query                    │
│  Score      8.5/10                           │
╰──────────────────────────────────────────────╯
```

### 2. Judge Mode (Review Artifacts)

```
[solver+judge] > /judge

[judge] > Review this code:
def fib(n): return fib(n-1)+fib(n-2) if n>1 else n

╭──────────────── Judge Review ─────────────────╮
│  Type       code_analysis                     │
│  Score      5.5/10                            │
│  Details    correctness: 7.0 | efficiency: 3.0│
│  Issues     No memoization; O(2^n) complexity │
╰───────────────────────────────────────────────╯
```

### 3. Evaluator Mode (Meta-Evaluation)

Evaluates the performance of Solver and Judge themselves.

```
[judge] > /evaluator

[evaluator] > Evaluate the system's performance on the last task

╭────────────── Meta Evaluation ────────────────╮
│  Solver Assessment                            │
│    task_completion: 0.85                      │
│    efficiency: 0.70                           │
│    reasoning_quality: 0.80                    │
│                                               │
│  Judge Assessment                             │
│    scoring_accuracy: 0.90                     │
│    issue_coverage: 0.75                       │
│    suggestion_actionability: 0.80             │
│                                               │
│  System Insights                              │
│    bottleneck: Solver lacks systematic testing│
│    suggestion: Add auto test case generation  │
│                                               │
│  Success Probability: 0.78                    │
╰───────────────────────────────────────────────╯
```

### 4. Workflow Mode (Full Pipeline)

Runs Solver → Judge → Auto-Improve loop until score >= 6.0

```
[solver+judge] > /workflow Write a literature review on RL for robotics

⠋ Running workflow...

╭──────────────── Final Output ─────────────────╮
│ # Literature Review: RL for Robotics          │
│ ## 1. Introduction ...                        │
│ ## 2. Key Methods ...                         │
╰───────────────────────────────────────────────╯

╭─────────── Workflow Complete ─────────────────╮
│  Status      Success                          │
│  Final Score 7.8/10                           │
│  Iterations  2                                │
│  Verdict     ACCEPT                           │
╰───────────────────────────────────────────────╯
```

### CLI One-Shot Commands

```bash
# Solver + Judge (default)
markscientist "Explain quicksort algorithm"

# Solver only (no auto-review)
markscientist "Explain quicksort" --no-review

# Judge only
markscientist "Review this code..." --agent judge

# Evaluator only
markscientist "Assess system performance" --agent evaluator

# Full workflow with improvement loop
markscientist "Write a research proposal" --workflow

# JSON output
markscientist "Analyze this data" --json
```

### Python API

```python
from markscientist.agents import SolverAgent, JudgeAgent, EvaluatorAgent
from markscientist.models.base import ModelConfig

config = ModelConfig(backend="openai", model_name="gpt-4o")

# Solver: Execute tasks
solver = SolverAgent(model_config=config)
result = solver.run("Implement binary search")
print(result.output)

# Judge: Review artifacts
judge = JudgeAgent(model_config=config)
review = judge.review(artifact=result.output, artifact_type="code")
print(f"Score: {review.overall_score}/10")
print(f"Issues: {review.weaknesses}")

# Evaluator: Meta-evaluate Solver + Judge
evaluator = EvaluatorAgent(model_config=config)
meta = evaluator.evaluate(
    original_task="Implement binary search",
    solver_output=result.output,
    judge_review=review.summary,
)
print(f"Success Probability: {meta.success_probability}")
print(f"System Insights: {meta.system_insights}")
```

## 🐾 Reviewer Buddies

| Buddy | Name | Focus |
|:-----:|------|-------|
| `((•)(•))` | Professor Owl | Methodology |
| `=•ω•=` | Dr. Whiskers | Details |
| `[•=•]` | EVAL-9000 | Metrics |
| `<•~•>` | Elder Dragon | Big Picture |
| `/• •\` | The Specter | Hidden Issues |
| `~(••)~` | Dr. Tentacle | Multi-angle |

## 📋 Commands

```
/help       Show commands        /workflow   Full pipeline
/solver     Solver mode          /review     Toggle auto-review
/judge      Judge mode           /model      Switch model
/evaluator  Evaluator mode       /clear      New session
```

## 🎯 Task Types

| Type | Scoring Dimensions |
|------|-------------------|
| `factual_query` | accuracy, completeness, clarity |
| `idea_proposal` | novelty, rigor, feasibility |
| `code_analysis` | correctness, depth, clarity |
| `literature_review` | coverage, synthesis, organization |
| `experiment_design` | methodology, validity, reproducibility |
| `writing_draft` | structure, clarity, coherence |
| `data_analysis` | accuracy, interpretation, visualization |
| `problem_solving` | correctness, efficiency, explanation |

## ⚙️ Config

```bash
# .env
API_KEY=your-key
MODEL_NAME=gpt-4o
MODEL_BACKEND=openai
```

## 🗺️ Roadmap

- [x] v0.1 — Three agents, multi-type Judge, Buddies
- [ ] v0.2 — Enhanced data collection
- [ ] v0.3 — Workflow optimization
- [ ] v1.0 — Self-trained model integration

## 📄 License

MIT
