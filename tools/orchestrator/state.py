"""Helpers for reading and writing /.orchestrator/state.json."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / ".orchestrator" / "state.json"
STATUS_PATH = ROOT / ".orchestrator" / "STATUS.md"


@dataclass
class Task:
    task_id: str
    title: str
    owner: str
    status: str
    branch: Optional[str] = None
    pr: Optional[str] = None
    deps: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            task_id=data.get("id", ""),
            title=data.get("title", ""),
            owner=data.get("owner", ""),
            status=data.get("status", "pending"),
            branch=data.get("branch"),
            pr=data.get("pr"),
            deps=data.get("deps", []),
            artifacts=data.get("artifacts", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.task_id,
            "title": self.title,
            "owner": self.owner,
            "status": self.status,
            "branch": self.branch,
            "pr": self.pr,
            "deps": self.deps,
            "artifacts": self.artifacts,
        }


@dataclass
class State:
    goal: str
    plan: Dict[str, Any]
    tasks: List[Task]
    ci_runs: List[Dict[str, Any]]
    decisions: List[Dict[str, Any]]

    @classmethod
    def load(cls) -> "State":
        data = json.loads(STATE_PATH.read_text())
        tasks = [Task.from_dict(entry) for entry in data.get("tasks", [])]
        return cls(
            goal=data.get("goal", ""),
            plan=data.get("plan", {}),
            tasks=tasks,
            ci_runs=data.get("ci_runs", []),
            decisions=data.get("decisions", []),
        )

    def save(self) -> None:
        payload = {
            "goal": self.goal,
            "plan": self.plan,
            "tasks": [task.to_dict() for task in self.tasks],
            "ci_runs": self.ci_runs,
            "decisions": self.decisions,
        }
        STATE_PATH.write_text(json.dumps(payload, indent=2) + "\n")

    def update_status_file(self) -> None:
        ready = [task.task_id for task in self.tasks if task.status == "ready"]
        active = [task.task_id for task in self.tasks if task.status == "in_progress"]
        review = [task.task_id for task in self.tasks if task.status == "review"]
        lines = [
            "# Orchestrator status dashboard",
            "",
            f"- **Current goal:** {self.goal or 'Set goal via orchestrator.'}",
            f"- **Active tasks:** {', '.join(active) or 'None'}",
            f"- **Ready for review:** {', '.join(review) or 'None'}",
            f"- **Next ready tasks:** {', '.join(ready) or 'None'}",
            "- **CI summary:** See .github/workflows/ci.yml for latest results.",
        ]
        STATUS_PATH.write_text("\n".join(lines) + "\n")
