from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class JudgeScenario(str, Enum):
    IDEA_GENERATION = "idea_generation"
    NOVELTY_CHECK = "novelty_check"
    PROJECT_DEFINITION = "project_definition"
    EXPERIMENT_DESIGN = "experiment_design"
    RESULT_ANALYSIS = "result_analysis"
    CLAIM_VALIDATION = "claim_validation"
    ABLATION_REVIEW = "ablation_review"
    PAPER_OUTLINE = "paper_outline"
    SECTION_DRAFT = "section_draft"
    FIGURE_TABLE = "figure_table"
    RESEARCH_REPORT = "research_report"
    REBUTTAL = "rebuttal"
    REVISION = "revision"
    CODE_REVIEW = "code_review"
    LITERATURE_REVIEW = "literature_review"


class JudgePerspective(str, Enum):
    SENIOR_REVIEWER = "senior_reviewer"
    NOVELTY_CRITIC = "novelty_critic"
    METHODS_EXPERT = "methods_expert"
    STATISTICS_EXPERT = "statistics_expert"
    WRITING_EXPERT = "writing_expert"
    DOMAIN_EXPERT = "domain_expert"
    LITERATURE_EXPERT = "literature_expert"
    CODE_EXPERT = "code_expert"
    REPRODUCIBILITY_ADVOCATE = "reproducibility_advocate"
    SKEPTIC = "skeptic"
    AREA_CHAIR = "area_chair"
    VISUALIZATION_EXPERT = "visualization_expert"


class JudgeSkill(str, Enum):
    GEVAL = "geval"
    PROMETHEUS = "prometheus"
    PAIRWISE = "pairwise"
    PANDALM = "pandalm"
    JUDGELM = "judgelm"


