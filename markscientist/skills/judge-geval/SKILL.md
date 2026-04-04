---
name: judge-geval
description: Multi-dimensional rubric judging for scientific artifacts, inspired by G-Eval style stepwise evaluation.
---

## Overview

- Use this skill when the reviewer should score a scientific artifact against several named dimensions rather than one overall impression.
- The emphasis is structured reasoning: inspect the artifact dimension by dimension, cite evidence, and then aggregate into a strict benchmark-style score.
- This skill is especially useful for project-definition review, experiment-design review, code review, and section-level report review.

## Use When

- The task requires criterion-by-criterion scoring such as rigor, novelty, reproducibility, scope control, or clarity.
- The artifact should be judged with an explicit rubric instead of informal prose.
- You need actionable feedback tied to distinct dimensions rather than one generic verdict.

## Evaluation Workflow

- Read the scenario contract, checklist, and artifact before scoring.
- Evaluate each dimension separately and ground each judgment in concrete evidence from the files.
- Penalize unsupported claims, missing artifacts, and vague checklist coverage.
- Aggregate the dimension-level findings into a final score and recommendation without ignoring the weakest critical dimension.

## Output Contract

- Return numeric scores on the requested scale.
- Include dimension-aware reasoning instead of only global commentary.
- Surface concrete strengths, weaknesses, and next actions that the next agent can execute immediately.

## Bias Controls

- Do not reward eloquent writing when the evidence is weak.
- Do not infer missing experiments, files, or figures from plausible prose.
- Keep the benchmark bar stable across turns and compare against the explicit checklist, not personal preference alone.
