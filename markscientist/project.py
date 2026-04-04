from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple


ALLOWED_TARGET_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def _has_pdf_signature(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            head = handle.read(1024)
    except OSError:
        return False
    return b"%PDF-" in head


@dataclass(frozen=True)
class ProjectPaths:
    project_root: Path
    task_root: Path
    public_root: Path
    judge_dir: Path
    source_data_dir: Path
    source_related_work_dir: Path
    public_data_dir: Path
    public_related_work_dir: Path
    code_dir: Path
    outputs_dir: Path
    report_dir: Path
    report_images_dir: Path
    task_info_path: Path
    instructions_path: Path
    report_path: Path
    judge_notes_path: Path
    judge_checklist_path: Path
    judge_paper_path: Path
    judge_images_dir: Path
    judge_feedback_path: Path


def resolve_project_paths(project_root: Path | str) -> ProjectPaths:
    root = Path(project_root).expanduser().resolve()
    task_root = root / "task"
    public_root = root / "public"
    judge_dir = task_root / "target_study"
    report_dir = public_root / "report"
    public_data_dir = public_root / "data"
    public_related_work_dir = public_root / "related_work"
    return ProjectPaths(
        project_root=root,
        task_root=task_root,
        public_root=public_root,
        judge_dir=judge_dir,
        source_data_dir=task_root / "data",
        source_related_work_dir=task_root / "related_work",
        public_data_dir=public_data_dir,
        public_related_work_dir=public_related_work_dir,
        code_dir=public_root / "code",
        outputs_dir=public_root / "outputs",
        report_dir=report_dir,
        report_images_dir=report_dir / "images",
        task_info_path=task_root / "task_info.json",
        instructions_path=public_root / "INSTRUCTIONS.md",
        report_path=report_dir / "report.md",
        judge_notes_path=judge_dir / "notes.md",
        judge_checklist_path=judge_dir / "checklist.json",
        judge_paper_path=judge_dir / "paper.pdf",
        judge_images_dir=judge_dir / "images",
        judge_feedback_path=judge_dir / "feedback_history.jsonl",
    )


def ensure_project_layout(project_root: Path | str) -> ProjectPaths:
    paths = resolve_project_paths(project_root)
    paths.project_root.mkdir(parents=True, exist_ok=True)
    paths.task_root.mkdir(parents=True, exist_ok=True)
    paths.source_data_dir.mkdir(parents=True, exist_ok=True)
    paths.source_related_work_dir.mkdir(parents=True, exist_ok=True)
    paths.public_root.mkdir(parents=True, exist_ok=True)
    paths.judge_dir.mkdir(parents=True, exist_ok=True)
    paths.judge_images_dir.mkdir(parents=True, exist_ok=True)
    paths.public_data_dir.mkdir(parents=True, exist_ok=True)
    paths.public_related_work_dir.mkdir(parents=True, exist_ok=True)
    paths.code_dir.mkdir(parents=True, exist_ok=True)
    paths.outputs_dir.mkdir(parents=True, exist_ok=True)
    paths.report_images_dir.mkdir(parents=True, exist_ok=True)
    return paths


INSTRUCTIONS_TEMPLATE = """\
## Role

You are an autonomous scientific research agent. Your mission is to independently complete a research task from start to finish:

1. **Read & Understand** — Study the related work and data to build domain context.
2. **Think & Design** — Formulate your research idea, hypothesis, and analysis plan.
3. **Code & Execute** — Implement the analysis, generate figures, and iterate until results are solid.
4. **Analyze & Report** — Interpret the results and produce a publication-quality research report.

---

## Research Task

### Task Description
{task_desc}

### Available Data Files
{data_text}

---

## Execution Protocol

**There is no human on the other end.** No one will answer questions, grant permissions, or provide clarification. You are fully on your own. If you encounter difficulties, confusion, or unexpected errors — do not ask for help, do not pause, and do not interrupt the task. Make your best judgment and keep going.

Your primary goal is to complete the research task and produce a high-quality `report/report.md`. Your implicit secondary goal is equally important: **ensure the session is never accidentally terminated before the task is done.**

If you are operating as a ReAct-style agent (Reasoning + Acting), note that a response containing only text with no tool call will be interpreted as task completion. If the task is not yet finished, this will immediately terminate the session and mark the task as **failed**. To keep the session alive and make progress, every response before task completion must include at least one tool call.

### Strictly Forbidden
- Outputting only a research plan or summary without calling any tool
- Asking questions, requesting clarification, or seeking confirmation
- Text-only reasoning responses that contain no tool call (causes accidental termination)
- Declaring the task complete before `report/report.md` is written
- Stopping or giving up due to errors, missing data, or uncertainty

### Rules
1. **Always act**: Unless the final report is fully written and all deliverables are complete, every response must include at least one tool call. Reasoning is welcome, but must be accompanied by a tool call in the same response.
2. **Never ask**: Do not pose questions, request clarification, or ask for permission. If something is ambiguous, make a reasonable assumption and proceed.
3. **Push through difficulties**: If a script fails, debug it. If data is unclear, make reasonable assumptions. If a package is missing, install it. Never stop because something is hard.
4. **Never finish early**: The task is only complete when `report/report.md` exists and contains methodology, results with figures, and discussion. Do not stop before then.

---

## Workspace

Your workspace is: `{workspace}`

- All file reads and writes must stay inside this directory.
- `data/` and `related_work/` are read-only — do not modify them.
- Do not access the network to download external datasets unless explicitly instructed.

### Layout
- `data/` — Input datasets (read-only)
- `related_work/` — Reference papers (read-only)
- `code/` — Write your analysis code here
- `outputs/` — Save intermediate results
- `report/` — Write your final report here
- `report/images/` — Save all figures here as **PNG files** (`.png` only)

### Deliverables
1. Analysis code in `code/`
2. Intermediate results in `outputs/`
3. A comprehensive research report as `report/report.md`:
   - Methodology, results, and discussion
   - Academic writing style
   - **Figures are mandatory** — generate plots and save to `report/images/`, reference them with relative paths: `images/figure_name.png`
   - Include at minimum: data overview, main results, and validation/comparison plots

### Technical Notes
- Install Python packages as needed before using them.
- Use matplotlib, seaborn, or any suitable visualization library. Save all figures as **PNG files** (`.png`). Do not use uncommon formats such as PPM, BMP, TIFF, or EPS — these cannot be rendered in the report viewer.
- Ensure code is reproducible.

---

Now proceed step by step with actions (tool calls) until `report/report.md` is complete.
"""


def read_text_if_exists(path: Path, *, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8").strip()


def load_checklist_text(path: Path) -> str:
    if not path.exists():
        return "[]"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return path.read_text(encoding="utf-8").strip()
    return json.dumps(payload, ensure_ascii=False, indent=2)


def load_checklist_payload(path: Path) -> list[dict[str, Any]] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, list):
        return None
    items: list[dict[str, Any]] = []
    for item in payload:
        if isinstance(item, dict):
            items.append(item)
    return items


def _format_workspace_listing(root: Path, subdir: str) -> str:
    base = root / subdir
    if not base.exists():
        return f"- `{subdir}/` is missing."
    file_paths = sorted(path for path in base.rglob("*") if path.is_file())
    if not file_paths:
        return f"- `{subdir}/` exists but contains no files."
    lines: list[str] = []
    for path in file_paths[:50]:
        rel_path = path.relative_to(root).as_posix()
        size_bytes = path.stat().st_size
        if size_bytes < 1024:
            size_text = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_text = f"{size_bytes / 1024:.1f} KB"
        else:
            size_text = f"{size_bytes / (1024 * 1024):.1f} MB"
        lines.append(f"- `{rel_path}` ({size_text})")
    if len(file_paths) > 50:
        lines.append(f"- ... and {len(file_paths) - 50} more files under `{subdir}/`.")
    return "\n".join(lines)


def _format_related_work_pdf_listing(root: Path, subdir: str) -> str:
    base = root / subdir
    if not base.exists():
        return f"- `{subdir}/` is missing."
    pdf_paths = sorted(path for path in base.rglob("*.pdf") if path.is_file())
    if not pdf_paths:
        return f"- `{subdir}/` contains no PDF files."
    lines: list[str] = []
    for path in pdf_paths[:50]:
        rel_path = path.relative_to(root).as_posix()
        size_bytes = path.stat().st_size
        validity_suffix = ""
        if not _has_pdf_signature(path):
            validity_suffix = ", invalid PDF signature"
        if size_bytes < 1024:
            size_text = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_text = f"{size_bytes / 1024:.1f} KB"
        else:
            size_text = f"{size_bytes / (1024 * 1024):.1f} MB"
        lines.append(f"- `{rel_path}` ({size_text}{validity_suffix})")
    if len(pdf_paths) > 50:
        lines.append(f"- ... and {len(pdf_paths) - 50} more PDF files under `{subdir}/`.")
    non_pdf_files = sorted(path for path in base.rglob("*") if path.is_file() and path.suffix.lower() != ".pdf")
    if non_pdf_files:
        lines.append(
            f"- Note: {len(non_pdf_files)} non-PDF files also exist under `{subdir}/`, but only PDFs are valid Solver-visible related work artifacts."
        )
    return "\n".join(lines)


def describe_workspace_inputs(workspace_root: Path | str) -> dict[str, str]:
    root = Path(workspace_root).expanduser().resolve()
    return {
        "data_inventory": _format_workspace_listing(root, "data"),
        "related_work_inventory": _format_related_work_pdf_listing(root, "related_work"),
    }


def describe_challenger_inputs(paths: ProjectPaths) -> dict[str, str]:
    task_root = paths.task_root
    public_root = paths.public_root
    return {
        "source_data_inventory": _format_workspace_listing(task_root, "data"),
        "source_related_work_inventory": _format_related_work_pdf_listing(task_root, "related_work"),
        "public_data_inventory": _format_workspace_listing(public_root, "data"),
        "public_related_work_inventory": _format_related_work_pdf_listing(public_root, "related_work"),
    }


def load_judge_materials_text(paths: ProjectPaths) -> str:
    blocks: list[str] = []
    if paths.judge_notes_path.exists():
        blocks.append("## Judge Notes\n" + paths.judge_notes_path.read_text(encoding="utf-8").strip())
    if paths.judge_checklist_path.exists():
        blocks.append("## Judge Checklist\n" + load_checklist_text(paths.judge_checklist_path))
    return "\n\n".join(block for block in blocks if block.strip())


def load_task_info(paths: ProjectPaths) -> Dict[str, Any]:
    if not paths.task_info_path.exists():
        return {}
    try:
        payload = json.loads(paths.task_info_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolved_task_data_sources(paths: ProjectPaths, task_info: Dict[str, Any]) -> list[Path]:
    data_items = task_info.get("data")
    if not isinstance(data_items, list):
        return []
    resolved: list[Path] = []
    for item in data_items:
        if not isinstance(item, dict):
            continue
        raw_path = str(item.get("path", "")).strip()
        if not raw_path.startswith("./data/"):
            continue
        relative = raw_path.removeprefix("./data/").strip("/")
        if not relative:
            continue
        resolved.append(paths.source_data_dir / relative)
    return resolved


def _task_data_manifest_lines(task_info: Dict[str, Any]) -> str:
    data_items = task_info.get("data")
    if not isinstance(data_items, list) or not data_items:
        return "No specific data files."
    lines: list[str] = []
    for item in data_items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "Unnamed dataset")).strip() or "Unnamed dataset"
        path = str(item.get("path", "")).strip()
        data_type = str(item.get("type", "")).strip()
        description = str(item.get("description", "")).strip()
        type_suffix = f" [{data_type}]" if data_type else ""
        lines.append(f"- **{name}**{type_suffix} (`{path}`): {description}")
    return "\n".join(lines) if lines else "No specific data files."


