"""Tester agent runs test batteries and records CI references."""
from __future__ import annotations

from typing import Dict

from .base import Agent, AgentContext
from ..state import State


class TesterAgent(Agent):
    name = "tester"

    def __init__(self, ctx: AgentContext) -> None:
        self.ctx = ctx

    def run(self, workflow_url: str) -> Dict[str, str]:
        state = State.load()
        state.ci_runs.append({"url": workflow_url})
        state.save()
        state.update_status_file()
        return {"status": "recorded", "workflow": workflow_url}
