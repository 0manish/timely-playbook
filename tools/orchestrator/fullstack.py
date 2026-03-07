"""FullStack-Agent integration helpers for the Timely orchestrator.

This module incorporates ideas from arXiv:2602.03798 by providing:
- pinned upstream sync (FullStack-Agent / FullStack-Dev / FullStack-Bench / FullStack-Learn)
- reusable project bootstrap from full-stack templates
- deterministic phase planning
- development-phase execution through Codex with artifact capture
- repository back-translation traces for future reuse
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .state import State, Task
from .helpers import kiss_bridge

ROOT = Path(__file__).resolve().parents[2]
DEFAULTS_PATH = ROOT / "tools" / "orchestrator" / "fullstack_defaults.json"
CONFIG_PATH = ROOT / ".orchestrator" / "fullstack-agent.json"


@dataclass
class ProjectPaths:
    """Resolved filesystem paths for a bootstrapped fullstack project."""

    root: Path
    app_root: Path
    timely_dir: Path
    brief_file: Path
    manifest_file: Path
    plan_file: Path
    runs_dir: Path
    backtranslation_dir: Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _run_command(
    cmd: Iterable[str],
    cwd: Path | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(cmd),
        cwd=str(cwd) if cwd else None,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def _slug(value: str) -> str:
    out = []
    for char in value:
        if char.isalnum() or char in {"-", "_"}:
            out.append(char)
        else:
            out.append("-")
    result = "".join(out).strip("-")
    return result or "project"


def _phase_task_id(project_id: str, phase_id: str) -> str:
    return f"FS-{_slug(project_id).upper()}-{_slug(phase_id).upper()}"


def _hash_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()


def _snapshot_tree(root: Path) -> Dict[str, str]:
    snapshot: Dict[str, str] = {}
    if not root.exists():
        return snapshot
    for item in sorted(root.rglob("*")):
        if not item.is_file():
            continue
        parts = set(item.parts)
        if ".git" in parts or "node_modules" in parts:
            continue
        rel = item.relative_to(root).as_posix()
        snapshot[rel] = _hash_file(item)
    return snapshot


def _changed_files(before: Dict[str, str], after: Dict[str, str]) -> Dict[str, List[str]]:
    before_keys = set(before)
    after_keys = set(after)

    added = sorted(after_keys - before_keys)
    removed = sorted(before_keys - after_keys)
    modified = sorted(k for k in before_keys & after_keys if before[k] != after[k])
    return {"added": added, "removed": removed, "modified": modified}


def ensure_config(force: bool = False) -> Path:
    """Create .orchestrator/fullstack-agent.json from defaults."""
    if CONFIG_PATH.exists() and not force:
        return CONFIG_PATH
    defaults = _load_json(DEFAULTS_PATH)
    _write_json(CONFIG_PATH, defaults)
    return CONFIG_PATH


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        ensure_config()
    return _load_json(CONFIG_PATH)


def _project_paths(config: Dict[str, Any], project_id: str) -> ProjectPaths:
    project_root = ROOT / config["projects_dir"] / _slug(project_id)
    timely_dir = project_root / ".timely"
    return ProjectPaths(
        root=project_root,
        app_root=project_root / "app",
        timely_dir=timely_dir,
        brief_file=project_root / "PROJECT_BRIEF.md",
        manifest_file=timely_dir / "fullstack-manifest.json",
        plan_file=timely_dir / "fullstack-plan.json",
        runs_dir=timely_dir / "runs",
        backtranslation_dir=project_root / "artifacts" / "backtranslation",
    )


def sync_upstreams(update: bool = False) -> Dict[str, Any]:
    """Clone/update pinned upstream repos used by FullStack-Agent integration."""
    config = load_config()
    results: List[Dict[str, Any]] = []

    for repo in config.get("upstreams", []):
        local_path = ROOT / repo["local_path"]
        local_path.parent.mkdir(parents=True, exist_ok=True)

        events: List[str] = []
        if not local_path.exists():
            clone = _run_command(["git", "clone", repo["url"], str(local_path)])
            if clone.returncode != 0:
                raise RuntimeError(f"git clone failed for {repo['id']}: {clone.stderr.strip()}")
            events.append("cloned")
        elif update:
            fetch = _run_command(["git", "fetch", "--tags", "--prune", "origin"], cwd=local_path)
            if fetch.returncode != 0:
                raise RuntimeError(f"git fetch failed for {repo['id']}: {fetch.stderr.strip()}")
            events.append("fetched")
        else:
            events.append("present")

        checkout = _run_command(["git", "checkout", "--detach", repo["ref"]], cwd=local_path)
        if checkout.returncode != 0:
            raise RuntimeError(f"git checkout failed for {repo['id']}: {checkout.stderr.strip()}")
        head = _run_command(["git", "rev-parse", "HEAD"], cwd=local_path)
        if head.returncode != 0:
            raise RuntimeError(f"git rev-parse failed for {repo['id']}: {head.stderr.strip()}")
        events.append(f"checked-out:{head.stdout.strip()}")

        results.append(
            {
                "id": repo["id"],
                "path": str(local_path.relative_to(ROOT)),
                "events": events,
            }
        )

    return {
        "status": "ok",
        "updated": update,
        "repos": results,
        "timestamp": _utc_now(),
    }


def _copy_template(config: Dict[str, Any], template_id: str, app_root: Path) -> Dict[str, str]:
    templates = config.get("templates", {})
    if template_id not in templates:
        raise ValueError(f"Unknown template: {template_id}")
    template = templates[template_id]

    mode = template["mode"]
    repo_map = {entry["id"]: ROOT / entry["local_path"] for entry in config.get("upstreams", [])}

    if mode == "coupled":
        source_root = repo_map[template["repo"]] / template["path"]
        if not source_root.exists():
            raise FileNotFoundError(
                f"Template source {source_root} is missing. Run fullstack-sync first."
            )
        shutil.copytree(source_root, app_root, dirs_exist_ok=True)
    elif mode == "decoupled":
        repo_root = repo_map[template["repo"]]
        common_path = repo_root / template["common_path"]
        frontend_path = repo_root / template["frontend_path"]
        backend_path = repo_root / template["backend_path"]
        for src in [common_path, frontend_path, backend_path]:
            if not src.exists():
                raise FileNotFoundError(f"Template source {src} is missing. Run fullstack-sync first.")

        shutil.copytree(common_path, app_root, dirs_exist_ok=True)
        shutil.copytree(frontend_path, app_root / "frontend", dirs_exist_ok=True)
        shutil.copytree(backend_path, app_root / "backend", dirs_exist_ok=True)
    else:
        raise ValueError(f"Unsupported template mode: {mode}")

    return {
        "template_id": template_id,
        "mode": mode,
    }


def bootstrap_project(
    project_id: str,
    brief: str,
    template_id: str,
    allow_existing: bool = False,
) -> Dict[str, Any]:
    """Create a reusable fullstack project workspace using pinned upstream templates."""
    config = load_config()
    paths = _project_paths(config, project_id)

    brief_text = brief.strip()
    if not brief_text:
        raise ValueError("Brief cannot be empty")

    if paths.root.exists() and not allow_existing:
        raise FileExistsError(f"Project already exists: {paths.root}")

    paths.root.mkdir(parents=True, exist_ok=True)
    paths.app_root.mkdir(parents=True, exist_ok=True)
    paths.timely_dir.mkdir(parents=True, exist_ok=True)
    paths.runs_dir.mkdir(parents=True, exist_ok=True)
    paths.backtranslation_dir.mkdir(parents=True, exist_ok=True)

    if any(paths.app_root.iterdir()) and not allow_existing:
        raise FileExistsError(f"Project app directory is not empty: {paths.app_root}")

    copy_info = _copy_template(config, template_id, paths.app_root)

    paths.brief_file.write_text(
        "# Project Brief\n\n"
        f"{brief_text}\n",
        encoding="utf-8",
    )

    upstream_refs = {item["id"]: item["ref"] for item in config.get("upstreams", [])}
    manifest = {
        "schema_version": config.get("schema_version", 1),
        "created_at": _utc_now(),
        "project_id": _slug(project_id),
        "paper": config.get("paper", {}),
        "template": template_id,
        "default_model": config.get("default_model", "gpt-5-codex"),
        "paths": {
            "project_root": str(paths.root.relative_to(ROOT)),
            "app_root": str(paths.app_root.relative_to(ROOT)),
            "brief_file": str(paths.brief_file.relative_to(ROOT)),
            "plan_file": str(paths.plan_file.relative_to(ROOT)),
        },
        "upstream_refs": upstream_refs,
    }

    phases = []
    for phase in config.get("phases", []):
        phases.append(
            {
                "id": phase["id"],
                "title": phase["title"],
                "status": "pending",
                "prompt_template": phase["prompt_template"],
                "validation_commands": phase.get("validation_commands", []),
                "runs": [],
            }
        )

    plan = {
        "project_id": _slug(project_id),
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
        "template": template_id,
        "phases": phases,
    }

    _write_json(paths.manifest_file, manifest)
    _write_json(paths.plan_file, plan)

    backtranslation_readme = paths.backtranslation_dir / "README.md"
    backtranslation_readme.write_text(
        "# Back-Translation Artifacts\n\n"
        "This directory stores phase prompts, command outputs, validation logs, and file-diff traces "
        "captured during each fullstack phase run.\n",
        encoding="utf-8",
    )

    return {
        "status": "ok",
        "project_id": _slug(project_id),
        "template": copy_info,
        "project_root": str(paths.root.relative_to(ROOT)),
        "manifest": str(paths.manifest_file.relative_to(ROOT)),
        "plan": str(paths.plan_file.relative_to(ROOT)),
    }


def _load_project(config: Dict[str, Any], project_id: str) -> Tuple[ProjectPaths, Dict[str, Any], Dict[str, Any]]:
    paths = _project_paths(config, project_id)
    if not paths.manifest_file.exists() or not paths.plan_file.exists():
        raise FileNotFoundError(
            f"Project '{project_id}' is not bootstrapped. Run fullstack-bootstrap first."
        )
    manifest = _load_json(paths.manifest_file)
    plan = _load_json(paths.plan_file)
    return paths, manifest, plan


def _save_plan(paths: ProjectPaths, plan: Dict[str, Any]) -> None:
    plan["updated_at"] = _utc_now()
    _write_json(paths.plan_file, plan)


def _sync_state_from_plan(paths: ProjectPaths, plan: Dict[str, Any]) -> None:
    state = State.load()
    existing = {task.task_id: task for task in state.tasks}
    phase_tasks: List[str] = []

    for idx, phase in enumerate(plan.get("phases", [])):
        task_id = _phase_task_id(plan["project_id"], phase["id"])
        phase_tasks.append(task_id)
        deps = [phase_tasks[idx - 1]] if idx > 0 else []

        status_map = {
            "pending": "pending",
            "ready": "ready",
            "in_progress": "in_progress",
            "done": "done",
            "failed": "changes_requested",
        }
        state_status = status_map.get(phase["status"], "pending")

        artifacts = [
            str(paths.plan_file.relative_to(ROOT)),
            str(paths.runs_dir.relative_to(ROOT)),
        ]

        if task_id in existing:
            task = existing[task_id]
            task.title = f"{plan['project_id']}: {phase['title']}"
            task.owner = "fullstack"
            task.status = state_status
            task.deps = deps
            task.artifacts = artifacts
        else:
            state.tasks.append(
                Task(
                    task_id=task_id,
                    title=f"{plan['project_id']}: {phase['title']}",
                    owner="fullstack",
                    status=state_status,
                    deps=deps,
                    artifacts=artifacts,
                )
            )

    state.save()
    state.update_status_file()


def plan_project(project_id: str, register_state: bool = True) -> Dict[str, Any]:
    """Set first pending phase to ready and sync orchestrator task graph."""
    config = load_config()
    paths, _, plan = _load_project(config, project_id)

    has_ready_or_in_progress = any(
        phase["status"] in {"ready", "in_progress"} for phase in plan.get("phases", [])
    )

    if not has_ready_or_in_progress:
        for phase in plan.get("phases", []):
            if phase["status"] == "pending":
                phase["status"] = "ready"
                break

    _save_plan(paths, plan)
    if register_state:
        _sync_state_from_plan(paths, plan)

    return {
        "status": "ok",
        "project_id": plan["project_id"],
        "plan_file": str(paths.plan_file.relative_to(ROOT)),
        "phases": plan.get("phases", []),
    }


def _render_prompt(
    prompt_template_path: Path,
    manifest: Dict[str, Any],
    paths: ProjectPaths,
    phase: Dict[str, Any],
) -> str:
    template = prompt_template_path.read_text(encoding="utf-8")
    brief_text = paths.brief_file.read_text(encoding="utf-8")

    context = {
        "project_id": manifest["project_id"],
        "template": manifest["template"],
        "paper_title": manifest.get("paper", {}).get("title", "FullStack-Agent"),
        "paper_url": manifest.get("paper", {}).get("url", "https://arxiv.org/abs/2602.03798"),
        "brief_file": str(paths.brief_file),
        "project_root": str(paths.root),
        "app_root": str(paths.app_root),
        "phase_id": phase["id"],
        "phase_title": phase["title"],
        "brief_text": brief_text.strip(),
    }
    return template.format(**context)


def run_phase(
    project_id: str,
    phase_id: str,
    model: str | None = None,
    dry_run: bool = False,
    skill: str | None = None,
) -> Dict[str, Any]:
    """Run one fullstack phase through Codex and capture back-translation artifacts."""
    config = load_config()
    paths, manifest, plan = _load_project(config, project_id)

    phases = plan.get("phases", [])
    phase = next((item for item in phases if item["id"] == phase_id), None)
    if not phase:
        raise ValueError(f"Unknown phase '{phase_id}' for project '{project_id}'")

    if phase["status"] not in {"ready", "in_progress", "failed"}:
        raise ValueError(
            f"Phase '{phase_id}' is in status '{phase['status']}'. Use fullstack-plan or complete dependencies first."
        )

    prompt_path = ROOT / phase["prompt_template"]
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template missing: {prompt_path}")

    prompt_text = _render_prompt(prompt_path, manifest, paths, phase)
    skill_profile = kiss_bridge.get_skill(skill)
    skill_overlay = ""
    skill_policy: Dict[str, Any] | None = None
    if skill_profile:
        if not skill_profile.supports_fullstack:
            raise ValueError(f"Skill '{skill}' is not compatible with fullstack mode")
        if skill_profile.applicable_phases and phase["id"] not in skill_profile.applicable_phases:
            raise ValueError(
                f"Skill '{skill}' is not applicable to phase '{phase_id}'. "
                f"Allowed phases: {', '.join(skill_profile.applicable_phases)}"
            )
        skill_overlay = kiss_bridge.compose_skill_overlay(
            profile=skill_profile,
            phase_id=phase_id,
            project_id=plan["project_id"],
        )
        prompt_text = f"{skill_overlay}\n{prompt_text}"
        skill_policy = {
            "name": skill_profile.name,
            "status": skill_profile.status,
            "summary": skill_profile.summarize_policy(),
        }
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = paths.runs_dir / f"{run_stamp}-{phase_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    prompt_file = run_dir / "prompt.md"
    prompt_file.write_text(prompt_text, encoding="utf-8")
    if skill_overlay:
        (run_dir / "skill-overlay.md").write_text(skill_overlay, encoding="utf-8")

    codex_cmd = [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--cd",
        str(paths.app_root),
        "--output-last-message",
        str(run_dir / "codex-last-message.txt"),
    ]
    selected_model = model or manifest.get("default_model") or config.get("default_model")
    if selected_model:
        codex_cmd.extend(["--model", selected_model])
    codex_cmd.append("-")

    if dry_run:
        return {
            "status": "dry_run",
            "project_id": plan["project_id"],
            "phase": phase_id,
            "prompt_file": str(prompt_file.relative_to(ROOT)),
            "command": codex_cmd,
        }

    phase["status"] = "in_progress"
    _save_plan(paths, plan)
    _sync_state_from_plan(paths, plan)

    started_at = _utc_now()
    before_snapshot = _snapshot_tree(paths.app_root)
    try:
        codex_result = _run_command(codex_cmd, cwd=ROOT, input_text=prompt_text)
    except FileNotFoundError as exc:
        codex_result = subprocess.CompletedProcess(
            args=codex_cmd,
            returncode=127,
            stdout="",
            stderr=str(exc),
        )

    (run_dir / "codex-stdout.log").write_text(codex_result.stdout, encoding="utf-8")
    (run_dir / "codex-stderr.log").write_text(codex_result.stderr, encoding="utf-8")

    validation_results = []
    for idx, command in enumerate(phase.get("validation_commands", []), start=1):
        result = _run_command(["bash", "-lc", command], cwd=paths.app_root)
        log_file = run_dir / f"validation-{idx}.log"
        log_file.write_text(
            f"$ {command}\n\nSTDOUT\n{result.stdout}\n\nSTDERR\n{result.stderr}\n",
            encoding="utf-8",
        )
        validation_results.append(
            {
                "command": command,
                "returncode": result.returncode,
                "log_file": str(log_file.relative_to(ROOT)),
            }
        )

    after_snapshot = _snapshot_tree(paths.app_root)
    changed = _changed_files(before_snapshot, after_snapshot)
    changed_file = run_dir / "changed-files.json"
    changed_file.write_text(json.dumps(changed, indent=2) + "\n", encoding="utf-8")

    policy_violations: list[str] = []
    policy_status = None
    if skill_profile:
        policy_violations = kiss_bridge.check_scope(changed, skill_profile)
        policy_status = skill_profile.on_policy_violation
        (run_dir / "skill-policy.json").write_text(
            json.dumps(
                {
                    "skill": skill_profile.name,
                    "violations": policy_violations,
                    "policy_action": skill_profile.on_policy_violation,
                    "summary": skill_profile.summarize_policy(),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    validations_ok = all(entry["returncode"] == 0 for entry in validation_results)
    policy_ok = True
    if policy_violations and skill_profile and skill_profile.on_policy_violation == "fail":
        policy_ok = False

    run_ok = codex_result.returncode == 0 and validations_ok and policy_ok
    phase["status"] = "done" if run_ok else "failed"

    phase_record = {
        "started_at": started_at,
        "finished_at": _utc_now(),
        "phase": phase_id,
        "summary": f"Phase {phase_id} execution {'succeeded' if run_ok else 'failed'}.",
        "required_outputs": skill_policy["summary"]["required_outputs"] if skill_policy else [],
        "run_dir": str(run_dir.relative_to(ROOT)),
        "prompt_file": str(prompt_file.relative_to(ROOT)),
        "codex_command": codex_cmd,
        "codex_returncode": codex_result.returncode,
        "validation": validation_results,
        "changed_files": changed,
        "skill": skill_policy,
        "policy": {
            "violations": policy_violations,
            "action": policy_status,
        },
    }
    phase.setdefault("runs", []).append(phase_record)

    if run_ok:
        for item in phases:
            if item["status"] == "pending":
                item["status"] = "ready"
                break

    trajectory_file = paths.backtranslation_dir / "trajectory.jsonl"
    with trajectory_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(phase_record) + "\n")

    _save_plan(paths, plan)
    _sync_state_from_plan(paths, plan)

    return {
        "status": "ok" if run_ok else "failed",
        "project_id": plan["project_id"],
        "phase": phase_id,
        "run_dir": str(run_dir.relative_to(ROOT)),
        "codex_returncode": codex_result.returncode,
        "validations_ok": validations_ok,
        "skill": skill_profile.name if skill_profile else None,
        "summary": f"Phase {phase_id} execution {'succeeded' if run_ok else 'failed'}.",
        "required_outputs": skill_policy["summary"]["required_outputs"] if skill_policy else [],
        "policy": {
            "violations": policy_violations,
            "action": policy_status,
        },
        "rollback_hint": (
            "No rollback action required for a successful run."
            if run_ok
            else f"Revert undesired changes and rerun using run_dir {run_dir.relative_to(ROOT)}."
        ),
        "changed": changed,
    }


def run_all_phases(
    project_id: str,
    model: str | None = None,
    continue_on_failure: bool = False,
    skill: str | None = None,
) -> Dict[str, Any]:
    """Run ready phases in order until completion or first failure."""
    config = load_config()
    _, _, plan = _load_project(config, project_id)
    max_steps = max(1, len(plan.get("phases", [])) * 3)

    results: List[Dict[str, Any]] = []
    for _ in range(max_steps):
        plan_result = plan_project(project_id=project_id, register_state=True)
        runnable = next(
            (phase for phase in plan_result.get("phases", []) if phase["status"] in {"ready", "in_progress"}),
            None,
        )
        if not runnable:
            break

        run_result = run_phase(
            project_id=project_id,
            phase_id=runnable["id"],
            model=model,
            dry_run=False,
            skill=skill,
        )
        results.append(run_result)
        if run_result["status"] != "ok" and not continue_on_failure:
            break
    else:
        raise RuntimeError("Aborted fullstack-run-all due to excessive loop iterations.")

    final_status = project_status(project_id=project_id)
    failed = [entry for entry in results if entry.get("status") != "ok"]
    return {
        "status": "ok" if not failed else "failed",
        "project_id": final_status["project_id"],
        "phase_results": results,
        "phase_counts": final_status["phase_counts"],
    }


def project_status(project_id: str) -> Dict[str, Any]:
    """Return current status summary for one fullstack project."""
    config = load_config()
    paths, manifest, plan = _load_project(config, project_id)

    counts = {"pending": 0, "ready": 0, "in_progress": 0, "done": 0, "failed": 0}
    for phase in plan.get("phases", []):
        counts[phase["status"]] = counts.get(phase["status"], 0) + 1

    return {
        "status": "ok",
        "project_id": manifest["project_id"],
        "template": manifest["template"],
        "paper": manifest.get("paper", {}),
        "project_root": str(paths.root.relative_to(ROOT)),
        "plan_file": str(paths.plan_file.relative_to(ROOT)),
        "phase_counts": counts,
        "phases": plan.get("phases", []),
    }