SCENARIO_CONFIGS: Dict[JudgeScenario, Dict[str, Any]] = {
    JudgeScenario.IDEA_GENERATION: {
        "description": "Evaluate brainstormed research ideas before they become a concrete project.",
        "dimensions": ("novelty", "feasibility", "impact", "clarity"),
        "strictness": "lenient",
        "recommended_roles": (
            JudgePerspective.NOVELTY_CRITIC,
            JudgePerspective.SENIOR_REVIEWER,
            JudgePerspective.AREA_CHAIR,
        ),
        "recommended_skill": JudgeSkill.GEVAL,
    },
    JudgeScenario.NOVELTY_CHECK: {
        "description": "Verify whether a proposed idea is genuinely differentiated from prior work.",
        "dimensions": ("originality", "differentiation", "gap_identification"),
        "strictness": "strict",
        "recommended_roles": (
            JudgePerspective.NOVELTY_CRITIC,
            JudgePerspective.LITERATURE_EXPERT,
            JudgePerspective.SKEPTIC,
        ),
        "recommended_skill": JudgeSkill.PAIRWISE,
    },
    JudgeScenario.PROJECT_DEFINITION: {
        "description": "Evaluate whether the prepared project is benchmark-quality, non-toy, grounded, and executable.",
        "dimensions": ("grounding", "scope", "executability", "scientific_value", "non_toy_quality"),
        "strictness": "strict",
        "recommended_roles": (
            JudgePerspective.METHODS_EXPERT,
            JudgePerspective.LITERATURE_EXPERT,
            JudgePerspective.AREA_CHAIR,
        ),
        "recommended_skill": JudgeSkill.PROMETHEUS,
    },
    JudgeScenario.EXPERIMENT_DESIGN: {
        "description": "Evaluate experiment plans, methodology, controls, and reproducibility before execution.",
        "dimensions": ("methodology", "validity", "reproducibility", "efficiency"),
        "strictness": "strict",
        "recommended_roles": (
            JudgePerspective.METHODS_EXPERT,
            JudgePerspective.REPRODUCIBILITY_ADVOCATE,
            JudgePerspective.SENIOR_REVIEWER,
        ),
        "recommended_skill": JudgeSkill.GEVAL,
    },
    JudgeScenario.RESULT_ANALYSIS: {
        "description": "Evaluate whether the experimental results are analyzed correctly and interpreted rigorously.",
        "dimensions": ("accuracy", "interpretation", "statistical_rigor", "limitations"),
        "strictness": "strict",
        "recommended_roles": (
            JudgePerspective.STATISTICS_EXPERT,
            JudgePerspective.METHODS_EXPERT,
            JudgePerspective.SKEPTIC,
        ),
        "recommended_skill": JudgeSkill.PROMETHEUS,
    },
    JudgeScenario.CLAIM_VALIDATION: {
        "description": "Check whether the report's claims are actually supported by the evidence and artifacts.",
        "dimensions": ("evidence_support", "claim_scope", "overclaim_risk"),
        "strictness": "very_strict",
        "recommended_roles": (
            JudgePerspective.SKEPTIC,
            JudgePerspective.AREA_CHAIR,
            JudgePerspective.REPRODUCIBILITY_ADVOCATE,
        ),
        "recommended_skill": JudgeSkill.JUDGELM,
    },
    JudgeScenario.ABLATION_REVIEW: {
        "description": "Evaluate whether ablation studies isolate the right variables and provide meaningful insight.",
        "dimensions": ("coverage", "isolation", "necessity", "insight"),
        "strictness": "strict",
        "recommended_roles": (
            JudgePerspective.METHODS_EXPERT,
            JudgePerspective.SENIOR_REVIEWER,
            JudgePerspective.STATISTICS_EXPERT,
        ),
        "recommended_skill": JudgeSkill.GEVAL,
    },
    JudgeScenario.PAPER_OUTLINE: {
        "description": "Evaluate the structure and planned flow of a paper outline.",
        "dimensions": ("structure", "flow", "completeness", "balance"),
        "strictness": "moderate",
        "recommended_roles": (
            JudgePerspective.WRITING_EXPERT,
            JudgePerspective.SENIOR_REVIEWER,
            JudgePerspective.AREA_CHAIR,
        ),
        "recommended_skill": JudgeSkill.PROMETHEUS,
    },
    JudgeScenario.SECTION_DRAFT: {
        "description": "Evaluate a draft paper section for clarity, technical depth, and coherence.",
        "dimensions": ("clarity", "coherence", "technical_depth", "conciseness"),
        "strictness": "moderate",
        "recommended_roles": (
            JudgePerspective.WRITING_EXPERT,
            JudgePerspective.DOMAIN_EXPERT,
            JudgePerspective.LITERATURE_EXPERT,
        ),
        "recommended_skill": JudgeSkill.GEVAL,
    },
    JudgeScenario.FIGURE_TABLE: {
        "description": "Evaluate figures and tables for clarity, informativeness, and presentation quality.",
        "dimensions": ("clarity", "informativeness", "aesthetics", "caption_quality"),
        "strictness": "moderate",
        "recommended_roles": (
            JudgePerspective.VISUALIZATION_EXPERT,
            JudgePerspective.WRITING_EXPERT,
            JudgePerspective.SENIOR_REVIEWER,
        ),
        "recommended_skill": JudgeSkill.PROMETHEUS,
    },
    JudgeScenario.RESEARCH_REPORT: {
        "description": "Evaluate the final research report and deliverables as a complete benchmark-quality scientific artifact.",
        "dimensions": ("novelty", "rigor", "clarity", "impact", "reproducibility"),
        "strictness": "strict",
        "recommended_roles": (
            JudgePerspective.AREA_CHAIR,
            JudgePerspective.SKEPTIC,
            JudgePerspective.REPRODUCIBILITY_ADVOCATE,
        ),
        "recommended_skill": JudgeSkill.PANDALM,
    },
    JudgeScenario.REBUTTAL: {
        "description": "Evaluate rebuttal responses for responsiveness, evidence, and clarity.",
        "dimensions": ("responsiveness", "evidence", "clarity", "diplomacy"),
        "strictness": "moderate",
        "recommended_roles": (
            JudgePerspective.SENIOR_REVIEWER,
            JudgePerspective.WRITING_EXPERT,
            JudgePerspective.AREA_CHAIR,
        ),
        "recommended_skill": JudgeSkill.PAIRWISE,
    },
    JudgeScenario.REVISION: {
        "description": "Evaluate whether a revised artifact materially improved over the previous version.",
        "dimensions": ("improvement", "completeness", "consistency"),
        "strictness": "strict",
        "recommended_roles": (
            JudgePerspective.SENIOR_REVIEWER,
            JudgePerspective.METHODS_EXPERT,
            JudgePerspective.AREA_CHAIR,
        ),
        "recommended_skill": JudgeSkill.PAIRWISE,
    },
    JudgeScenario.CODE_REVIEW: {
        "description": "Evaluate code quality, correctness, and reproducibility of the implementation.",
        "dimensions": ("correctness", "efficiency", "readability", "reproducibility"),
        "strictness": "strict",
        "recommended_roles": (
            JudgePerspective.CODE_EXPERT,
            JudgePerspective.REPRODUCIBILITY_ADVOCATE,
            JudgePerspective.METHODS_EXPERT,
        ),
        "recommended_skill": JudgeSkill.GEVAL,
    },
    JudgeScenario.LITERATURE_REVIEW: {
        "description": "Evaluate literature review coverage, synthesis, recency, and organization.",
        "dimensions": ("coverage", "synthesis", "organization", "recency"),
        "strictness": "moderate",
        "recommended_roles": (
            JudgePerspective.LITERATURE_EXPERT,
            JudgePerspective.DOMAIN_EXPERT,
            JudgePerspective.SENIOR_REVIEWER,
        ),
        "recommended_skill": JudgeSkill.PROMETHEUS,
    },
}


