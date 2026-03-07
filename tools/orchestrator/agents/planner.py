"""Planner agent emits task graphs based on repository goals."""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

from .base import Agent, AgentContext
from ..state import State, Task


class PlannerAgent(Agent):
    name = "planner"

    def __init__(self, ctx: AgentContext) -> None:
        self.ctx = ctx

    def run(self, goal: str, ready_tasks: List[str] | None = None) -> Dict[str, Any]:
        state = State.load()
        state.goal = goal
        ready_tasks = ready_tasks or []
        now = dt.datetime.utcnow().isoformat()
        new_task = Task(
            task_id=f"PLAN-{now[:19].replace(':', '').replace('-', '')}",
            title="Refresh coordination plan",
            owner=self.name,
            status="done",
            artifacts=[".orchestrator/state.json"],
        )
        state.tasks.append(new_task)
        state.plan["last_refresh"] = now
        state.plan["ready_tasks"] = ready_tasks
        state.save()
        state.update_status_file()
        return {
            "status": "ok",
            "task_id": new_task.task_id,
            "active_goal": state.goal,
        }
