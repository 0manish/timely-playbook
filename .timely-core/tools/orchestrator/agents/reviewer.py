"""Reviewer agent enforces guardrails before merge."""
from __future__ import annotations

from typing import Dict

from .base import Agent, AgentContext
from ..state import State


class ReviewerAgent(Agent):
    name = "reviewer"

    def __init__(self, ctx: AgentContext) -> None:
        self.ctx = ctx

    def run(self, task_id: str, verdict: str) -> Dict[str, str]:
        state = State.load()
        for task in state.tasks:
            if task.task_id == task_id:
                task.status = verdict
                break
        else:
            raise ValueError(f"Task {task_id} not found")
        state.save()
        state.update_status_file()
        return {"task_id": task_id, "verdict": verdict}
