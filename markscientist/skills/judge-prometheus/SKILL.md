---
name: judge-prometheus
description: Strict criterion-by-criterion grading for scientific work, inspired by Prometheus-style rubric evaluation.
---

## Overview

- Use this skill when the review should behave like a strict rubric grader rather than an open-ended critic.
- The emphasis is consistency: apply the stated criteria one by one and resist generous scoring when a requirement is only partially met.
- This skill is especially strong for project-definition review, reproducibility review, and benchmark gating decisions.

## Use When

- The task has explicit acceptance criteria or a weighted checklist.
- The review should separate "fully satisfied", "partially satisfied", and "missing" more sharply than a generic reviewer would.
- The workflow needs a dependable gate for accept, revise, or rechallenge decisions.

## Evaluation Workflow

- Read the task contract and checklist before reading the artifact conclusion.
- Grade each criterion independently against observable evidence.
- Distinguish between complete satisfaction, partial satisfaction, and unsupported claims.
- Keep the final score aligned with the weakest important unmet criterion instead of averaging away critical failures.

## Output Contract

- Return explicit scores, a short summary, and a decision that can route the workflow.
- Tie major deductions to concrete unmet checklist items.
- Produce suggestions that map directly onto missing artifacts, weak evidence, or scope flaws.

## Bias Controls

- Do not pass artifacts that sound reasonable but fail key checklist items.
- Do not soften deductions just because the effort appears substantial.
- Prefer conservative scoring when evidence is incomplete or ambiguous.