PERSPECTIVE_CONFIGS: Dict[JudgePerspective, Dict[str, str]] = {
    JudgePerspective.SENIOR_REVIEWER: {
        "title": "Senior Reviewer",
        "focus": "overall scientific quality and publishability",
        "guidance": "Weigh strengths and weaknesses fairly, emphasize significance, and keep a strong benchmark bar.",
        "persona": "Prof. Reviewer",
    },
    JudgePerspective.NOVELTY_CRITIC: {
        "title": "Novelty Critic",
        "focus": "originality and differentiation from prior work",
        "guidance": "Be skeptical of novelty claims and highlight overlap or incremental framing.",
        "persona": "Dr. Novel",
    },
    JudgePerspective.METHODS_EXPERT: {
        "title": "Methods Expert",
        "focus": "experimental design, scope control, and methodological rigor",
        "guidance": "Inspect controls, baseline fairness, confounds, and methodological soundness.",
        "persona": "Dr. Methods",
    },
    JudgePerspective.STATISTICS_EXPERT: {
        "title": "Statistics Expert",
        "focus": "statistical validity and quantitative interpretation",
        "guidance": "Check sample size, significance claims, uncertainty handling, and misuse of metrics.",
        "persona": "Prof. Stats",
    },
    JudgePerspective.WRITING_EXPERT: {
        "title": "Writing Expert",
        "focus": "clarity, organization, and presentation",
        "guidance": "Evaluate whether the structure and prose help the scientific content land clearly.",
        "persona": "Dr. Clarity",
    },
    JudgePerspective.DOMAIN_EXPERT: {
        "title": "Domain Expert",
        "focus": "technical correctness in the target domain",
        "guidance": "Check domain-specific assumptions, terminology, and technical soundness.",
        "persona": "Prof. Domain",
    },
    JudgePerspective.LITERATURE_EXPERT: {
        "title": "Literature Expert",
        "focus": "coverage, positioning, and fairness to prior work",
        "guidance": "Identify missing prior work, mispositioning, or unfair novelty framing.",
        "persona": "Dr. Literature",
    },
    JudgePerspective.CODE_EXPERT: {
        "title": "Code Expert",
        "focus": "implementation correctness and engineering quality",
        "guidance": "Look for bugs, fragile assumptions, and implementation gaps that could change results.",
        "persona": "Dr. Code",
    },
    JudgePerspective.REPRODUCIBILITY_ADVOCATE: {
        "title": "Reproducibility Advocate",
        "focus": "artifact completeness and whether another researcher could reproduce the work",
        "guidance": "Check whether code, figures, parameters, datasets, and procedures are exposed clearly enough to reproduce the study.",
        "persona": "Dr. Reproduce",
    },
    JudgePerspective.SKEPTIC: {
        "title": "Skeptic",
        "focus": "unsupported claims, missing evidence, and overclaim detection",
        "guidance": "Assume claims are not yet proven; require direct support and penalize overreach.",
        "persona": "Dr. Skeptic",
    },
    JudgePerspective.AREA_CHAIR: {
        "title": "Area Chair",
        "focus": "balanced final judgment across quality, significance, and benchmark fit",
        "guidance": "Integrate multiple dimensions into a decisive final judgment.",
        "persona": "AC Chair",
    },
    JudgePerspective.VISUALIZATION_EXPERT: {
        "title": "Visualization Expert",
        "focus": "figures, tables, and visual communication quality",
        "guidance": "Evaluate whether visuals are clear, informative, correctly labeled, and scientifically useful.",
        "persona": "Dr. Visual",
    },
}


