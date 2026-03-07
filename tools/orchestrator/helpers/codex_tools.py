"""Wrapper for invoking the Codex CLI or MCP server."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]


def codex_edit(prompt: str, files: Iterable[str]) -> str:
    args = ["codex", "apply", "--prompt", prompt, *files]
    result = subprocess.run(args, cwd=str(ROOT), check=True, capture_output=True, text=True)
    return result.stdout


def codex_chat(messages: list[dict]) -> str:
    payload = json.dumps({"messages": messages})
    result = subprocess.run(
        ["codex", "chat", "--stdin"],
        input=payload,
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout
