from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

CORE_ROOT = Path(__file__).resolve().parents[1]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from tools.orchestrator.helpers import agent_tools


class AgentToolTests(unittest.TestCase):
    def test_agent_edit_uses_builtin_codex_provider(self) -> None:
        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="edited",
                stderr="",
            )
            result = agent_tools.agent_edit("fix it", ["README.md", "AGENTS.md"])

        self.assertEqual(result, "edited")
        mock_run.assert_called_once()
        args = mock_run.call_args.args[0]
        self.assertEqual(
            args,
            ["codex", "apply", "--prompt", "fix it", "README.md", "AGENTS.md"],
        )
        self.assertTrue(mock_run.call_args.kwargs["check"])
        self.assertEqual(mock_run.call_args.kwargs["cwd"], str(agent_tools.ROOT))

    def test_agent_chat_uses_builtin_codex_provider(self) -> None:
        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="reply",
                stderr="",
            )
            result = agent_tools.agent_chat([{"role": "user", "content": "hello"}])

        self.assertEqual(result, "reply")
        mock_run.assert_called_once()
        self.assertEqual(mock_run.call_args.args[0], ["codex", "chat", "--stdin"])
        self.assertEqual(
            mock_run.call_args.kwargs["input"],
            json.dumps({"messages": [{"role": "user", "content": "hello"}]}),
        )

    def test_agent_edit_accepts_custom_provider_config(self) -> None:
        provider_config = {
            "edit_command": ["other-agent", "edit", "--prompt", "{prompt}", "{files}"],
        }

        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="ok",
                stderr="",
            )
            result = agent_tools.agent_edit(
                "apply change",
                ["a.txt", "b.txt"],
                provider="other-agent",
                provider_config=provider_config,
            )

        self.assertEqual(result, "ok")
        self.assertEqual(
            mock_run.call_args.args[0],
            ["other-agent", "edit", "--prompt", "apply change", "a.txt", "b.txt"],
        )


if __name__ == "__main__":
    unittest.main()
