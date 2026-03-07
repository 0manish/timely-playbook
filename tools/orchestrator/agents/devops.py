"""DevOps agent coordinates deployments and rollbacks."""
from __future__ import annotations

from typing import Dict

from .base import Agent, AgentContext
from ..state import State


class DevOpsAgent(Agent):
    name = "devops"

    def __init__(self, ctx: AgentContext) -> None:
        self.ctx = ctx

    def run(self, environment: str, result: str) -> Dict[str, str]:
        state = State.load()
        state.decisions.append({
            "id": f"DEPLOY-{environment}",
            "topic": f"Deploy to {environment}",
            "status": result,
        })
        state.save()
        state.update_status_file()
        return {"environment": environment, "result": result}
