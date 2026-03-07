"""Provider-agnostic helpers for invoking agent CLIs."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.workspace import resolve_workspace

ROOT = resolve_workspace(Path(__file__).resolve()).root

BUILTIN_TOOL_PROVIDERS: dict[str, dict[str, Any]] = {
    "codex": {
        "edit_command": ["codex", "apply", "--prompt", "{prompt}", "{files}"],
        "chat_command": ["codex", "chat", "--stdin"],
        "stdin_payload": "messages_json",
    }
}


def _string_list(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    raise ValueError(f"Provider field '{field_name}' must be a list of strings")


def _expand_args(
    parts: Sequence[str],
    substitutions: Mapping[str, str],
    expansions: Mapping[str, Sequence[str]] | None = None,
) -> list[str]:
    expanded: list[str] = []
    for part in parts:
        if expansions and part in expansions:
            expanded.extend(str(item) for item in expansions[part])
            continue
        expanded.append(str(part).format(**substitutions))
    return [item for item in expanded if item]


def _resolve_provider_config(
    provider: str,
    provider_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    selected = provider.strip() or "codex"
    payload = dict(BUILTIN_TOOL_PROVIDERS.get(selected, {}))
    if provider_config:
        payload.update(provider_config)
    if not payload:
        raise ValueError(f"Unsupported agent provider '{selected}'")
    return payload


def agent_edit(
    prompt: str,
    files: Iterable[str],
    provider: str = "codex",
    provider_config: Mapping[str, Any] | None = None,
    root: Path | None = None,
) -> str:
    payload = _resolve_provider_config(provider=provider, provider_config=provider_config)
    command = _string_list(payload.get("edit_command"), "edit_command")
    if not command:
        raise ValueError(f"Provider '{provider}' does not define an edit command")

    args = _expand_args(
        command,
        substitutions={"prompt": prompt},
        expansions={"{files}": [str(item) for item in files]},
    )
    result = subprocess.run(
        args,
        cwd=str(root or ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def agent_chat(
    messages: list[dict],
    provider: str = "codex",
    provider_config: Mapping[str, Any] | None = None,
    root: Path | None = None,
) -> str:
    payload = _resolve_provider_config(provider=provider, provider_config=provider_config)
    command = _string_list(payload.get("chat_command"), "chat_command")
    if not command:
        raise ValueError(f"Provider '{provider}' does not define a chat command")

    messages_json = json.dumps({"messages": messages})
    args = _expand_args(
        command,
        substitutions={"messages_json": messages_json},
    )
    stdin_payload = messages_json if payload.get("stdin_payload") == "messages_json" else None
    result = subprocess.run(
        args,
        input=stdin_payload,
        cwd=str(root or ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout
