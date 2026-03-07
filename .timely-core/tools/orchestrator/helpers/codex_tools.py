"""Compatibility wrapper around provider-agnostic agent helpers."""
from __future__ import annotations

from typing import Iterable

from .agent_tools import agent_chat, agent_edit


def codex_edit(prompt: str, files: Iterable[str]) -> str:
    return agent_edit(prompt=prompt, files=files, provider="codex")


def codex_chat(messages: list[dict]) -> str:
    return agent_chat(messages=messages, provider="codex")
