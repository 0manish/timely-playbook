from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.orchestrator import fullstack


class FullstackIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Prompt templates expected by config.
        prompt_dir = self.root / "tools" / "orchestrator" / "fullstack_prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        (prompt_dir / "01_architecture.md").write_text(
            "Phase {phase_title}\nProject {project_id}\n{brief_text}\n",
            encoding="utf-8",
        )

        # Minimal coupled template source.
        template_root = self.root / "vendor" / "demo-repo" / "template"
        template_root.mkdir(parents=True, exist_ok=True)
        (template_root / "README.md").write_text("# Demo\n", encoding="utf-8")
        (template_root / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")

        # Defaults payload used to generate .orchestrator/fullstack-agent.json.
        defaults_payload = {
            "schema_version": 1,
            "paper": {
                "arxiv_id": "2602.03798",
                "title": "FullStack-Agent",
                "url": "https://arxiv.org/abs/2602.03798",
            },
            "default_model": "test-model",
            "projects_dir": "projects",
            "upstreams": [
                {
                    "id": "demo-repo",
                    "url": "https://example.invalid/repo.git",
                    "ref": "deadbeef",
                    "local_path": "vendor/demo-repo",
                }
            ],
            "templates": {
                "demo-template": {
                    "mode": "coupled",
                    "repo": "demo-repo",
                    "path": "template",
                }
            },
            "phases": [
                {
                    "id": "architecture",
                    "title": "Architecture",
                    "prompt_template": "tools/orchestrator/fullstack_prompts/01_architecture.md",
                    "validation_commands": ["test -f README.md"],
                }
            ],
        }

        defaults_path = self.root / "tools" / "orchestrator" / "fullstack_defaults.json"
        defaults_path.parent.mkdir(parents=True, exist_ok=True)
        defaults_path.write_text(json.dumps(defaults_payload, indent=2) + "\n", encoding="utf-8")

        self.patches = [
            patch.object(fullstack, "ROOT", self.root),
            patch.object(fullstack, "DEFAULTS_PATH", defaults_path),
            patch.object(fullstack, "CONFIG_PATH", self.root / ".orchestrator" / "fullstack-agent.json"),
        ]
        for patcher in self.patches:
            patcher.start()

    def tearDown(self) -> None:
        for patcher in reversed(self.patches):
            patcher.stop()
        self.temp_dir.cleanup()

    def test_ensure_config_writes_config_file(self) -> None:
        config_path = fullstack.ensure_config()
        self.assertTrue(config_path.exists())
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["default_model"], "test-model")

    def test_bootstrap_creates_manifest_and_plan(self) -> None:
        fullstack.ensure_config()
        result = fullstack.bootstrap_project(
            project_id="demo",
            brief="Build a project planner",
            template_id="demo-template",
        )

        self.assertEqual(result["status"], "ok")

        plan_file = self.root / result["plan"]
        manifest_file = self.root / result["manifest"]
        self.assertTrue(plan_file.exists())
        self.assertTrue(manifest_file.exists())

        plan_payload = json.loads(plan_file.read_text(encoding="utf-8"))
        self.assertEqual(plan_payload["phases"][0]["status"], "pending")

        app_readme = self.root / result["project_root"] / "app" / "README.md"
        self.assertTrue(app_readme.exists())

    def test_plan_and_dry_run_phase(self) -> None:
        fullstack.ensure_config()
        fullstack.bootstrap_project(
            project_id="demo",
            brief="Build a project planner",
            template_id="demo-template",
        )

        plan_result = fullstack.plan_project("demo", register_state=False)
        self.assertEqual(plan_result["phases"][0]["status"], "ready")

        run_result = fullstack.run_phase(
            project_id="demo",
            phase_id="architecture",
            model="custom-model",
            dry_run=True,
        )

        self.assertEqual(run_result["status"], "dry_run")
        command = run_result["command"]
        self.assertIn("custom-model", command)

        prompt_file = self.root / run_result["prompt_file"]
        self.assertTrue(prompt_file.exists())
        prompt_text = prompt_file.read_text(encoding="utf-8")
        self.assertIn("Build a project planner", prompt_text)
        self.assertIn("Architecture", prompt_text)

    def test_run_all_phases_executes_ready_phase(self) -> None:
        fullstack.ensure_config()
        fullstack.bootstrap_project(
            project_id="demo",
            brief="Build a project planner",
            template_id="demo-template",
        )
        fullstack.plan_project("demo", register_state=False)

        def fake_run(cmd, cwd=None, input_text=None):
            del cwd, input_text
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="ok", stderr="")

        with patch.object(fullstack, "_run_command", side_effect=fake_run):
            run_all_result = fullstack.run_all_phases(project_id="demo")

        self.assertEqual(run_all_result["status"], "ok")
        self.assertEqual(len(run_all_result["phase_results"]), 1)
        self.assertEqual(run_all_result["phase_results"][0]["phase"], "architecture")

        status = fullstack.project_status("demo")
        self.assertEqual(status["phase_counts"]["done"], 1)


if __name__ == "__main__":
    unittest.main()
