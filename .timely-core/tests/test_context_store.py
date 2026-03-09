from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

CORE_ROOT = Path(__file__).resolve().parents[1]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from tools.orchestrator import state as orchestrator_state
from tools.workspace import resolve_workspace


class ContextStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        (self.root / ".timely-core").mkdir(parents=True, exist_ok=True)
        local_dir = self.root / ".timely-playbook" / "local"
        (local_dir / ".orchestrator").mkdir(parents=True, exist_ok=True)
        (local_dir / "timely-trackers").mkdir(parents=True, exist_ok=True)

        (local_dir / "AGENTS.md").write_text("# Guardrails\n\nReview deploy approvals.\n", encoding="utf-8")
        (local_dir / "SKILLS.md").write_text("# Skills\n\nPlanner and reviewer overlays.\n", encoding="utf-8")
        (local_dir / ".orchestrator" / "ownership.yaml").write_text("areas:\n  docs:\n    owners:\n      - docs-agent\n", encoding="utf-8")
        (local_dir / "timely-trackers" / "test-run-journal.md").write_text("# Journal\n\nDeployment checks recorded here.\n", encoding="utf-8")

        state_payload = {
            "goal": "Ship a staged deployment plan",
            "plan": {
                "summary": "Finalize deployment readiness",
                "notes": ["Verify smoke coverage", "Record approvals"],
            },
            "tasks": [
                {
                    "id": "DEPLOY-001",
                    "title": "Prepare staging deployment",
                    "owner": "devops",
                    "status": "ready",
                    "deps": [],
                    "artifacts": ["deploy/staging.md"],
                }
            ],
            "ci_runs": [
                {
                    "id": "CI-1",
                    "workflow": "ci.yml",
                    "status": "passed",
                    "summary": "smoke ok",
                    "url": "local://ci/1",
                }
            ],
            "decisions": [
                {
                    "id": "DEC-1",
                    "topic": "Use staged deployment",
                    "context": "Reduces rollout risk",
                    "status": "accepted",
                    "timestamp": "2026-03-08T00:00:00Z",
                }
            ],
        }
        (local_dir / ".orchestrator" / "state.json").write_text(
            json.dumps(state_payload, indent=2) + "\n",
            encoding="utf-8",
        )

        workspace = resolve_workspace(repo_root=self.root)
        self.patches = [
            patch.object(orchestrator_state, "WORKSPACE", workspace),
            patch.object(orchestrator_state, "ROOT", workspace.root),
            patch.object(orchestrator_state, "STATE_PATH", workspace.state_path),
            patch.object(orchestrator_state, "STATUS_PATH", workspace.status_path),
            patch.object(orchestrator_state, "CXDB_PATH", workspace.cxdb_path),
            patch.object(orchestrator_state, "LEANN_INDEX_PATH", workspace.leann_index_path),
        ]
        for patcher in self.patches:
            patcher.start()

    def tearDown(self) -> None:
        for patcher in reversed(self.patches):
            patcher.stop()
        self.temp_dir.cleanup()

    def test_state_load_migrates_export_into_cxdb_and_builds_leann(self) -> None:
        state = orchestrator_state.State.load()
        state.update_status_file()

        self.assertEqual(state.goal, "Ship a staged deployment plan")
        self.assertTrue((self.root / ".timely-playbook" / "local" / ".cxdb" / "cxdb.sqlite3").exists())
        self.assertTrue((self.root / ".timely-playbook" / "local" / ".leann" / "index.json").exists())
        self.assertTrue((self.root / ".timely-playbook" / "local" / ".orchestrator" / "STATUS.md").exists())

        search_result = orchestrator_state.search_context("staging deployment", limit=3)
        ids = [entry["id"] for entry in search_result["results"]]
        self.assertIn("task/DEPLOY-001", ids)

    def test_sync_context_indexes_workspace_files(self) -> None:
        summary = orchestrator_state.sync_context()
        self.assertEqual(summary["cxdb_path"], ".timely-playbook/local/.cxdb/cxdb.sqlite3")
        self.assertEqual(summary["leann_index_path"], ".timely-playbook/local/.leann/index.json")

        search_result = orchestrator_state.search_context("deploy approvals", limit=5)
        ids = [entry["id"] for entry in search_result["results"]]
        self.assertIn("file/.timely-playbook/local/AGENTS.md", ids)


if __name__ == "__main__":
    unittest.main()