SKILL_DIR_NAMES: Dict[JudgeSkill, str] = {
    JudgeSkill.GEVAL: "judge-geval",
    JudgeSkill.PROMETHEUS: "judge-prometheus",
    JudgeSkill.PAIRWISE: "judge-pairwise",
    JudgeSkill.PANDALM: "judge-pandalm",
    JudgeSkill.JUDGELM: "judge-judgelm",
}

SKILL_ROOT = Path(__file__).resolve().parent / "skills"


@dataclass(frozen=True)
class JudgeSkillDoc:
    skill: JudgeSkill
    name: str
    description: str
    relative_path: str
    overview: Tuple[str, ...]
    use_when: Tuple[str, ...]
    evaluation_workflow: Tuple[str, ...]
    output_contract: Tuple[str, ...]
    bias_controls: Tuple[str, ...]


def _split_frontmatter(markdown_text: str) -> tuple[Dict[str, str], str]:
    if not markdown_text.startswith("---\n"):
        return {}, markdown_text
    _, remainder = markdown_text.split("---\n", 1)
    frontmatter_text, body = remainder.split("\n---\n", 1)
    metadata: Dict[str, str] = {}
    for line in frontmatter_text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, body.strip()


def _extract_section(body: str, title: str) -> Tuple[str, ...]:
    pattern = rf"^##\s+{re.escape(title)}\s*$([\s\S]*?)(?=^##\s+|\Z)"
    match = re.search(pattern, body, flags=re.MULTILINE)
    if not match:
        return ()
    content = match.group(1).strip()
    items: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return tuple(items)


@lru_cache(maxsize=None)
def load_judge_skill_doc(skill: JudgeSkill) -> JudgeSkillDoc:
    relative_path = f"markscientist/skills/{SKILL_DIR_NAMES[skill]}/SKILL.md"
    path = SKILL_ROOT / SKILL_DIR_NAMES[skill] / "SKILL.md"
    markdown_text = path.read_text(encoding="utf-8")
    metadata, body = _split_frontmatter(markdown_text)
    return JudgeSkillDoc(
        skill=skill,
        name=metadata.get("name", skill.value),
        description=metadata.get("description", ""),
        relative_path=relative_path,
        overview=_extract_section(body, "Overview"),
        use_when=_extract_section(body, "Use When"),
        evaluation_workflow=_extract_section(body, "Evaluation Workflow"),
        output_contract=_extract_section(body, "Output Contract"),
        bias_controls=_extract_section(body, "Bias Controls"),
    )


