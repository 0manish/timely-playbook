from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.chub import timely_registry


class TimelyRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        files = {
            "TimelyPlaybook.md": "# Timely Playbook\n\n> Main operating guide.\n",
            "DFD.md": "# DFD\n\n```mermaid\nflowchart TD\n```\n",
            "timely-trackers/test-run-journal.md": "# Test Run Journal\n\n> Journal guidance.\n",
            "templates/todo-backlog.md": "# TODO / OKR Backlog Template\n\n> Template guidance.\n",
            "snippets/release-readiness-shared.md": "# Shared snippet\n\nShared snippet details.\n",
            ".orchestrator/STATUS.md": "# Status\n\nCurrent status snapshot.\n",
            "tools/orchestrator/fullstack_prompts/01_architecture.md": "# Architecture\n\nDesign the system.\n",
            "dist/ignored.md": "# Ignored\n",
            "run-logs/20260307/summary.md": "# Run log\n",
        }

        for relative, content in files.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        self.overrides = self.root / "overrides.json"
        self.overrides.write_text(
            json.dumps(
                {
                    "DFD.md": {
                        "description": "Mermaid data flow diagram.",
                        "tags": ["diagram", "data-flow"],
                    }
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_prepare_repo_local_chub_writes_registry_and_copies_docs(self) -> None:
        summary = timely_registry.prepare_repo_local_chub(
            repo_root=self.root,
            chub_dir=self.root / ".chub",
            overrides_path=self.overrides,
        )

        self.assertEqual(summary["docs"], 7)

        registry_path = self.root / ".chub" / "timely-source" / "timely-playbook" / "registry.json"
        self.assertTrue(registry_path.exists())
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        ids = {doc["id"] for doc in payload["docs"]}

        self.assertIn("timely-playbook/timely-playbook", ids)
        self.assertIn("timely-playbook/tracker-test-run-journal", ids)
        self.assertIn("timely-playbook/template-todo-backlog", ids)
        self.assertIn("timely-playbook/snippet-release-readiness-shared", ids)
        self.assertIn("timely-playbook/status", ids)
        self.assertIn("timely-playbook/prompt-architecture", ids)

        copied_doc = self.root / ".chub" / "timely-source" / "timely-playbook" / "docs" / "timely-playbook" / "DOC.md"
        self.assertEqual(
            copied_doc.read_text(encoding="utf-8"),
            (self.root / "TimelyPlaybook.md").read_text(encoding="utf-8"),
        )
        self.assertFalse((self.root / ".chub" / "timely-source" / "timely-playbook" / "docs" / "ignored").exists())

    def test_prepare_repo_local_chub_applies_overrides_and_writes_config(self) -> None:
        timely_registry.prepare_repo_local_chub(
            repo_root=self.root,
            chub_dir=self.root / ".chub",
            overrides_path=self.overrides,
        )

        registry_path = self.root / ".chub" / "timely-source" / "timely-playbook" / "registry.json"
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        docs = {doc["id"]: doc for doc in payload["docs"]}

        dfd = docs["timely-playbook/dfd"]
        self.assertEqual(dfd["description"], "Mermaid data flow diagram.")
        self.assertIn("diagram", dfd["tags"])
        self.assertIn("data-flow", dfd["tags"])
        self.assertEqual(dfd["languages"][0]["language"], "markdown")
        self.assertEqual(dfd["languages"][0]["versions"][0]["version"], "current")

        config_path = self.root / ".chub" / "config.yaml"
        config_text = config_path.read_text(encoding="utf-8")
        self.assertIn("url: https://cdn.aichub.org/v1", config_text)
        self.assertIn("telemetry: true", config_text)
        self.assertIn((self.root / ".chub" / "timely-dist").resolve().as_posix(), config_text)


if __name__ == "__main__":
    unittest.main()
