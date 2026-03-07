"""Implementer agent writes code for a specific area."""
from __future__ import annotations

from typing import Dict

from .base import Agent, AgentContext
from ..state import State


class ImplementerAgent(Agent):
    name = "implementer"

    def __init__(self, ctx: AgentContext, owner: str) -> None:
        self.ctx = ctx
        self.owner = owner

    def run(self, task_id: str) -> Dict[str, str]:
        state = State.load()
        for task in state.tasks:
            if task.task_id == task_id:
                task.status = "in_progress"
                task.owner = self.owner
                break
        else:
            raise ValueError(f"Task {task_id} not found")
        state.save()
        state.update_status_file()
        return {"status": "started", "task_id": task_id, "owner": self.owner}
