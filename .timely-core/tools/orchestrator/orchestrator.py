"""Entry point that coordinates planner, implementers, and CI bridge."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from tools.workspace import resolve_workspace, validate_core_manifest

WORKSPACE = resolve_workspace(Path(__file__).resolve())
REPO_ROOT = WORKSPACE.core_dir
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from tools.orchestrator.agents.base import AgentContext
from tools.orchestrator.agents.planner import PlannerAgent
from tools.orchestrator.agents.implementer import ImplementerAgent
from tools.orchestrator.agents.tester import TesterAgent
from tools.orchestrator.agents.reviewer import ReviewerAgent
from tools.orchestrator.agents.devops import DevOpsAgent
from tools.orchestrator.state import STATE_PATH, State, search_context, sync_context
from tools.orchestrator.helpers import ci_tools
from tools.orchestrator import fullstack

ROOT = WORKSPACE.root
OWNERSHIP = WORKSPACE.ownership_path


def plan(goal: str, ready_tasks: List[str]) -> None:
    ctx = AgentContext(str(ROOT), str(OWNERSHIP), str(STATE_PATH))
    agent = PlannerAgent(ctx)
    result = agent.run(goal=goal, ready_tasks=ready_tasks)
    print(json.dumps(result, indent=2))


def start_ready(owner: str) -> None:
    ctx = AgentContext(str(ROOT), str(OWNERSHIP), str(STATE_PATH))
    implementer = ImplementerAgent(ctx, owner)
    state = State.load()
    ready = [task.task_id for task in state.tasks if task.status == "ready"]
    if not ready:
        print("No ready tasks. Run plan first.")
        return
    for task_id in ready:
        result = implementer.run(task_id)
        print(json.dumps(result))


def record_ci(repo: str, workflow: str) -> None:
    run = ci_tools.fetch_latest_run(repo=repo, workflow=workflow)
    summary = ci_tools.summarize_run(run)
    ctx = AgentContext(str(ROOT), str(OWNERSHIP), str(STATE_PATH))
    tester = TesterAgent(ctx)
    tester.run(workflow_url=run.get("html_url", "")) if run else tester.run("N/A")
    print(summary)


def update_status() -> None:
    state = State.load()
    state.update_status_file()
    print("STATUS.md refreshed")


def context_sync() -> None:
    print(json.dumps(sync_context(), indent=2))


def context_search(query: str, limit: int) -> None:
    print(json.dumps(search_context(query=query, limit=limit), indent=2))


def review(task_id: str, verdict: str) -> None:
    ctx = AgentContext(str(ROOT), str(OWNERSHIP), str(STATE_PATH))
    reviewer = ReviewerAgent(ctx)
    result = reviewer.run(task_id=task_id, verdict=verdict)
    print(json.dumps(result))


def deploy(environment: str, result_value: str) -> None:
    ctx = AgentContext(str(ROOT), str(OWNERSHIP), str(STATE_PATH))
    devops = DevOpsAgent(ctx)
    result = devops.run(environment=environment, result=result_value)
    print(json.dumps(result))


def fullstack_init_config(force: bool) -> None:
    path = fullstack.ensure_config(force=force)
    print(json.dumps({"status": "ok", "config_path": str(path)}))


def fullstack_sync(update: bool) -> None:
    print(json.dumps(fullstack.sync_upstreams(update=update), indent=2))


def fullstack_bootstrap(
    project_id: str,
    brief: str | None,
    brief_file: str | None,
    template: str,
    allow_existing: bool,
) -> None:
    if brief_file:
        brief = Path(brief_file).read_text(encoding="utf-8")
    if not brief:
        raise ValueError("Provide --brief or --brief-file")
    result = fullstack.bootstrap_project(
        project_id=project_id,
        brief=brief,
        template_id=template,
        allow_existing=allow_existing,
    )
    print(json.dumps(result, indent=2))


def fullstack_plan(project_id: str, no_state: bool) -> None:
    result = fullstack.plan_project(project_id=project_id, register_state=not no_state)
    print(json.dumps(result, indent=2))


def fullstack_run(
    project_id: str,
    phase_id: str,
    model: str | None,
    provider: str | None,
    dry_run: bool,
    skill: str | None,
) -> None:
    result = fullstack.run_phase(
        project_id=project_id,
        phase_id=phase_id,
        model=model,
        provider=provider,
        dry_run=dry_run,
        skill=skill,
    )
    print(json.dumps(result, indent=2))


def fullstack_run_all(
    project_id: str,
    model: str | None,
    provider: str | None,
    continue_on_failure: bool,
    skill: str | None,
) -> None:
    result = fullstack.run_all_phases(
        project_id=project_id,
        model=model,
        provider=provider,
        continue_on_failure=continue_on_failure,
        skill=skill,
    )
    print(json.dumps(result, indent=2))


def fullstack_status(project_id: str) -> None:
    print(json.dumps(fullstack.project_status(project_id=project_id), indent=2))


def main() -> None:
    validate_core_manifest(WORKSPACE)
    parser = argparse.ArgumentParser(description="Multi-agent conductor helper")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_cmd = sub.add_parser("plan", help="Refresh goals and planning metadata")
    plan_cmd.add_argument("goal", help="Active program goal")
    plan_cmd.add_argument("--ready", nargs="*", default=[], help="Tasks pre-marked ready")

    ready_cmd = sub.add_parser("start-ready", help="Kick off implementers for ready tasks")
    ready_cmd.add_argument("owner", help="Implementer persona identifier")

    ci_cmd = sub.add_parser("record-ci", help="Record the latest CI run")
    ci_cmd.add_argument("repo", help="GitHub repo, e.g. org/project")
    ci_cmd.add_argument("workflow", help="Workflow file name, e.g. ci.yml")

    sub.add_parser("update-status", help="Regenerate STATUS.md from the CXDB-backed state")
    sub.add_parser("context-sync", help="Sync project-local CXDB and LEANN state")

    context_search_cmd = sub.add_parser("context-search", help="Search the local LEANN context index")
    context_search_cmd.add_argument("query")
    context_search_cmd.add_argument("--limit", type=int, default=5, help="Maximum number of results")

    review_cmd = sub.add_parser("review", help="Record reviewer verdict for a task")
    review_cmd.add_argument("task_id")
    review_cmd.add_argument("verdict", choices=["review", "approved", "changes_requested"])

    deploy_cmd = sub.add_parser("deploy", help="Record deployment outcome")
    deploy_cmd.add_argument("environment")
    deploy_cmd.add_argument("result", choices=["succeeded", "failed", "rolled_back"])

    fs_init_cmd = sub.add_parser("fullstack-init-config", help="Write fullstack integration config")
    fs_init_cmd.add_argument("--force", action="store_true", help="Overwrite existing config file")

    fs_sync_cmd = sub.add_parser("fullstack-sync", help="Clone/update pinned FullStack-Agent upstream repos")
    fs_sync_cmd.add_argument("--update", action="store_true", help="Fetch latest remote refs before checkout")

    fs_bootstrap_cmd = sub.add_parser("fullstack-bootstrap", help="Create a new reusable fullstack project workspace")
    fs_bootstrap_cmd.add_argument("project_id", help="Project identifier")
    fs_bootstrap_cmd.add_argument("--brief", default=None, help="Short project brief text")
    fs_bootstrap_cmd.add_argument("--brief-file", default=None, help="Path to Markdown/TXT brief")
    fs_bootstrap_cmd.add_argument("--template", default="nextjs-nestjs-postresql", help="Template key from fullstack-agent.json")
    fs_bootstrap_cmd.add_argument("--allow-existing", action="store_true", help="Allow writing into an existing project directory")

    fs_plan_cmd = sub.add_parser("fullstack-plan", help="Prepare phase plan and sync CXDB-backed tasks")
    fs_plan_cmd.add_argument("project_id")
    fs_plan_cmd.add_argument("--no-state", action="store_true", help="Do not sync orchestrator state tasks")

    fs_run_cmd = sub.add_parser(
        "fullstack-run",
        help="Run one fullstack phase through the configured agent provider",
    )
    fs_run_cmd.add_argument("project_id")
    fs_run_cmd.add_argument("phase_id", help="Phase id from the project plan")
    fs_run_cmd.add_argument("--model", default=None, help="Override model for this phase run")
    fs_run_cmd.add_argument("--provider", default=None, help="Override agent provider for this phase run")
    fs_run_cmd.add_argument("--dry-run", action="store_true", help="Render prompt and print command only")
    fs_run_cmd.add_argument("--skill", default=None, help="Optional SKILLS.md overlay name")

    fs_run_all_cmd = sub.add_parser("fullstack-run-all", help="Run all ready phases in sequence")
    fs_run_all_cmd.add_argument("project_id")
    fs_run_all_cmd.add_argument("--model", default=None, help="Override model for all phase runs")
    fs_run_all_cmd.add_argument("--provider", default=None, help="Override agent provider for all phase runs")
    fs_run_all_cmd.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="Continue to subsequent phases when one phase fails",
    )
    fs_run_all_cmd.add_argument("--skill", default=None, help="Optional SKILLS.md overlay name")

    fs_status_cmd = sub.add_parser("fullstack-status", help="Show fullstack project status summary")
    fs_status_cmd.add_argument("project_id")

    args = parser.parse_args()

    if args.command == "plan":
        plan(goal=args.goal, ready_tasks=args.ready)
    elif args.command == "start-ready":
        start_ready(owner=args.owner)
    elif args.command == "record-ci":
        record_ci(repo=args.repo, workflow=args.workflow)
    elif args.command == "update-status":
        update_status()
    elif args.command == "context-sync":
        context_sync()
    elif args.command == "context-search":
        context_search(query=args.query, limit=args.limit)
    elif args.command == "review":
        review(task_id=args.task_id, verdict=args.verdict)
    elif args.command == "deploy":
        deploy(environment=args.environment, result_value=args.result)
    elif args.command == "fullstack-init-config":
        fullstack_init_config(force=args.force)
    elif args.command == "fullstack-sync":
        fullstack_sync(update=args.update)
    elif args.command == "fullstack-bootstrap":
        fullstack_bootstrap(
            project_id=args.project_id,
            brief=args.brief,
            brief_file=args.brief_file,
            template=args.template,
            allow_existing=args.allow_existing,
        )
    elif args.command == "fullstack-plan":
        fullstack_plan(project_id=args.project_id, no_state=args.no_state)
    elif args.command == "fullstack-run":
        fullstack_run(
            project_id=args.project_id,
            phase_id=args.phase_id,
            model=args.model,
            provider=args.provider,
            dry_run=args.dry_run,
            skill=args.skill,
        )
    elif args.command == "fullstack-run-all":
        fullstack_run_all(
            project_id=args.project_id,
            model=args.model,
            provider=args.provider,
            continue_on_failure=args.continue_on_failure,
            skill=args.skill,
        )
    elif args.command == "fullstack-status":
        fullstack_status(project_id=args.project_id)


if __name__ == "__main__":
    main()
