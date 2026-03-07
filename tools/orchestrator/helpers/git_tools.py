"""Git helpers used by orchestrator agents."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, Optional

ROOT = Path(__file__).resolve().parents[3]


def run_git(args: Iterable[str], cwd: Optional[Path] = None) -> str:
    cwd = cwd or ROOT
    result = subprocess.run([
        "git",
        *args,
    ], cwd=str(cwd), check=True, capture_output=True, text=True)
    return result.stdout.strip()


def ensure_branch(branch: str, base: str = "main") -> None:
    existing = run_git(["branch", "--list", branch])
    if existing:
        return
    run_git(["fetch", "origin", base])
    run_git(["checkout", "-b", branch, f"origin/{base}"])


def commit_all(message: str) -> None:
    run_git(["add", "-A"])
    run_git(["commit", "-m", message])


def push(branch: str, set_upstream: bool = True) -> None:
    args = ["push"]
    if set_upstream:
        args.extend(["-u", "origin", branch])
    else:
        args.extend(["origin", branch])
    run_git(args)
