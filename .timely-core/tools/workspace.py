"""Workspace path resolution helpers for Timely Playbook."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

DEFAULT_CORE_DIR = ".timely-core"
DEFAULT_TIMELY_DIR = ".timely-playbook"
LEGACY_CONFIG = "timely-playbook.yaml"
RELOCATED_CONFIG = f"{DEFAULT_TIMELY_DIR}/config.yaml"


@dataclass(frozen=True)
class WorkspacePaths:
    root: Path
    core_dir: Path
    timely_dir: Path
    local_dir: Path
    runtime_dir: Path
    bin_dir: Path
    config_path: Path
    legacy_config_path: Path
    chub_dir: Path
    relocated: bool

    @property
    def skills_path(self) -> Path:
        return self.local_dir / "SKILLS.md" if self.relocated else self.root / "SKILLS.md"

    @property
    def agents_path(self) -> Path:
        return self.local_dir / "AGENTS.md" if self.relocated else self.root / "AGENTS.md"

    @property
    def ownership_path(self) -> Path:
        return self.local_dir / ".orchestrator" / "ownership.yaml" if self.relocated else self.root / ".orchestrator" / "ownership.yaml"

    @property
    def state_path(self) -> Path:
        return self.local_dir / ".orchestrator" / "state.json" if self.relocated else self.root / ".orchestrator" / "state.json"

    @property
    def status_path(self) -> Path:
        return self.local_dir / ".orchestrator" / "STATUS.md" if self.relocated else self.root / ".orchestrator" / "STATUS.md"

    @property
    def fullstack_config_path(self) -> Path:
        return self.local_dir / ".orchestrator" / "fullstack-agent.json" if self.relocated else self.root / ".orchestrator" / "fullstack-agent.json"

    @property
    def fullstack_defaults_path(self) -> Path:
        return self.core_dir / "tools" / "orchestrator" / "fullstack_defaults.json"


def _env_path(name: str) -> Path | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def _discover_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent

    for candidate in [current, *current.parents]:
        if candidate.name in {DEFAULT_CORE_DIR, DEFAULT_TIMELY_DIR}:
            return candidate.parent
        if (candidate / DEFAULT_CORE_DIR).exists() or (candidate / DEFAULT_TIMELY_DIR).exists():
            return candidate
        if (candidate / "cmd" / "timely-playbook" / "main.go").exists():
            return candidate
        if (candidate / LEGACY_CONFIG).exists():
            return candidate
        if (candidate / ".git").exists() and (candidate / "tools").exists():
            return candidate

    return current


def resolve_workspace(start: Path | None = None, repo_root: Path | None = None) -> WorkspacePaths:
    root = _env_path("TIMELY_REPO_ROOT")
    if root is None:
        root = repo_root.resolve() if repo_root is not None else _discover_root(start or Path(__file__).resolve())

    core_dir = _env_path("TIMELY_CORE_DIR") or (root / DEFAULT_CORE_DIR)
    timely_dir = _env_path("TIMELY_PLAYBOOK_DIR") or (root / DEFAULT_TIMELY_DIR)
    local_dir = _env_path("TIMELY_LOCAL_DIR") or (timely_dir / "local")
    runtime_dir = _env_path("TIMELY_RUNTIME_DIR") or (timely_dir / "runtime")
    bin_dir = _env_path("TIMELY_BIN_DIR") or (timely_dir / "bin")
    config_path = _env_path("TIMELY_CONFIG_PATH") or (root / RELOCATED_CONFIG)
    relocated = any(
        os.environ.get(name, "").strip()
        for name in (
            "TIMELY_CORE_DIR",
            "TIMELY_PLAYBOOK_DIR",
            "TIMELY_LOCAL_DIR",
            "TIMELY_RUNTIME_DIR",
            "TIMELY_BIN_DIR",
            "TIMELY_CONFIG_PATH",
        )
    ) or core_dir.exists() or timely_dir.exists() or config_path.exists()

    if not relocated:
        core_dir = root
        timely_dir = root
        local_dir = root
        runtime_dir = root
        bin_dir = root / "scripts"
        config_path = root / LEGACY_CONFIG

    chub_dir = _env_path("TIMELY_CHUB_DIR") or _env_path("CHUB_DIR") or (root / ".chub")
    return WorkspacePaths(
        root=root,
        core_dir=core_dir,
        timely_dir=timely_dir,
        local_dir=local_dir,
        runtime_dir=runtime_dir,
        bin_dir=bin_dir,
        config_path=config_path,
        legacy_config_path=root / LEGACY_CONFIG,
        chub_dir=chub_dir,
        relocated=relocated,
    )


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_core_manifest(workspace: WorkspacePaths | None = None) -> None:
    workspace = workspace or resolve_workspace()
    if not workspace.relocated:
        return

    manifest_path = workspace.core_dir / "manifest.json"
    if not manifest_path.exists():
        return

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = dict(payload.get("files", {}))
    actual: Dict[str, str] = {}
    for path in sorted(workspace.core_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(workspace.core_dir).as_posix()
        if rel == "manifest.json":
            continue
        if "__pycache__" in rel or rel.endswith(".pyc"):
            continue
        actual[rel] = _hash_file(path)

    if set(expected) != set(actual):
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise RuntimeError(f"Timely core drift detected: missing={missing} extra={extra}")

    for rel, digest in expected.items():
        if actual[rel] != digest:
            raise RuntimeError(f"Timely core drift detected at {rel}")
