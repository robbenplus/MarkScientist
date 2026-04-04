---
name: judge-judgelm
description: Evidence-heavy claim scrutiny for scientific artifacts, inspired by JudgeLM-style critical review and overclaim detection.
---

## Overview

- Use this skill when the review should aggressively test whether claims are actually justified by the visible evidence.
- The emphasis is claim validation: check claim scope, locate supporting artifacts, and penalize unsupported extrapolation.
- This skill is especially useful for final report review, claim validation, and skeptical panel roles.

## Use When

- The artifact makes strong scientific claims that need evidence tracing.
- The workflow must detect overclaiming, missing support, or conclusions that outrun the data.
- The reviewer should behave skeptically and demand direct support from code, outputs, figures, or cited materials.

## Evaluation Workflow

- Enumerate the major claims before scoring them.
- For each important claim, look for direct support in the report, figures, outputs, code artifacts, or cited sources.
- Distinguish between measured results, justified interpretation, and speculation.
- Penalize claims that are plausible but not concretely supported by the available artifacts.

## Output Contract

- Return scores and feedback that make the claim-evidence gaps explicit.
- Highlight overclaim risk, unsupported inference, and missing validation steps.
- Give next actions that reduce claim scope or add missing evidence.

## Bias Controls

- Do not accept a claim because it sounds domain-plausible.
- Do not treat citations as proof when the current artifact has not reproduced or validated the cited claim.
- Be especially strict when the report uses definitive language without matching empirical support.