@dataclass(frozen=True)
class JudgePolicy:
    scenario: JudgeScenario
    perspective: JudgePerspective
    skill: JudgeSkill
    description: str
    dimensions: Tuple[str, ...]
    strictness: str
    focus: str
    guidance: str
    persona: str
    skill_name: str
    skill_description: str
    skill_path: str
    skill_workflow: Tuple[str, ...]
    output_contract: Tuple[str, ...]
    bias_controls: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario": self.scenario.value,
            "perspective": self.perspective.value,
            "skill": self.skill.value,
            "description": self.description,
            "dimensions": list(self.dimensions),
            "strictness": self.strictness,
            "focus": self.focus,
            "guidance": self.guidance,
            "persona": self.persona,
            "skill_name": self.skill_name,
            "skill_description": self.skill_description,
            "skill_path": self.skill_path,
            "skill_workflow": list(self.skill_workflow),
            "output_contract": list(self.output_contract),
            "bias_controls": list(self.bias_controls),
        }

    def render(self, heading: str) -> str:
        lines = [
            f"## {heading}",
            f"- scenario: {self.scenario.value}",
            f"- perspective: {self.perspective.value} ({PERSPECTIVE_CONFIGS[self.perspective]['title']})",
            f"- persona: {self.persona}",
            f"- skill: {self.skill.value} ({self.skill_name})",
            f"- skill_path: {self.skill_path}",
            f"- strictness: {self.strictness}",
            f"- focus: {self.focus}",
            f"- scenario_description: {self.description}",
            f"- perspective_guidance: {self.guidance}",
            f"- skill_description: {self.skill_description}",
            "- dimensions:",
        ]
        lines.extend(f"  - {dimension}" for dimension in self.dimensions)
        if self.skill_workflow:
            lines.append("- skill_workflow:")
            lines.extend(f"  - {step}" for step in self.skill_workflow)
        if self.output_contract:
            lines.append("- skill_output_contract:")
            lines.extend(f"  - {item}" for item in self.output_contract)
        if self.bias_controls:
            lines.append("- bias_controls:")
            lines.extend(f"  - {control}" for control in self.bias_controls)
        return "\n".join(lines)


def render_policy_panel(heading: str, policies: Tuple[JudgePolicy, ...]) -> str:
    lines = [f"## {heading}"]
    for index, policy in enumerate(policies, start=1):
        lines.append(policy.render(f"Reviewer {index}"))
    return "\n\n".join(lines)


def build_judge_policy(
    scenario: JudgeScenario,
    perspective: Optional[JudgePerspective] = None,
    skill: Optional[JudgeSkill] = None,
) -> JudgePolicy:
    scenario_config = SCENARIO_CONFIGS[scenario]
    perspective = perspective or scenario_config["recommended_roles"][0]
    skill = skill or scenario_config["recommended_skill"]
    perspective_config = PERSPECTIVE_CONFIGS[perspective]
    skill_doc = load_judge_skill_doc(skill)
    return JudgePolicy(
        scenario=scenario,
        perspective=perspective,
        skill=skill,
        description=str(scenario_config["description"]),
        dimensions=tuple(scenario_config["dimensions"]),
        strictness=str(scenario_config["strictness"]),
        focus=str(perspective_config["focus"]),
        guidance=str(perspective_config["guidance"]),
        persona=str(perspective_config["persona"]),
        skill_name=skill_doc.name,
        skill_description=skill_doc.description,
        skill_path=skill_doc.relative_path,
        skill_workflow=skill_doc.evaluation_workflow,
        output_contract=skill_doc.output_contract,
        bias_controls=skill_doc.bias_controls,
    )


SKILL_ROTATIONS: Dict[JudgeSkill, Tuple[JudgeSkill, ...]] = {
    JudgeSkill.GEVAL: (JudgeSkill.GEVAL, JudgeSkill.PROMETHEUS, JudgeSkill.JUDGELM),
    JudgeSkill.PROMETHEUS: (JudgeSkill.PROMETHEUS, JudgeSkill.GEVAL, JudgeSkill.JUDGELM),
    JudgeSkill.PAIRWISE: (JudgeSkill.PAIRWISE, JudgeSkill.PROMETHEUS, JudgeSkill.GEVAL),
    JudgeSkill.PANDALM: (JudgeSkill.PANDALM, JudgeSkill.JUDGELM, JudgeSkill.PROMETHEUS),
    JudgeSkill.JUDGELM: (JudgeSkill.JUDGELM, JudgeSkill.GEVAL, JudgeSkill.PROMETHEUS),
}

PANEL_FALLBACKS: Tuple[JudgePerspective, ...] = (
    JudgePerspective.AREA_CHAIR,
    JudgePerspective.SKEPTIC,
    JudgePerspective.REPRODUCIBILITY_ADVOCATE,
    JudgePerspective.SENIOR_REVIEWER,
)


