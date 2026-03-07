from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

CORE_ROOT = Path(__file__).resolve().parents[1]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from tools.orchestrator import fullstack


class FullstackIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Prompt templates expected by config.
        prompt_dir = self.root / ".timely-core" / "tools" / "orchestrator" / "fullstack_prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        (prompt_dir / "01_architecture.md").write_text(
            "Phase {phase_title}\nProject {project_id}\n{brief_text}\n",
            encoding="utf-8",
        )

        # Minimal coupled template source.
        template_root = self.root / ".timely-playbook" / "local" / ".orchestrator" / "upstream" / "demo-repo" / "template"
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
                    "local_path": ".timely-playbook/local/.orchestrator/upstream/demo-repo",
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
                    "prompt_template": ".timely-core/tools/orchestrator/fullstack_prompts/01_architecture.md",
                    "validation_commands": ["test -f README.md"],
                }
            ],
        }

        defaults_path = self.root / ".timely-core" / "tools" / "orchestrator" / "fullstack_defaults.json"
        defaults_path.parent.mkdir(parents=True, exist_ok=True)
        defaults_path.write_text(json.dumps(defaults_payload, indent=2) + "\n", encoding="utf-8")

        self.patches = [
            patch.object(fullstack, "ROOT", self.root),
            patch.object(fullstack, "DEFAULTS_PATH", defaults_path),
            patch.object(fullstack, "CONFIG_PATH", self.root / ".timely-playbook" / "local" / ".orchestrator" / "fullstack-agent.json"),
            patch.object(fullstack, "validate_core_manifest", lambda *_args, **_kwargs: None),
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

        manifest_payload = json.loads(manifest_file.read_text(encoding="utf-8"))
        self.assertEqual(manifest_payload["default_provider"], "codex")

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
        self.assertEqual(run_result["provider"], "codex")
        command = run_result["command"]
        self.assertEqual(command[0], "codex")
        self.assertIn("custom-model", command)

        prompt_file = self.root / run_result["prompt_file"]
        self.assertTrue(prompt_file.exists())
        prompt_text = prompt_file.read_text(encoding="utf-8")
        self.assertIn("Build a project planner", prompt_text)
        self.assertIn("Architecture", prompt_text)

    def test_dry_run_supports_custom_provider_override(self) -> None:
        fullstack.ensure_config()
        config_path = self.root / ".timely-playbook" / "local" / ".orchestrator" / "fullstack-agent.json"
        config_payload = json.loads(config_path.read_text(encoding="utf-8"))
        config_payload["providers"] = {
            "demo-agent": {
                "label": "Demo Agent",
                "stdin_prompt": False,
                "exec_command": [
                    "demo-agent",
                    "run",
                    "--cwd",
                    "{workdir}",
                    "--artifact",
                    "{run_dir}/agent-last-message.txt",
                    "{model_args}",
                ],
                "model_arg": ["--model", "{model}"],
            }
        }
        config_path.write_text(json.dumps(config_payload, indent=2) + "\n", encoding="utf-8")

        fullstack.bootstrap_project(
            project_id="demo",
            brief="Build a project planner",
            template_id="demo-template",
        )
        fullstack.plan_project("demo", register_state=False)

        run_result = fullstack.run_phase(
            project_id="demo",
            phase_id="architecture",
            model="alt-model",
            provider="demo-agent",
            dry_run=True,
        )

        self.assertEqual(run_result["status"], "dry_run")
        self.assertEqual(run_result["provider"], "demo-agent")
        command = run_result["command"]
        self.assertEqual(command[0], "demo-agent")
        self.assertIn("--cwd", command)
        self.assertIn("alt-model", command)
        self.assertNotIn("-", command)

    def test_custom_provider_run_uses_agent_logs_and_skips_stdin(self) -> None:
        fullstack.ensure_config()
        config_path = self.root / ".timely-playbook" / "local" / ".orchestrator" / "fullstack-agent.json"
        config_payload = json.loads(config_path.read_text(encoding="utf-8"))
        config_payload["providers"] = {
            "demo-agent": {
                "label": "Demo Agent",
                "stdin_prompt": False,
                "exec_command": [
                    "demo-agent",
                    "run",
                    "--cwd",
                    "{workdir}",
                    "--artifact",
                    "{run_dir}/agent-last-message.txt",
                    "{model_args}",
                ],
                "model_arg": ["--model", "{model}"],
            }
        }
        config_path.write_text(json.dumps(config_payload, indent=2) + "\n", encoding="utf-8")

        fullstack.bootstrap_project(
            project_id="demo",
            brief="Build a project planner",
            template_id="demo-template",
        )
        fullstack.plan_project("demo", register_state=False)

        calls: list[dict[str, object]] = []

        def fake_run(cmd, cwd=None, input_text=None):
            calls.append({"cmd": cmd, "cwd": cwd, "input_text": input_text})
            if cmd[0] == "demo-agent":
                return subprocess.CompletedProcess(
                    args=cmd,
                    returncode=0,
                    stdout="agent ok",
                    stderr="",
                )
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        with patch.object(fullstack, "_run_command", side_effect=fake_run):
            run_result = fullstack.run_phase(
                project_id="demo",
                phase_id="architecture",
                model="alt-model",
                provider="demo-agent",
            )

        self.assertEqual(run_result["status"], "ok")
        self.assertEqual(run_result["provider"], "demo-agent")
        provider_call = next(entry for entry in calls if entry["cmd"][0] == "demo-agent")
        self.assertIsNone(provider_call["input_text"])

        run_dir = self.root / run_result["run_dir"]
        self.assertTrue((run_dir / "agent-stdout.log").exists())
        self.assertTrue((run_dir / "agent-stderr.log").exists())
        self.assertFalse((run_dir / "codex-stdout.log").exists())
        self.assertFalse((run_dir / "codex-stderr.log").exists())
        status = fullstack.project_status("demo")
        self.assertEqual(status["phase_counts"]["done"], 1)

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
