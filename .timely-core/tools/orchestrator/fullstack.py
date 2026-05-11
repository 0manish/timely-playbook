"""FullStack-Agent integration helpers for the Timely orchestrator.

This module incorporates ideas from arXiv:2602.03798 by providing:
- pinned upstream sync (FullStack-Agent / FullStack-Dev / FullStack-Bench / FullStack-Learn)
- reusable project bootstrap from full-stack templates
- deterministic phase planning
- development-phase execution through a configurable agent provider with artifact capture
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
from tools.workspace import resolve_workspace, validate_core_manifest

WORKSPACE = resolve_workspace(Path(__file__).resolve())
ROOT = WORKSPACE.root
DEFAULTS_PATH = WORKSPACE.fullstack_defaults_path
CONFIG_PATH = WORKSPACE.fullstack_config_path


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


@dataclass(frozen=True)
class AgentProvider:
    """Resolved command template for one fullstack execution provider."""

    name: str
    label: str
    exec_command: Tuple[str, ...]
    model_arg: Tuple[str, ...]
    stdin_prompt: bool = True


@dataclass(frozen=True)
class AgentStack:
    """Resolved orchestration profile layered on top of an execution provider."""

    name: str
    label: str
    provider: str
    adapter: str
    orchestration_mode: str
    description: str = ""


@dataclass(frozen=True)
class OrchestrationAdapter:
    """Resolved adapter profile for handing work to an orchestration layer."""

    name: str
    label: str
    submit_command: Tuple[str, ...]
    stdin_payload: str = "none"
    completion_mode: str = "sync_exec"
    fallback_to_provider: bool = True


BUILTIN_PROVIDERS: Dict[str, Dict[str, Any]] = {
    "codex": {
        "label": "Codex CLI",
        "stdin_prompt": True,
        "exec_command": [
            "codex",
            "exec",
            "--skip-git-repo-check",
            "--cd",
            "{workdir}",
            "--output-last-message",
            "{run_dir}/agent-last-message.txt",
            "{model_args}",
            "-",
        ],
        "model_arg": ["--model", "{model}"],
    }
}

BUILTIN_STACKS: Dict[str, Dict[str, Any]] = {
    "codex_symphony": {
        "label": "Codex + Symphony",
        "provider": "codex",
        "adapter": "symphony",
        "orchestration_mode": "symphony",
        "description": (
            "Use a Symphony-style ticket control plane with Codex as the default "
            "execution provider."
        ),
    },
    "codex_cli": {
        "label": "Codex CLI",
        "provider": "codex",
        "adapter": "direct_cli",
        "orchestration_mode": "direct_cli",
        "description": "Run Timely phases directly through Codex CLI without a Symphony layer.",
    },
}

BUILTIN_ADAPTERS: Dict[str, Dict[str, Any]] = {
    "direct_cli": {
        "label": "Direct CLI execution",
        "submit_command": [],
        "stdin_payload": "none",
        "completion_mode": "sync_exec",
        "fallback_to_provider": True,
    },
    "symphony": {
        "label": "Symphony handoff",
        "submit_command": [],
        "stdin_payload": "json",
        "completion_mode": "async_handoff",
        "fallback_to_provider": True,
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _string_list(value: Any, field_name: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    raise ValueError(f"Provider field '{field_name}' must be a list of strings")


def _expand_command(
    parts: Tuple[str, ...],
    substitutions: Dict[str, str],
    expansions: Dict[str, List[str]] | None = None,
) -> List[str]:
    expanded: List[str] = []
    for part in parts:
        if expansions and part in expansions:
            expanded.extend(expansions[part])
            continue
        expanded.append(part.format(**substitutions))
    return [item for item in expanded if item]


def _resolve_provider(config: Dict[str, Any], provider_name: str | None) -> AgentProvider:
    selected = str(provider_name or config.get("default_provider") or "codex").strip() or "codex"
    raw_providers = config.get("providers", {})
    if raw_providers is not None and not isinstance(raw_providers, dict):
        raise ValueError("Config field 'providers' must be an object when present")

    provider_payload = dict(BUILTIN_PROVIDERS.get(selected, {}))
    if isinstance(raw_providers, dict) and isinstance(raw_providers.get(selected), dict):
        provider_payload.update(raw_providers[selected])

    if not provider_payload:
        available = sorted(
            set(BUILTIN_PROVIDERS)
            | (set(raw_providers.keys()) if isinstance(raw_providers, dict) else set())
        )
        raise ValueError(
            f"Unknown provider '{selected}'. Available providers: {', '.join(available)}"
        )

    exec_command = _string_list(provider_payload.get("exec_command"), "exec_command")
    if not exec_command:
        raise ValueError(f"Provider '{selected}' is missing an exec command")

    model_arg = _string_list(provider_payload.get("model_arg"), "model_arg")
    return AgentProvider(
        name=selected,
        label=str(provider_payload.get("label", selected)).strip() or selected,
        exec_command=exec_command,
        model_arg=model_arg,
        stdin_prompt=bool(provider_payload.get("stdin_prompt", True)),
    )


def _resolve_stack(config: Dict[str, Any], stack_name: str | None) -> AgentStack:
    selected = str(stack_name or config.get("default_stack") or "codex_symphony").strip() or "codex_symphony"
    raw_stacks = config.get("stacks", {})
    if raw_stacks is not None and not isinstance(raw_stacks, dict):
        raise ValueError("Config field 'stacks' must be an object when present")

    stack_payload = dict(BUILTIN_STACKS.get(selected, {}))
    if isinstance(raw_stacks, dict) and isinstance(raw_stacks.get(selected), dict):
        stack_payload.update(raw_stacks[selected])

    if not stack_payload:
        available = sorted(
            set(BUILTIN_STACKS)
            | (set(raw_stacks.keys()) if isinstance(raw_stacks, dict) else set())
        )
        raise ValueError(
            f"Unknown stack '{selected}'. Available stacks: {', '.join(available)}"
        )

    provider = str(stack_payload.get("provider", "")).strip()
    if not provider:
        raise ValueError(f"Stack '{selected}' is missing a provider")
    adapter = str(stack_payload.get("adapter", "direct_cli")).strip() or "direct_cli"

    orchestration_mode = str(stack_payload.get("orchestration_mode", "direct_cli")).strip() or "direct_cli"
    return AgentStack(
        name=selected,
        label=str(stack_payload.get("label", selected)).strip() or selected,
        provider=provider,
        adapter=adapter,
        orchestration_mode=orchestration_mode,
        description=str(stack_payload.get("description", "")).strip(),
    )


def _resolve_adapter(config: Dict[str, Any], adapter_name: str | None) -> OrchestrationAdapter:
    selected = str(adapter_name or "direct_cli").strip() or "direct_cli"
    raw_adapters = config.get("adapters", {})
    if raw_adapters is not None and not isinstance(raw_adapters, dict):
        raise ValueError("Config field 'adapters' must be an object when present")

    adapter_payload = dict(BUILTIN_ADAPTERS.get(selected, {}))
    if isinstance(raw_adapters, dict) and isinstance(raw_adapters.get(selected), dict):
        adapter_payload.update(raw_adapters[selected])

    if not adapter_payload:
        available = sorted(
            set(BUILTIN_ADAPTERS)
            | (set(raw_adapters.keys()) if isinstance(raw_adapters, dict) else set())
        )
        raise ValueError(
            f"Unknown adapter '{selected}'. Available adapters: {', '.join(available)}"
        )

    return OrchestrationAdapter(
        name=selected,
        label=str(adapter_payload.get("label", selected)).strip() or selected,
        submit_command=_string_list(adapter_payload.get("submit_command"), "submit_command"),
        stdin_payload=str(adapter_payload.get("stdin_payload", "none")).strip() or "none",
        completion_mode=str(adapter_payload.get("completion_mode", "sync_exec")).strip() or "sync_exec",
        fallback_to_provider=bool(adapter_payload.get("fallback_to_provider", True)),
    )


def _build_provider_command(
    provider: AgentProvider,
    workdir: Path,
    run_dir: Path,
    model: str | None,
) -> List[str]:
    substitutions = {
        "workdir": str(workdir),
        "run_dir": str(run_dir),
        "model": model or "",
    }
    model_args = _expand_command(provider.model_arg, substitutions) if model and provider.model_arg else []
    expansions = {"{model_args}": model_args}
    command = _expand_command(provider.exec_command, substitutions, expansions=expansions)
    if model_args and "{model_args}" not in provider.exec_command:
        command.extend(model_args)
    return command


def _build_adapter_command(
    adapter: OrchestrationAdapter,
    workdir: Path,
    run_dir: Path,
    payload_file: Path,
    prompt_file: Path,
    model: str | None,
    project_id: str,
    phase_id: str,
    stack_name: str,
    provider_name: str,
) -> List[str]:
    substitutions = {
        "workdir": str(workdir),
        "run_dir": str(run_dir),
        "payload_file": str(payload_file),
        "prompt_file": str(prompt_file),
        "model": model or "",
        "project_id": project_id,
        "phase_id": phase_id,
        "stack": stack_name,
        "provider": provider_name,
    }
    return _expand_command(adapter.submit_command, substitutions)


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
    validate_core_manifest(WORKSPACE)
    if CONFIG_PATH.exists() and not force:
        return CONFIG_PATH
    defaults = _load_json(DEFAULTS_PATH)
    _write_json(CONFIG_PATH, defaults)
    return CONFIG_PATH


def load_config() -> Dict[str, Any]:
    validate_core_manifest(WORKSPACE)
    if not CONFIG_PATH.exists():
        ensure_config()
    return _load_json(CONFIG_PATH)


def resolve_runtime_profile(
    stack: str | None = None,
    provider: str | None = None,
) -> Dict[str, Any]:
    config = load_config()
    stack_profile = _resolve_stack(config=config, stack_name=stack or config.get("default_stack"))
    adapter_profile = _resolve_adapter(config=config, adapter_name=stack_profile.adapter)
    provider_profile = _resolve_provider(
        config=config,
        provider_name=provider or stack_profile.provider or config.get("default_provider"),
    )
    orchestration_mode = stack_profile.orchestration_mode or config.get("default_orchestration_mode") or "direct_cli"
    return {
        "stack": stack_profile.name,
        "stack_label": stack_profile.label,
        "provider": provider_profile.name,
        "provider_label": provider_profile.label,
        "adapter": adapter_profile.name,
        "adapter_label": adapter_profile.label,
        "adapter_configured": bool(adapter_profile.submit_command),
        "adapter_completion_mode": adapter_profile.completion_mode,
        "adapter_fallback_to_provider": adapter_profile.fallback_to_provider,
        "orchestration_mode": orchestration_mode,
    }


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
    default_stack_name = config.get("default_stack", "codex_symphony")
    default_stack_profile = _resolve_stack(config=config, stack_name=default_stack_name)
    manifest = {
        "schema_version": config.get("schema_version", 1),
        "created_at": _utc_now(),
        "project_id": _slug(project_id),
        "paper": config.get("paper", {}),
        "template": template_id,
        "default_stack": default_stack_profile.name,
        "default_provider": default_stack_profile.provider or config.get("default_provider", "codex"),
        "default_adapter": default_stack_profile.adapter or config.get("default_adapter", "symphony"),
        "default_orchestration_mode": (
            default_stack_profile.orchestration_mode
            or config.get("default_orchestration_mode", "symphony")
        ),
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


def _build_symphony_payload(
    *,
    manifest: Dict[str, Any],
    plan: Dict[str, Any],
    phase: Dict[str, Any],
    paths: ProjectPaths,
    run_dir: Path,
    prompt_file: Path,
    provider_profile: AgentProvider,
    stack_profile: AgentStack,
    adapter_profile: OrchestrationAdapter,
    selected_model: str | None,
    task_kind: str = "fullstack_phase",
    extra: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    payload = {
        "schema_version": 1,
        "task_kind": task_kind,
        "created_at": _utc_now(),
        "project_id": manifest["project_id"],
        "phase_id": phase["id"],
        "phase_title": phase["title"],
        "stack": {
            "name": stack_profile.name,
            "label": stack_profile.label,
            "adapter": adapter_profile.name,
            "orchestration_mode": stack_profile.orchestration_mode,
        },
        "provider": {
            "name": provider_profile.name,
            "label": provider_profile.label,
            "model": selected_model,
        },
        "paths": {
            "repo_root": str(ROOT),
            "project_root": str(paths.root),
            "app_root": str(paths.app_root),
            "prompt_file": str(prompt_file),
            "run_dir": str(run_dir),
            "ownership_path": str(WORKSPACE.ownership_path),
            "state_path": str(WORKSPACE.state_path),
        },
        "validation_commands": phase.get("validation_commands", []),
        "plan_file": str(paths.plan_file),
        "manifest_file": str(paths.manifest_file),
        "template": manifest["template"],
    }
    if extra:
        payload["extra"] = extra
    return payload


def _dispatch_symphony(
    *,
    adapter_profile: OrchestrationAdapter,
    stack_profile: AgentStack,
    provider_profile: AgentProvider,
    paths: ProjectPaths,
    plan: Dict[str, Any],
    phase: Dict[str, Any],
    manifest: Dict[str, Any],
    prompt_file: Path,
    prompt_text: str,
    run_dir: Path,
    selected_model: str | None,
    extra_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    payload = _build_symphony_payload(
        manifest=manifest,
        plan=plan,
        phase=phase,
        paths=paths,
        run_dir=run_dir,
        prompt_file=prompt_file,
        provider_profile=provider_profile,
        stack_profile=stack_profile,
        adapter_profile=adapter_profile,
        selected_model=selected_model,
        extra=extra_payload,
    )
    payload_file = run_dir / "symphony-payload.json"
    payload_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    adapter_cmd = _build_adapter_command(
        adapter=adapter_profile,
        workdir=paths.app_root,
        run_dir=run_dir,
        payload_file=payload_file,
        prompt_file=prompt_file,
        model=selected_model,
        project_id=plan["project_id"],
        phase_id=phase["id"],
        stack_name=stack_profile.name,
        provider_name=provider_profile.name,
    )
    result = _run_command(
        adapter_cmd,
        cwd=ROOT,
        input_text=json.dumps(payload) if adapter_profile.stdin_payload == "json" else None,
    )
    adapter_stdout = run_dir / "adapter-stdout.log"
    adapter_stderr = run_dir / "adapter-stderr.log"
    adapter_stdout.write_text(result.stdout, encoding="utf-8")
    adapter_stderr.write_text(result.stderr, encoding="utf-8")
    return {
        "payload": payload,
        "payload_file": payload_file,
        "command": adapter_cmd,
        "result": result,
        "stdout_file": adapter_stdout,
        "stderr_file": adapter_stderr,
    }


def run_phase(
    project_id: str,
    phase_id: str,
    model: str | None = None,
    provider: str | None = None,
    stack: str | None = None,
    dry_run: bool = False,
    skill: str | None = None,
) -> Dict[str, Any]:
    """Run one fullstack phase through the configured agent provider."""
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
    stack_profile = _resolve_stack(
        config=config,
        stack_name=stack or manifest.get("default_stack"),
    )
    provider_profile = _resolve_provider(
        config=config,
        provider_name=provider or stack_profile.provider or manifest.get("default_provider"),
    )
    adapter_profile = _resolve_adapter(
        config=config,
        adapter_name=stack_profile.adapter or manifest.get("default_adapter"),
    )
    orchestration_mode = (
        stack_profile.orchestration_mode
        or manifest.get("default_orchestration_mode")
        or config.get("default_orchestration_mode")
        or "direct_cli"
    )

    prompt_file = run_dir / "prompt.md"
    prompt_file.write_text(prompt_text, encoding="utf-8")
    if skill_overlay:
        (run_dir / "skill-overlay.md").write_text(skill_overlay, encoding="utf-8")

    selected_model = model or manifest.get("default_model") or config.get("default_model")
    handoff_mode = "local_provider"
    adapter_cmd: List[str] = []
    payload_file: Path | None = None
    if orchestration_mode == "symphony":
        payload = _build_symphony_payload(
            manifest=manifest,
            plan=plan,
            phase=phase,
            paths=paths,
            run_dir=run_dir,
            prompt_file=prompt_file,
            provider_profile=provider_profile,
            stack_profile=stack_profile,
            adapter_profile=adapter_profile,
            selected_model=selected_model,
        )
        payload_file = run_dir / "symphony-payload.json"
        payload_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        if adapter_profile.submit_command:
            adapter_cmd = _build_adapter_command(
                adapter=adapter_profile,
                workdir=paths.app_root,
                run_dir=run_dir,
                payload_file=payload_file,
                prompt_file=prompt_file,
                model=selected_model,
                project_id=plan["project_id"],
                phase_id=phase["id"],
                stack_name=stack_profile.name,
                provider_name=provider_profile.name,
            )
            handoff_mode = "external_symphony"
        elif adapter_profile.fallback_to_provider:
            handoff_mode = "local_fallback"
        else:
            raise ValueError(
                f"Stack '{stack_profile.name}' requires adapter '{adapter_profile.name}', "
                "but no submit command is configured."
            )
    agent_cmd = _build_provider_command(
        provider=provider_profile,
        workdir=paths.app_root,
        run_dir=run_dir,
        model=selected_model,
    )

    if dry_run:
        return {
            "status": "dry_run",
            "project_id": plan["project_id"],
            "phase": phase_id,
            "stack": stack_profile.name,
            "stack_label": stack_profile.label,
            "adapter": adapter_profile.name,
            "adapter_label": adapter_profile.label,
            "handoff_mode": handoff_mode,
            "orchestration_mode": orchestration_mode,
            "provider": provider_profile.name,
            "provider_label": provider_profile.label,
            "prompt_file": str(prompt_file.relative_to(ROOT)),
            "payload_file": str(payload_file.relative_to(ROOT)) if payload_file else None,
            "command": adapter_cmd if handoff_mode == "external_symphony" else agent_cmd,
        }

    phase["status"] = "in_progress"
    _save_plan(paths, plan)
    _sync_state_from_plan(paths, plan)

    started_at = _utc_now()
    if handoff_mode == "external_symphony":
        dispatch = _dispatch_symphony(
            adapter_profile=adapter_profile,
            stack_profile=stack_profile,
            provider_profile=provider_profile,
            paths=paths,
            plan=plan,
            phase=phase,
            manifest=manifest,
            prompt_file=prompt_file,
            prompt_text=prompt_text,
            run_dir=run_dir,
            selected_model=selected_model,
        )
        dispatch_result = dispatch["result"]
        if dispatch_result.returncode == 0:
            phase_summary = (
                f"Phase {phase_id} handed off to external Symphony adapter "
                f"via {provider_profile.name}."
            )
            phase_record = {
                "started_at": started_at,
                "finished_at": _utc_now(),
                "phase": phase_id,
                "summary": phase_summary,
                "required_outputs": skill_policy["summary"]["required_outputs"] if skill_policy else [],
                "run_dir": str(run_dir.relative_to(ROOT)),
                "prompt_file": str(prompt_file.relative_to(ROOT)),
                "payload_file": str(dispatch["payload_file"].relative_to(ROOT)),
                "handoff_mode": handoff_mode,
                "stack": {
                    "name": stack_profile.name,
                    "label": stack_profile.label,
                    "adapter": adapter_profile.name,
                    "orchestration_mode": orchestration_mode,
                    "description": stack_profile.description,
                },
                "provider": {
                    "name": provider_profile.name,
                    "label": provider_profile.label,
                },
                "adapter": {
                    "name": adapter_profile.name,
                    "label": adapter_profile.label,
                    "completion_mode": adapter_profile.completion_mode,
                },
                "agent_command": agent_cmd,
                "adapter_command": dispatch["command"],
                "agent_returncode": None,
                "codex_command": agent_cmd,
                "codex_returncode": None,
                "validation": [],
                "changed_files": {"added": [], "removed": [], "modified": []},
                "skill": skill_policy,
                "policy": {
                    "violations": [],
                    "action": None,
                },
            }
            phase.setdefault("runs", []).append(phase_record)
            _save_plan(paths, plan)
            _sync_state_from_plan(paths, plan)
            return {
                "status": "dispatched",
                "project_id": plan["project_id"],
                "phase": phase_id,
                "stack": stack_profile.name,
                "adapter": adapter_profile.name,
                "handoff_mode": handoff_mode,
                "orchestration_mode": orchestration_mode,
                "provider": provider_profile.name,
                "run_dir": str(run_dir.relative_to(ROOT)),
                "payload_file": str(dispatch["payload_file"].relative_to(ROOT)),
                "summary": phase_summary,
                "skill": skill_profile.name if skill_profile else None,
                "rollback_hint": (
                    f"Update or cancel the external Symphony task referenced by "
                    f"{dispatch['payload_file'].relative_to(ROOT)} if the handoff was incorrect."
                ),
            }

        phase["status"] = "failed"
        phase_record = {
            "started_at": started_at,
            "finished_at": _utc_now(),
            "phase": phase_id,
            "summary": f"Phase {phase_id} Symphony handoff failed.",
            "required_outputs": skill_policy["summary"]["required_outputs"] if skill_policy else [],
            "run_dir": str(run_dir.relative_to(ROOT)),
            "prompt_file": str(prompt_file.relative_to(ROOT)),
            "payload_file": str(dispatch["payload_file"].relative_to(ROOT)),
            "handoff_mode": handoff_mode,
            "stack": {
                "name": stack_profile.name,
                "label": stack_profile.label,
                "adapter": adapter_profile.name,
                "orchestration_mode": orchestration_mode,
                "description": stack_profile.description,
            },
            "provider": {
                "name": provider_profile.name,
                "label": provider_profile.label,
            },
            "adapter": {
                "name": adapter_profile.name,
                "label": adapter_profile.label,
                "completion_mode": adapter_profile.completion_mode,
            },
            "agent_command": agent_cmd,
            "adapter_command": dispatch["command"],
            "agent_returncode": dispatch_result.returncode,
            "codex_command": agent_cmd,
            "codex_returncode": dispatch_result.returncode,
            "validation": [],
            "changed_files": {"added": [], "removed": [], "modified": []},
            "skill": skill_policy,
            "policy": {
                "violations": [],
                "action": None,
            },
        }
        phase.setdefault("runs", []).append(phase_record)
        _save_plan(paths, plan)
        _sync_state_from_plan(paths, plan)
        return {
            "status": "failed",
            "project_id": plan["project_id"],
            "phase": phase_id,
            "stack": stack_profile.name,
            "adapter": adapter_profile.name,
            "handoff_mode": handoff_mode,
            "orchestration_mode": orchestration_mode,
            "provider": provider_profile.name,
            "run_dir": str(run_dir.relative_to(ROOT)),
            "payload_file": str(dispatch["payload_file"].relative_to(ROOT)),
            "agent_returncode": dispatch_result.returncode,
            "summary": f"Phase {phase_id} Symphony handoff failed.",
            "skill": skill_profile.name if skill_profile else None,
            "rollback_hint": (
                f"Inspect adapter logs in {run_dir.relative_to(ROOT)} and retry the external handoff."
            ),
        }

    before_snapshot = _snapshot_tree(paths.app_root)
    try:
        agent_result = _run_command(
            agent_cmd,
            cwd=ROOT,
            input_text=prompt_text if provider_profile.stdin_prompt else None,
        )
    except FileNotFoundError as exc:
        agent_result = subprocess.CompletedProcess(
            args=agent_cmd,
            returncode=127,
            stdout="",
            stderr=str(exc),
        )

    agent_stdout = run_dir / "agent-stdout.log"
    agent_stderr = run_dir / "agent-stderr.log"
    agent_stdout.write_text(agent_result.stdout, encoding="utf-8")
    agent_stderr.write_text(agent_result.stderr, encoding="utf-8")
    if provider_profile.name == "codex":
        shutil.copyfile(agent_stdout, run_dir / "codex-stdout.log")
        shutil.copyfile(agent_stderr, run_dir / "codex-stderr.log")
        agent_last_message = run_dir / "agent-last-message.txt"
        if agent_last_message.exists():
            shutil.copyfile(agent_last_message, run_dir / "codex-last-message.txt")

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

    run_ok = agent_result.returncode == 0 and validations_ok and policy_ok
    phase["status"] = "done" if run_ok else "failed"
    phase_summary = (
        f"Phase {phase_id} execution via {provider_profile.name} "
        f"{'succeeded' if run_ok else 'failed'}."
    )

    phase_record = {
        "started_at": started_at,
        "finished_at": _utc_now(),
        "phase": phase_id,
        "summary": phase_summary,
        "required_outputs": skill_policy["summary"]["required_outputs"] if skill_policy else [],
        "run_dir": str(run_dir.relative_to(ROOT)),
        "prompt_file": str(prompt_file.relative_to(ROOT)),
        "payload_file": str(payload_file.relative_to(ROOT)) if payload_file else None,
        "handoff_mode": handoff_mode,
        "stack": {
            "name": stack_profile.name,
            "label": stack_profile.label,
            "adapter": adapter_profile.name,
            "orchestration_mode": orchestration_mode,
            "description": stack_profile.description,
        },
        "provider": {
            "name": provider_profile.name,
            "label": provider_profile.label,
        },
        "agent_command": agent_cmd,
        "agent_returncode": agent_result.returncode,
        "codex_command": agent_cmd,
        "codex_returncode": agent_result.returncode,
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
        "stack": stack_profile.name,
        "adapter": adapter_profile.name,
        "handoff_mode": handoff_mode,
        "orchestration_mode": orchestration_mode,
        "provider": provider_profile.name,
        "run_dir": str(run_dir.relative_to(ROOT)),
        "agent_returncode": agent_result.returncode,
        "codex_returncode": agent_result.returncode,
        "validations_ok": validations_ok,
        "skill": skill_profile.name if skill_profile else None,
        "summary": phase_summary,
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
    provider: str | None = None,
    stack: str | None = None,
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
            provider=provider,
            stack=stack,
            dry_run=False,
            skill=skill,
        )
        results.append(run_result)
        if run_result["status"] == "dispatched":
            break
        if run_result["status"] != "ok" and not continue_on_failure:
            break
    else:
        raise RuntimeError("Aborted fullstack-run-all due to excessive loop iterations.")

    final_status = project_status(project_id=project_id)
    failed = [entry for entry in results if entry.get("status") == "failed"]
    dispatched = [entry for entry in results if entry.get("status") == "dispatched"]
    return {
        "status": "failed" if failed else ("dispatched" if dispatched else "ok"),
        "project_id": final_status["project_id"],
        "phase_results": results,
        "phase_counts": final_status["phase_counts"],
    }


def reconcile_phase(
    project_id: str,
    phase_id: str,
    state: str,
    summary: str | None = None,
    external_run_id: str | None = None,
) -> Dict[str, Any]:
    """Reconcile one externally managed phase back into Timely state."""
    config = load_config()
    paths, _, plan = _load_project(config, project_id)
    phases = plan.get("phases", [])
    phase = next((item for item in phases if item["id"] == phase_id), None)
    if not phase:
        raise ValueError(f"Unknown phase '{phase_id}' for project '{project_id}'")

    normalized = state.strip().lower()
    allowed = {"pending", "ready", "in_progress", "done", "failed"}
    if normalized not in allowed:
        raise ValueError(f"Unsupported reconcile state '{state}'. Allowed: {', '.join(sorted(allowed))}")

    phase["status"] = normalized
    if phase.get("runs"):
        phase["runs"][-1]["reconciliation"] = {
            "state": normalized,
            "summary": summary or "",
            "external_run_id": external_run_id,
            "updated_at": _utc_now(),
        }

    if normalized == "done":
        for item in phases:
            if item["status"] == "pending":
                item["status"] = "ready"
                break

    _save_plan(paths, plan)
    _sync_state_from_plan(paths, plan)
    return {
        "status": "ok",
        "project_id": plan["project_id"],
        "phase": phase_id,
        "phase_state": normalized,
        "summary": summary or "",
        "external_run_id": external_run_id,
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
        "default_stack": manifest.get("default_stack") or config.get("default_stack") or "codex_symphony",
        "default_provider": manifest.get("default_provider") or config.get("default_provider") or "codex",
        "default_adapter": manifest.get("default_adapter") or config.get("default_adapter") or "symphony",
        "default_orchestration_mode": (
            manifest.get("default_orchestration_mode")
            or config.get("default_orchestration_mode")
            or "symphony"
        ),
        "paper": manifest.get("paper", {}),
        "project_root": str(paths.root.relative_to(ROOT)),
        "plan_file": str(paths.plan_file.relative_to(ROOT)),
        "phase_counts": counts,
        "phases": plan.get("phases", []),
    }


def dispatch_autofix(
    repo: str,
    workflow: str,
    head_branch: str,
    run_url: str,
    stack: str | None = None,
    provider: str | None = None,
) -> Dict[str, Any]:
    """Hand a CI autofix task to the configured external Symphony adapter."""
    config = load_config()
    runtime = resolve_runtime_profile(stack=stack, provider=provider)
    if runtime["orchestration_mode"] != "symphony":
        raise ValueError("Autofix dispatch only applies to Symphony-mode stacks")
    if not runtime["adapter_configured"]:
        raise ValueError("No Symphony submit command is configured for autofix dispatch")

    stack_profile = _resolve_stack(config=config, stack_name=runtime["stack"])
    adapter_profile = _resolve_adapter(config=config, adapter_name=stack_profile.adapter)
    provider_profile = _resolve_provider(config=config, provider_name=runtime["provider"])

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = ROOT / ".timely-playbook" / "local" / ".orchestrator" / "autofix" / run_stamp
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = run_dir / "autofix-prompt.md"
    prompt_text = (
        f"CI failed for repository {repo} on branch {head_branch}.\n\n"
        f"Workflow URL: {run_url}\n"
        f"Workflow name: {workflow}\n\n"
        "Repair the issue, obey repository ownership rules, and open a pull request with the fix."
    )
    prompt_file.write_text(prompt_text, encoding="utf-8")
    payload = {
        "schema_version": 1,
        "task_kind": "autofix",
        "created_at": _utc_now(),
        "stack": runtime,
        "provider": {
            "name": provider_profile.name,
            "label": provider_profile.label,
        },
        "repo": repo,
        "workflow": workflow,
        "head_branch": head_branch,
        "run_url": run_url,
        "paths": {
            "repo_root": str(ROOT),
            "ownership_path": str(WORKSPACE.ownership_path),
            "run_dir": str(run_dir),
            "prompt_file": str(prompt_file),
        },
        "instructions": prompt_text,
    }
    payload_file = run_dir / "autofix-payload.json"
    payload_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    adapter_cmd = _build_adapter_command(
        adapter=adapter_profile,
        workdir=ROOT,
        run_dir=run_dir,
        payload_file=payload_file,
        prompt_file=prompt_file,
        model=config.get("default_model"),
        project_id=repo.replace("/", "-"),
        phase_id="autofix",
        stack_name=stack_profile.name,
        provider_name=provider_profile.name,
    )
    result = _run_command(
        adapter_cmd,
        cwd=ROOT,
        input_text=json.dumps(payload) if adapter_profile.stdin_payload == "json" else None,
    )
    (run_dir / "adapter-stdout.log").write_text(result.stdout, encoding="utf-8")
    (run_dir / "adapter-stderr.log").write_text(result.stderr, encoding="utf-8")
    return {
        "status": "ok" if result.returncode == 0 else "failed",
        "stack": stack_profile.name,
        "provider": provider_profile.name,
        "adapter": adapter_profile.name,
        "payload_file": str(payload_file.relative_to(ROOT)),
        "run_dir": str(run_dir.relative_to(ROOT)),
        "returncode": result.returncode,
    }