def build_default_panel(scenario: JudgeScenario) -> Tuple[JudgePolicy, ...]:
    scenario_config = SCENARIO_CONFIGS[scenario]
    roles = list(scenario_config["recommended_roles"])
    for fallback in PANEL_FALLBACKS:
        if len(roles) >= 3:
            break
        if fallback not in roles:
            roles.append(fallback)
    skill_rotation = SKILL_ROTATIONS[scenario_config["recommended_skill"]]
    return tuple(
        build_judge_policy(
            scenario,
            perspective=roles[index],
            skill=skill_rotation[min(index, len(skill_rotation) - 1)],
        )
        for index in range(min(3, len(roles)))
    )


def default_project_panel() -> Tuple[JudgePolicy, ...]:
    return build_default_panel(JudgeScenario.PROJECT_DEFINITION)


def default_report_panel(scenario: JudgeScenario = JudgeScenario.RESEARCH_REPORT) -> Tuple[JudgePolicy, ...]:
    return build_default_panel(scenario)


def policy_key_for(policy: JudgePolicy) -> str:
    return f"{policy.scenario.value}:{policy.perspective.value}:{policy.skill.value}"


@dataclass
class TasteCalibration:
    policy_key: str
    score_offset: float = 0.0
    agreement_count: int = 0
    disagree_count: int = 0
    too_high_count: int = 0
    too_low_count: int = 0

    @property
    def total_feedback(self) -> int:
        return self.agreement_count + self.disagree_count + self.too_high_count + self.too_low_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_key": self.policy_key,
            "score_offset": self.score_offset,
            "agreement_count": self.agreement_count,
            "disagree_count": self.disagree_count,
            "too_high_count": self.too_high_count,
            "too_low_count": self.too_low_count,
            "total_feedback": self.total_feedback,
        }


@dataclass
class TasteProfile:
    calibrations: Dict[str, TasteCalibration] = field(default_factory=dict)
    min_feedback_threshold: int = 3

    def apply(self, score: float, policy_key: str) -> Tuple[float, Dict[str, Any]]:
        calibration = self.calibrations.get(policy_key)
        metadata = {
            "policy_key": policy_key,
            "calibration_applied": False,
            "original_score": score,
            "offset": 0.0,
        }
        if calibration is None or calibration.total_feedback < self.min_feedback_threshold:
            return score, metadata
        adjusted_score = max(0.0, min(100.0, score + calibration.score_offset))
        metadata["calibration_applied"] = True
        metadata["offset"] = calibration.score_offset
        metadata["adjusted_score"] = adjusted_score
        metadata["feedback_count"] = calibration.total_feedback
        return adjusted_score, metadata


def load_taste_profile(
    feedback_path: Optional[Path] = None,
    min_feedback_threshold: int = 3,
) -> TasteProfile:
    if feedback_path is None:
        return TasteProfile(min_feedback_threshold=min_feedback_threshold)
    if not feedback_path.exists():
        return TasteProfile(min_feedback_threshold=min_feedback_threshold)

    raw_counts: Dict[str, Dict[str, int]] = {}
    try:
        with feedback_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                policy_key = (
                    record.get("policy_key")
                    or record.get("judge_perspective")
                    or record.get("reviewer_role")
                    or record.get("buddy_name")
                )
                reaction = record.get("user_reaction")
                if not policy_key or not reaction:
                    continue
                stats = raw_counts.setdefault(
                    str(policy_key),
                    {"agree": 0, "disagree": 0, "too_high": 0, "too_low": 0},
                )
                if reaction in stats:
                    stats[reaction] += 1
    except OSError:
        return TasteProfile(min_feedback_threshold=min_feedback_threshold)

    calibrations: Dict[str, TasteCalibration] = {}
    for policy_key, stats in raw_counts.items():
        offset = max(-20.0, min(20.0, (stats["too_low"] - stats["too_high"]) * 3.0))
        calibrations[policy_key] = TasteCalibration(
            policy_key=policy_key,
            score_offset=offset,
            agreement_count=stats["agree"],
            disagree_count=stats["disagree"],
            too_high_count=stats["too_high"],
            too_low_count=stats["too_low"],
        )
    return TasteProfile(calibrations=calibrations, min_feedback_threshold=min_feedback_threshold)
