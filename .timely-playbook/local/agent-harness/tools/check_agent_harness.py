#!/usr/bin/env python3
"""Lightweight generic harness checks for Timely-seeded repos.

Validates consistency between skill registries and optionally agent rosters.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List


def _repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if p.name != "local" and (p / "AGENTS.md").exists():
            return p
        if (p / ".timely-playbook" / "local" / "SKILLS.md").exists() and (
            p / ".timely-playbook" / "local" / "AGENTS.md"
        ).exists():
            return p
        p = p.parent
    return p


REPO_ROOT = _repo_root()


def _load(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_json_block(text: str) -> Dict[str, object] | None:
    m = re.search(r"```json\n(.*?)\n```", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def _skill_paths_from_json(skills_path: Path) -> set[str]:
    data = _extract_json_block(_load(skills_path))
    paths: set[str] = set()
    if not data:
        return paths
    for item in data.get("repo_local_skills", {}).values():
        p = item.get("path")
        if isinstance(p, str) and p.endswith("SKILL.md"):
            paths.add(str(Path(p)))
    return paths


def _discover_skill_paths() -> set[str]:
    return {
        p.relative_to(REPO_ROOT).as_posix()
        for p in (REPO_ROOT / ".timely-playbook/local/skills").glob("*/SKILL.md")
    }


def _md_links_from_file(path: Path) -> set[str]:
    text = _load(path)
    links = set()
    links.update(re.findall(r"\[[^\]]+\]\(([^\)]+)\)", text))
    links.update(re.findall(r"`([^`]+\.md)`", text))
    return {
        Path(item).as_posix()
        for item in links
        if item.endswith(".md")
    }


def check_skills(issues: List[str]) -> None:
    skills_doc = REPO_ROOT / ".timely-playbook/local/SKILLS.md"
    if not skills_doc.exists():
        issues.append("missing .timely-playbook/local/SKILLS.md")
        return

    listed = set(_skill_paths_from_json(skills_doc))
    actual = {p for p in _discover_skill_paths()}

    if listed and not actual:
        issues.append("SKILLS.md has local skill registry entries but no local skill files were found")
        return

    missing = sorted(actual - listed)
    extra = sorted(listed - actual)
    if missing:
        issues.append(f"unregistered local skills in .timely-playbook/local/skills: {', '.join(missing)}")
    if extra:
        issues.append(f"SKILLS.md lists missing local skill files: {', '.join(extra)}")


def check_agent_roster(issues: List[str]) -> None:
    agents_dir = REPO_ROOT / ".agents/agents"
    agents_readme = REPO_ROOT / ".agents/README.md"
    if not agents_dir.exists():
        return
    actual = {
        p.as_posix()
        for p in agents_dir.glob("*.md")
    }
    if not actual:
        issues.append(".agents/agents exists but contains no agent definitions")
        return
    if not agents_readme.exists():
        issues.append(".agents/agents exists but .agents/README.md is missing")
        return
    listed = {p for p in _md_links_from_file(agents_readme) if p.startswith(".agents/agents/")}
    if not listed:
        issues.append(".agents/README.md does not enumerate .agents/agents/*.md")
        return
    missing = sorted(actual - listed)
    stale = sorted(listed - actual)
    if missing:
        issues.append(f"agent files not registered in .agents/README.md: {', '.join(missing)}")
    if stale:
        issues.append(f".agents/README.md references missing agent files: {', '.join(stale)}")


def run_checks(json_mode: bool = False) -> int:
    issues: List[str] = []
    check_skills(issues)
    check_agent_roster(issues)

    if json_mode:
        print(json.dumps({"pass": not issues, "issues": issues}, indent=2, sort_keys=True))
    else:
        status = "PASS" if not issues else "FAIL"
        print(f"timely-agent-harness checks: {status}")
        if issues:
            for item in issues:
                print(f"- {item}")
    return 0 if not issues else 1


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run generic Timely agent-harness checks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return run_checks(json_mode=parser.parse_args(argv).json)


if __name__ == "__main__":
    raise SystemExit(main())
