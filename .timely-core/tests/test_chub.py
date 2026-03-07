from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

CORE_ROOT = Path(__file__).resolve().parents[1]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from tools.chub import timely_registry


class TimelyRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        files = {
            ".timely-core/TimelyPlaybook.md": "# Timely Playbook\n\n> Main operating guide.\n",
            ".timely-core/DFD.md": "# DFD\n\n```mermaid\nflowchart TD\n```\n",
            ".timely-playbook/local/AGENTS.md": "# Local guardrails\n",
            ".timely-playbook/local/SKILLS.md": "# Local skills\n",
            ".timely-playbook/local/timely-trackers/test-run-journal.md": "# Test Run Journal\n\n> Journal guidance.\n",
            ".timely-core/templates/todo-backlog.md": "# TODO / OKR Backlog Template\n\n> Template guidance.\n",
            ".timely-core/snippets/release-readiness-shared.md": "# Shared snippet\n\nShared snippet details.\n",
            ".timely-playbook/local/.orchestrator/STATUS.md": "# Status\n\nCurrent status snapshot.\n",
            ".timely-core/tools/orchestrator/fullstack_prompts/01_architecture.md": "# Architecture\n\nDesign the system.\n",
            ".timely-playbook/runtime/package.json": '{\n  "dependencies": {\n    "@aisuite/chub": "0.1.1"\n  }\n}\n',
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

        self.assertEqual(summary["docs"], 9)
        self.assertTrue((self.root / ".chub" / "timely-mirror-metadata.json").exists())

        registry_path = self.root / ".chub" / "timely-source" / "timely-playbook" / "registry.json"
        self.assertTrue(registry_path.exists())
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        ids = {doc["id"] for doc in payload["docs"]}

        self.assertIn("timely-playbook/timely-playbook", ids)
        self.assertIn("timely-playbook/agents", ids)
        self.assertIn("timely-playbook/skills", ids)
        self.assertIn("timely-playbook/tracker-test-run-journal", ids)
        self.assertIn("timely-playbook/template-todo-backlog", ids)
        self.assertIn("timely-playbook/snippet-release-readiness-shared", ids)
        self.assertIn("timely-playbook/status", ids)
        self.assertIn("timely-playbook/prompt-architecture", ids)

        copied_doc = self.root / ".chub" / "timely-source" / "timely-playbook" / "docs" / "timely-playbook" / "DOC.md"
        self.assertEqual(
            copied_doc.read_text(encoding="utf-8"),
            (self.root / ".timely-core" / "TimelyPlaybook.md").read_text(encoding="utf-8"),
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

        metadata_path = self.root / ".chub" / "timely-mirror-metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.assertEqual(metadata["schema_version"], 1)
        self.assertEqual(metadata["author"], "timely-playbook")
        self.assertEqual(metadata["chub_dependency_version"], "0.1.1")
        self.assertEqual(metadata["docs"], 9)
        self.assertEqual(metadata["registry_path"], registry_path.resolve().as_posix())
        self.assertIn("timely-playbook/timely-playbook", metadata["entry_ids"])
        self.assertIn("TimelyPlaybook.md", metadata["tracked_paths"])

    def test_last_updated_for_uses_relocated_paths_when_git_metadata_is_missing(self) -> None:
        core_doc = self.root / ".timely-core" / "TimelyPlaybook.md"
        agents_doc = self.root / ".timely-playbook" / "local" / "AGENTS.md"
        skills_doc = self.root / ".timely-playbook" / "local" / "SKILLS.md"
        tracker_doc = self.root / ".timely-playbook" / "local" / "timely-trackers" / "test-run-journal.md"
        architecture_prompt = self.root / ".timely-core" / "tools" / "orchestrator" / "fullstack_prompts" / "01_architecture.md"

        os.utime(core_doc, (1_710_000_000, 1_710_000_000))
        os.utime(agents_doc, (1_712_000_000, 1_712_000_000))
        os.utime(skills_doc, (1_713_000_000, 1_713_000_000))
        os.utime(tracker_doc, (1_715_000_000, 1_715_000_000))
        os.utime(architecture_prompt, (1_720_000_000, 1_720_000_000))

        with patch.object(timely_registry, "git_last_updated", return_value=None):
            self.assertEqual(
                timely_registry.last_updated_for(self.root, Path("TimelyPlaybook.md")),
                "2024-03-09",
            )
            self.assertEqual(
                timely_registry.last_updated_for(self.root, Path("AGENTS.md")),
                "2024-04-01",
            )
            self.assertEqual(
                timely_registry.last_updated_for(self.root, Path("SKILLS.md")),
                "2024-04-13",
            )
            self.assertEqual(
                timely_registry.last_updated_for(self.root, Path("timely-trackers/test-run-journal.md")),
                "2024-05-06",
            )
            self.assertEqual(
                timely_registry.last_updated_for(
                    self.root,
                    Path("tools/orchestrator/fullstack_prompts/01_architecture.md"),
                ),
                "2024-07-03",
            )


if __name__ == "__main__":
    unittest.main()
