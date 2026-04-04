---
name: judge-pandalm
description: Balanced scientific artifact judging with explicit tie handling and stable cross-example calibration, inspired by PandaLM-style evaluation.
---

## Overview

- Use this skill when the review needs balanced, reproducible judgment over complete research reports.
- The emphasis is calibrated evaluation: weigh multiple dimensions, keep decisions stable, and avoid overreacting to one flashy section.
- This skill works well for final report review and benchmark-level acceptance decisions.

## Use When

- The artifact is a full report or end-to-end deliverable rather than a narrow subcomponent.
- The workflow needs a balanced judgment that integrates rigor, novelty, clarity, and reproducibility.
- The review should explicitly handle borderline cases instead of forcing an overconfident verdict.

## Evaluation Workflow

- Inspect the report as a complete scientific artifact, including code-backed outputs and figures.
- Balance strengths and weaknesses across methodology, results, limitations, and reproducibility.
- Treat unsupported core claims or missing artifacts as decisive negatives even when presentation is strong.
- Use calibrated scoring that reflects the artifact's benchmark readiness, not just local improvement.

## Output Contract

- Return a balanced overall score plus a clear explanation of the main acceptance blockers.
- Surface both strong aspects and limiting weaknesses so the workflow can improve efficiently.
- Keep the final recommendation aligned with benchmark readiness, not with effort or narrative quality alone.

## Bias Controls

- Avoid score inflation from polished writing or visually attractive figures alone.
- Do not let one excellent section override missing core evidence elsewhere in the report.
- Prefer stable, benchmark-consistent scoring over dramatic swing judgments.