def build_solver_instructions(paths: ProjectPaths) -> str:
    task_info = load_task_info(paths)
    task_desc = str(task_info.get("task", "")).strip()
    if not task_desc:
        task_desc = "No task description was provided."
    return INSTRUCTIONS_TEMPLATE.format(
        workspace=str(paths.public_root.resolve()),
        task_desc=task_desc,
        data_text=_task_data_manifest_lines(task_info),
    )


def _clear_directory_contents(root: Path) -> None:
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)
        return
    for path in sorted(root.iterdir()):
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def export_solver_workspace_from_task(paths: ProjectPaths) -> None:
    task_info = load_task_info(paths)
    _clear_directory_contents(paths.public_data_dir)
    _clear_directory_contents(paths.public_related_work_dir)
    for source in _resolved_task_data_sources(paths, task_info):
        if not source.exists():
            continue
        target = paths.public_data_dir / source.relative_to(paths.source_data_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        elif source.is_file():
            shutil.copy2(source, target)
    for source in sorted(paths.source_related_work_dir.glob("*.pdf")):
        shutil.copy2(source, paths.public_related_work_dir / source.name)
    paths.instructions_path.write_text(build_solver_instructions(paths), encoding="utf-8")


def missing_solver_contract_files(paths: ProjectPaths) -> list[str]:
    required = [paths.instructions_path]
    missing: list[str] = []
    for path in required:
        if not path.exists():
            missing.append(path.relative_to(paths.public_root).as_posix())
            continue
        if not path.read_text(encoding="utf-8").strip():
            missing.append(path.relative_to(paths.public_root).as_posix())
    return missing


def missing_source_input_dirs(paths: ProjectPaths) -> list[str]:
    missing: list[str] = []
    if _count_files(paths.source_data_dir) == 0:
        missing.append(paths.source_data_dir.relative_to(paths.project_root).as_posix())
    if not any(path.is_file() for path in paths.source_related_work_dir.rglob("*.pdf")):
        missing.append(paths.source_related_work_dir.relative_to(paths.project_root).as_posix())
    return missing


def missing_task_contract_files(paths: ProjectPaths) -> list[str]:
    missing: list[str] = []
    for path in (paths.task_info_path, paths.judge_checklist_path, paths.judge_paper_path):
        if not path.exists() or not path.read_bytes():
            missing.append(path.relative_to(paths.project_root).as_posix())
    return missing


def missing_judge_contract_files(paths: ProjectPaths) -> list[str]:
    required = [paths.judge_checklist_path]
    missing: list[str] = []
    for path in required:
        if not path.exists():
            missing.append(path.relative_to(paths.project_root).as_posix())
            continue
        if not path.read_text(encoding="utf-8").strip():
            missing.append(path.relative_to(paths.project_root).as_posix())
    has_target_images = any(path.is_file() for path in paths.judge_images_dir.rglob("*"))
    if not has_target_images:
        missing.append(paths.judge_images_dir.relative_to(paths.project_root).as_posix())
    return missing


def _count_files(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*") if path.is_file())


def missing_solver_visible_input_dirs(paths: ProjectPaths) -> list[str]:
    missing: list[str] = []
    if _count_files(paths.public_data_dir) == 0:
        missing.append(paths.public_data_dir.relative_to(paths.project_root).as_posix())
    if not any(path.is_file() for path in paths.public_related_work_dir.rglob("*.pdf")):
        missing.append(paths.public_related_work_dir.relative_to(paths.project_root).as_posix())
    return missing


def invalid_solver_visible_input_files(paths: ProjectPaths) -> list[str]:
    invalid: list[str] = []
    if paths.public_data_dir.exists():
        for path in sorted(paths.public_data_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() == ".pdf":
                invalid.append(f"{path.relative_to(paths.project_root).as_posix()} (solver-visible data must not contain PDF files)")
    if paths.public_related_work_dir.exists():
        for path in sorted(paths.public_related_work_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() != ".pdf":
                invalid.append(f"{path.relative_to(paths.project_root).as_posix()} (related work must be PDF)")
            elif not _has_pdf_signature(path):
                invalid.append(f"{path.relative_to(paths.project_root).as_posix()} (related work PDF is invalid or not a real PDF)")
    return invalid


def invalid_source_input_files(paths: ProjectPaths) -> list[str]:
    invalid: list[str] = []
    if paths.source_data_dir.exists():
        for path in sorted(paths.source_data_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() == ".pdf":
                invalid.append(f"{path.relative_to(paths.project_root).as_posix()} (source data must not contain PDF files)")

    if paths.source_related_work_dir.exists():
        for path in sorted(paths.source_related_work_dir.rglob("*")):
            if not path.is_file():
                continue
            relative_path = path.relative_to(paths.project_root).as_posix()
            if path.parent != paths.source_related_work_dir:
                # ReadPDF may materialize parser sidecars beneath a sibling folder named
                # after the source PDF. Those derived artifacts are allowed in the
                # canonical source archive as long as the top-level source files are real PDFs.
                continue
            if path.suffix.lower() != ".pdf":
                invalid.append(f"{relative_path} (top-level source related work must be PDF)")
            elif not _has_pdf_signature(path):
                invalid.append(f"{relative_path} (source related work PDF is invalid or not a real PDF)")
    if paths.judge_paper_path.exists() and not _has_pdf_signature(paths.judge_paper_path):
        invalid.append(f"{paths.judge_paper_path.relative_to(paths.project_root).as_posix()} (target study paper must be a real PDF)")

    checklist_payload = load_checklist_payload(paths.judge_checklist_path)
    if paths.judge_checklist_path.exists() and checklist_payload is None:
        invalid.append(
            f"{paths.judge_checklist_path.relative_to(paths.project_root).as_posix()} (checklist must be a JSON array of checklist item objects)"
        )
    image_items = [item for item in checklist_payload or [] if str(item.get("type", "")).strip().lower() == "image"]
    if paths.judge_checklist_path.exists() and not image_items:
        invalid.append(
            f"{paths.judge_checklist_path.relative_to(paths.project_root).as_posix()} (checklist must include at least one image item grounded in target_study/images)"
        )
    for index, item in enumerate(image_items, start=1):
        raw_path = item.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            invalid.append(
                f"{paths.judge_checklist_path.relative_to(paths.project_root).as_posix()} (image checklist item {index} must include a relative path under images/)"
            )
            continue
        normalized_path = raw_path.replace("\\", "/").strip()
        if not normalized_path.startswith("images/"):
            invalid.append(
                f"{paths.judge_checklist_path.relative_to(paths.project_root).as_posix()} (image checklist item {index} path must start with images/)"
            )
            continue
        target_image_path = paths.judge_dir / normalized_path
        if not target_image_path.exists() or not target_image_path.is_file():
            invalid.append(
                f"{paths.judge_checklist_path.relative_to(paths.project_root).as_posix()} (image checklist item {index} references a missing target image: {normalized_path})"
            )
            continue
        if target_image_path.suffix.lower() not in ALLOWED_TARGET_IMAGE_SUFFIXES:
            invalid.append(
                f"{target_image_path.relative_to(paths.project_root).as_posix()} (target study images must be raster images extracted from the target PDF)"
            )
            continue
        if target_image_path.stat().st_size == 0:
            invalid.append(
                f"{target_image_path.relative_to(paths.project_root).as_posix()} (target study image must not be empty)"
            )

    task_info = load_task_info(paths)
    data_items = task_info.get("data")
    if data_items is not None and not isinstance(data_items, list):
        invalid.append(f"{paths.task_info_path.relative_to(paths.project_root).as_posix()} (`data` must be a list)")
        return invalid
    for item in data_items or []:
        if not isinstance(item, dict):
            invalid.append(f"{paths.task_info_path.relative_to(paths.project_root).as_posix()} (`data` entries must be objects)")
            continue
        raw_path = str(item.get("path", "")).strip()
        data_type = str(item.get("type", "")).strip().lower()
        if not raw_path.startswith("./data/"):
            invalid.append(
                f"{paths.task_info_path.relative_to(paths.project_root).as_posix()} (`data[].path` must start with ./data/)"
            )
            continue
        if raw_path.lower().endswith(".pdf") or data_type == "pdf":
            invalid.append(
                f"{paths.task_info_path.relative_to(paths.project_root).as_posix()} (`data[].path` must not reference PDF files)"
            )
            continue
        relative = raw_path.removeprefix("./data/").strip("/")
        if not relative:
            invalid.append(
                f"{paths.task_info_path.relative_to(paths.project_root).as_posix()} (`data[].path` must reference a concrete data file or directory)"
            )
            continue
        resolved_path = (paths.source_data_dir / relative).resolve()
        try:
            resolved_path.relative_to(paths.source_data_dir.resolve())
        except ValueError:
            invalid.append(
                f"{paths.task_info_path.relative_to(paths.project_root).as_posix()} (`data[].path` must stay within task/data/)"
            )
            continue
        if not resolved_path.exists():
            invalid.append(
                f"{paths.task_info_path.relative_to(paths.project_root).as_posix()} (`data[].path` references a missing source data path: {raw_path})"
            )
    return invalid


def solver_artifact_status(paths: ProjectPaths) -> dict[str, int | bool]:
    report_exists = paths.report_path.exists() and bool(paths.report_path.read_text(encoding="utf-8").strip())
    return {
        "code_files": _count_files(paths.code_dir),
        "output_files": _count_files(paths.outputs_dir),
        "image_files": _count_files(paths.report_images_dir),
        "report_exists": report_exists,
    }


def snapshot_solver_owned_files(paths: ProjectPaths) -> Dict[str, Tuple[int, int]]:
    snapshot: Dict[str, Tuple[int, int]] = {}

    def _record_tree(root: Path) -> None:
        if not root.exists():
            return
        for path in sorted(root.rglob("*")):
            if path.is_file():
                rel_path = path.relative_to(paths.public_root).as_posix()
                stat = path.stat()
                snapshot[rel_path] = (stat.st_mtime_ns, stat.st_size)

    _record_tree(paths.code_dir)
    _record_tree(paths.outputs_dir)
    _record_tree(paths.report_images_dir)
    if paths.report_path.exists():
        stat = paths.report_path.stat()
        snapshot[paths.report_path.relative_to(paths.public_root).as_posix()] = (stat.st_mtime_ns, stat.st_size)
    return snapshot


def detect_solver_owned_file_changes(
    before: Dict[str, Tuple[int, int]],
    after: Dict[str, Tuple[int, int]],
) -> list[str]:
    changed: set[str] = set()
    for rel_path, fingerprint in after.items():
        if before.get(rel_path) != fingerprint:
            changed.add(rel_path)
    for rel_path in before:
        if rel_path not in after:
            changed.add(rel_path)
    return sorted(changed)
