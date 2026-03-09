"""Helpers for reading and writing Timely orchestrator state through CXDB."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from tools.context.cxdb import CXDB, ContextDocument
from tools.context.leann import LEANNIndex
from tools.workspace import resolve_workspace

WORKSPACE = resolve_workspace(Path(__file__).resolve())
ROOT = WORKSPACE.root
STATE_PATH = WORKSPACE.state_path
STATUS_PATH = WORKSPACE.status_path
CXDB_PATH = WORKSPACE.cxdb_path
LEANN_INDEX_PATH = WORKSPACE.leann_index_path


def _json_payload(goal: str, plan: Dict[str, Any], tasks: Iterable["Task"], ci_runs: List[Dict[str, Any]], decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "goal": goal,
        "plan": plan,
        "tasks": [task.to_dict() for task in tasks],
        "ci_runs": ci_runs,
        "decisions": decisions,
    }


def _coerce_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "goal": data.get("goal", ""),
        "plan": data.get("plan", {}),
        "tasks": data.get("tasks", []),
        "ci_runs": data.get("ci_runs", []),
        "decisions": data.get("decisions", []),
    }


def _relative_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _markdown_context_files() -> List[Path]:
    candidates = [
        WORKSPACE.agents_path,
        WORKSPACE.skills_path,
        WORKSPACE.ownership_path,
        STATUS_PATH,
    ]
    tracker_dir = WORKSPACE.local_dir / "timely-trackers"
    if tracker_dir.exists():
        candidates.extend(sorted(path for path in tracker_dir.rglob("*") if path.is_file()))
    return [path for path in candidates if path.exists() and path.is_file()]


def _build_documents(payload: Dict[str, Any]) -> List[ContextDocument]:
    documents: List[ContextDocument] = []

    goal = str(payload.get("goal", "")).strip()
    if goal:
        documents.append(
            ContextDocument(
                doc_id="state/goal",
                kind="state",
                title="Active goal",
                body=goal,
                source_path=_relative_path(CXDB_PATH),
                metadata={"section": "goal"},
            )
        )

    plan = payload.get("plan", {})
    if plan:
        plan_summary = []
        if plan.get("summary"):
            plan_summary.append(str(plan["summary"]))
        notes = plan.get("notes", [])
        if notes:
            plan_summary.append("Notes:\n- " + "\n- ".join(str(note) for note in notes))
        milestones = plan.get("milestones", [])
        if milestones:
            rendered = []
            for milestone in milestones:
                rendered.append(
                    f"{milestone.get('id', '')}: {milestone.get('name', '')} target={milestone.get('target', '')}"
                )
            plan_summary.append("Milestones:\n- " + "\n- ".join(rendered))
        documents.append(
            ContextDocument(
                doc_id="state/plan",
                kind="state",
                title="Coordination plan",
                body="\n\n".join(plan_summary) or json.dumps(plan, indent=2),
                source_path=_relative_path(CXDB_PATH),
                metadata={"section": "plan"},
            )
        )

    for task in payload.get("tasks", []):
        documents.append(
            ContextDocument(
                doc_id=f"task/{task.get('id', '')}",
                kind="task",
                title=task.get("title", task.get("id", "task")),
                body="\n".join(
                    [
                        f"Task ID: {task.get('id', '')}",
                        f"Owner: {task.get('owner', '')}",
                        f"Status: {task.get('status', '')}",
                        f"Branch: {task.get('branch') or ''}",
                        f"PR: {task.get('pr') or ''}",
                        f"Dependencies: {', '.join(task.get('deps', [])) or 'None'}",
                        f"Artifacts: {', '.join(task.get('artifacts', [])) or 'None'}",
                    ]
                ),
                source_path=_relative_path(CXDB_PATH),
                metadata={"section": "tasks", "task_id": task.get("id", "")},
            )
        )

    for idx, run in enumerate(payload.get("ci_runs", []), start=1):
        doc_id = run.get("id") or f"ci-run-{idx}"
        documents.append(
            ContextDocument(
                doc_id=f"ci/{doc_id}",
                kind="ci_run",
                title=run.get("workflow", run.get("summary", doc_id)),
                body=json.dumps(run, indent=2, sort_keys=True),
                source_path=_relative_path(CXDB_PATH),
                metadata={"section": "ci_runs", "ci_id": doc_id},
            )
        )

    for idx, decision in enumerate(payload.get("decisions", []), start=1):
        doc_id = decision.get("id") or f"decision-{idx}"
        body = "\n".join(
            [
                f"Topic: {decision.get('topic', '')}",
                f"Status: {decision.get('status', '')}",
                f"Context: {decision.get('context', '')}",
                f"Timestamp: {decision.get('timestamp', '')}",
            ]
        ).strip()
        documents.append(
            ContextDocument(
                doc_id=f"decision/{doc_id}",
                kind="decision",
                title=decision.get("topic", doc_id),
                body=body or json.dumps(decision, indent=2, sort_keys=True),
                source_path=_relative_path(CXDB_PATH),
                metadata={"section": "decisions", "decision_id": doc_id},
            )
        )

    for path in _markdown_context_files():
        text = _read_text(path)
        if not text:
            continue
        first_line = next((line.strip("# ").strip() for line in text.splitlines() if line.strip()), path.name)
        documents.append(
            ContextDocument(
                doc_id=f"file/{_relative_path(path)}",
                kind="workspace_file",
                title=first_line,
                body=text,
                source_path=_relative_path(path),
                metadata={"section": "workspace", "path": _relative_path(path)},
            )
        )

    return documents


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
        store = CXDB(CXDB_PATH)
        export_exists = STATE_PATH.exists()
        db_exists = store.exists()

        use_export = export_exists and (
            not db_exists or STATE_PATH.stat().st_mtime > CXDB_PATH.stat().st_mtime
        )

        if use_export:
            data = _coerce_payload(json.loads(STATE_PATH.read_text(encoding="utf-8")))
            store.save_state(data, event_type="imported_state_export")
        elif db_exists:
            data = _coerce_payload(store.load_state())
        else:
            data = _coerce_payload({})
            STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            STATE_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            store.save_state(data, event_type="initialized_state_store")

        tasks = [Task.from_dict(entry) for entry in data.get("tasks", [])]
        return cls(
            goal=data.get("goal", ""),
            plan=data.get("plan", {}),
            tasks=tasks,
            ci_runs=data.get("ci_runs", []),
            decisions=data.get("decisions", []),
        )

    def _payload(self) -> Dict[str, Any]:
        return _json_payload(
            goal=self.goal,
            plan=self.plan,
            tasks=self.tasks,
            ci_runs=self.ci_runs,
            decisions=self.decisions,
        )

    def refresh_context_store(self) -> Dict[str, Any]:
        payload = self._payload()
        store = CXDB(CXDB_PATH)
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        store.save_state(payload)

        documents = _build_documents(payload)
        stored_docs = store.replace_documents(documents)
        leann = LEANNIndex(LEANN_INDEX_PATH)
        index_summary = leann.build(documents)
        return {
            "cxdb_path": _relative_path(CXDB_PATH),
            "leann_index_path": _relative_path(LEANN_INDEX_PATH),
            "documents": stored_docs,
            "generated_at": index_summary["generated_at"],
        }

    def save(self) -> None:
        self.refresh_context_store()

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
            f"- **CXDB store:** `{_relative_path(CXDB_PATH)}`",
            f"- **LEANN index:** `{_relative_path(LEANN_INDEX_PATH)}`",
            "- **CI summary:** See .github/workflows/ci.yml for latest results.",
        ]
        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATUS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.refresh_context_store()


def sync_context() -> Dict[str, Any]:
    state = State.load()
    return state.refresh_context_store()


def search_context(query: str, limit: int = 5) -> Dict[str, Any]:
    if not LEANN_INDEX_PATH.exists():
        sync_context()
    index = LEANNIndex(LEANN_INDEX_PATH)
    return {
        "query": query,
        "limit": limit,
        "results": index.search(query=query, limit=limit),
    }
