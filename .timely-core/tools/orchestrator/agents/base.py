"""Base definitions for orchestrator-managed agents."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class AgentContext:
    repo_root: str
    ownership_path: str
    state_path: str


class Agent:
    name: str = "agent"

    def run(self, **_: Any) -> Dict[str, Any]:  # pragma: no cover - template behaviour
        raise NotImplementedError
