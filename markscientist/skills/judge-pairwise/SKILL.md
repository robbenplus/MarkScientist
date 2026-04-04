---
name: judge-pairwise
description: Head-to-head revision judging for scientific artifacts, inspired by pairwise evaluation methods such as AlpacaEval-style comparisons.
---

## Overview

- Use this skill when the key question is whether a revised artifact is actually better than a previous one.
- The emphasis is comparative judgment: identify real improvement, regression, or tie, rather than scoring each artifact in isolation.
- This skill is best for revision review, rebuttal review, and before-versus-after report comparison.

## Use When

- The workflow has two versions of a report, section, or response and needs to know which one is stronger.
- The decision should focus on net improvement, regression risk, and evidence gain.
- A simple absolute score would hide whether the new version truly fixed earlier weaknesses.

## Evaluation Workflow

- Compare the older and newer artifacts against the same checklist and scientific standard.
- Identify concrete improvements, regressions, and unresolved weaknesses.
- Prefer the version with stronger evidence, tighter claims, and better checklist completion.
- If neither version clearly improves the science, return a tie or conservative recommendation.

## Output Contract

- State which version is better and why.
- Ground the comparison in specific changes to evidence, claims, figures, code, or validation.
- Highlight unresolved weaknesses that still block acceptance even if the new version is better.

## Bias Controls

- Do not assume longer or newer means better.
- Do not reward cosmetic rewrites when the scientific substance is unchanged.
- Penalize regressions in rigor, traceability, or reproducibility even if presentation improved.
