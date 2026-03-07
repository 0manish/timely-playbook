"""KISS-to-Codex skill loading and scope helpers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[3]
SKILLS_PATH = ROOT / "SKILLS.md"
JSON_BLOCK_RE = re.compile(r"```json\n(.*?)```", re.S)


@dataclass(frozen=True)
class SkillProfile:
    """Parsed skill entry used by fullstack overlays."""

    name: str
    description: str
    status: str
    supports_fullstack: bool
    prompt_prefix: str
    sections: Dict[str, str]
    allowed_paths: Tuple[str, ...]
    forbidden_paths: Tuple[str, ...]
    applicable_phases: Tuple[str, ...]
    max_changed_files: int
    on_policy_violation: str
    required_outputs: Tuple[str, ...]

    def overlay_lines(self, phase_id: str, project_id: str) -> list[str]:
        """Return human-readable overlay lines for prompt injection."""

        lines = [
            "# Skill overlay (Timely Playbook + KISS A-E)",
            f"Skill: {self.name}",
            f"Description: {self.description}",
            f"Project: {project_id}",
            f"Phase: {phase_id}",
            "",
            "Policy sections:",
        ]
        for key in sorted(self.sections):
            lines.append(f"- {key}: {self.sections[key]}")

        lines.extend(
            [
                "",
                "Execution constraints:",
                f"Allowed paths: {', '.join(self.allowed_paths) or 'default app scope'}",
                f"Forbidden paths: {', '.join(self.forbidden_paths) or 'none'}",
                f"Max changed files: {self.max_changed_files}",
                f"Policy action on violation: {self.on_policy_violation}",
            ]
        )
        return lines

    def summarize_policy(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "supports_fullstack": self.supports_fullstack,
            "allowed_paths": list(self.allowed_paths),
            "forbidden_paths": list(self.forbidden_paths),
            "applicable_phases": list(self.applicable_phases),
            "max_changed_files": self.max_changed_files,
            "on_policy_violation": self.on_policy_violation,
            "required_outputs": list(self.required_outputs),
        }


def _normalize_path_patterns(patterns: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    normalized = []
    for item in patterns:
        value = (item or "").strip()
        if not value:
            continue
        normalized.append(value.lstrip("/"))
    return tuple(normalized)


def _load_skill_registry(skills_path: Path = SKILLS_PATH) -> Dict[str, Any]:
    """Load and parse the JSON registry block from SKILLS.md."""
    if not skills_path.exists():
        return {}

    source = skills_path.read_text(encoding="utf-8")
    for block in JSON_BLOCK_RE.findall(source):
        text = block.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and "skills" in payload:
            return payload
    return {}


def _to_skill_profile(name: str, payload: Dict[str, Any]) -> SkillProfile:
    sections = payload.get("sections", {})
    if not isinstance(sections, dict):
        sections = {}

    scope = payload.get("scope", {})
    if not isinstance(scope, dict):
        scope = {}

    allowed = _normalize_path_patterns(scope.get("allowed_paths", []))
    forbidden = _normalize_path_patterns(scope.get("forbidden_paths", []))
    applicable = _normalize_path_patterns(scope.get("applicable_phases", ()))

    return SkillProfile(
        name=name,
        description=str(payload.get("description", "")).strip(),
        status=str(payload.get("status", "inactive")).strip().lower(),
        supports_fullstack=bool(payload.get("supports_fullstack", False)),
        prompt_prefix=str(payload.get("prompt_prefix", "")).strip(),
        sections={str(key): str(value).strip() for key, value in sections.items() if value is not None},
        allowed_paths=allowed,
        forbidden_paths=forbidden,
        applicable_phases=applicable,
        max_changed_files=int(scope.get("max_changed_files", 0) or 0),
        on_policy_violation=str(scope.get("on_policy_violation", "warn")).strip().lower() or "warn",
        required_outputs=tuple(str(item).strip() for item in payload.get("required_outputs", ())),
    )


def load_skills(skills_path: Path = SKILLS_PATH) -> Dict[str, SkillProfile]:
    """Return active skill profiles from SKILLS.md."""
    payload = _load_skill_registry(skills_path=skills_path)
    skills: Dict[str, SkillProfile] = {}
    raw_skills = payload.get("skills", {})
    if not isinstance(raw_skills, dict):
        return {}

    for name, raw in raw_skills.items():
        if not isinstance(raw, dict):
            continue
        profile = _to_skill_profile(name, raw)
        if profile.status == "active":
            skills[name] = profile
    return skills


def get_default_skill_name(skills_path: Path = SKILLS_PATH) -> str:
    payload = _load_skill_registry(skills_path=skills_path)
    name = payload.get("default_skill", "")
    return str(name).strip()


def get_skill(profile_name: str | None, skills_path: Path = SKILLS_PATH) -> SkillProfile | None:
    """Resolve a named skill profile.

    Returns None only when no name is supplied. Raises ValueError for unknown,
    inactive, or unknown-default skill references.
    """
    if profile_name is None:
        return None

    profile_name = profile_name.strip()
    if not profile_name:
        return None

    skills = load_skills(skills_path=skills_path)
    if not skills:
        raise ValueError("No active skills loaded from SKILLS.md")

    if profile_name == "default":
        profile_name = get_default_skill_name(skills_path=skills_path)

    profile = skills.get(profile_name)
    if profile is None:
        available = ", ".join(sorted(skills.keys()))
        raise ValueError(f"Unknown or inactive skill '{profile_name}'. Available: {available}")
    return profile


def compose_skill_overlay(profile: SkillProfile, phase_id: str, project_id: str) -> str:
    lines = [profile.prompt_prefix] if profile.prompt_prefix else []
    lines.extend(profile.overlay_lines(phase_id=phase_id, project_id=project_id))
    return "\n".join(lines).strip() + "\n"


def _matches(path: str, pattern: str) -> bool:
    path = path.replace("\\", "/").strip("/")
    candidate = pattern.strip().strip("/")
    return fnmatch(path, candidate)


def check_scope(changed_files: Dict[str, List[str]], profile: SkillProfile) -> list[str]:
    """Return violations for changed files against skill scope config."""
    violations: list[str] = []
    tracked = sorted(set(changed_files.get("added", []) + changed_files.get("modified", []) + changed_files.get("removed", [])))

    for entry in tracked:
        if profile.forbidden_paths and any(_matches(entry, item) for item in profile.forbidden_paths):
            violations.append(f"forbidden-path: {entry}")

        if profile.allowed_paths and not any(_matches(entry, item) for item in profile.allowed_paths):
            violations.append(f"outside-allowed-scope: {entry}")

    if profile.max_changed_files > 0 and len(tracked) > profile.max_changed_files:
        violations.append(
            f"changed-file-limit: {len(tracked)} > {profile.max_changed_files}"
        )

    return violations

