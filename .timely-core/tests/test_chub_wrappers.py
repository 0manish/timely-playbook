from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

CORE_ROOT = Path(__file__).resolve().parents[1]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from tools.chub import timely_registry


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        del exc_type, exc, tb
        return False

    def read(self) -> bytes:
        return self.payload


class ChubWrapperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.repo_root = Path(__file__).resolve().parents[2]
        self.log_dir = self.root / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._copy_repo_file(".timely-core/tools/__init__.py")
        self._copy_repo_file(".timely-core/tools/workspace.py")
        self._copy_repo_file(".timely-core/tools/chub/__init__.py")
        self._copy_repo_file(".timely-core/scripts/chub.sh")
        self._copy_repo_file(".timely-core/scripts/chub-mcp.sh")
        self._copy_repo_file(".timely-core/tools/chub/timely_registry.py")
        self._copy_repo_file(".timely-core/tools/chub/metadata_overrides.json")

        self._write_file(
            ".timely-core/TimelyPlaybook.md",
            "# Timely Playbook\n\n> Main operating guide.\n",
        )
        self._write_file(
            ".timely-playbook/runtime/node_modules/.bin/chub",
            """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "${FAKE_LOG_DIR}/chub-args.log"
printf '%s\\n' "${CHUB_DIR:-}" >> "${FAKE_LOG_DIR}/chub-env.log"
cmd="${1:-}"
if [[ "${cmd}" == "build" ]]; then
  output=""
  prev=""
  for arg in "$@"; do
    if [[ "${prev}" == "-o" ]]; then
      output="${arg}"
      break
    fi
    prev="${arg}"
  done
  if [[ -n "${output}" ]]; then
    mkdir -p "${output}"
    printf 'built\\n' > "${output}/.built"
  fi
  exit 0
fi
if [[ "${cmd}" == "--help" ]]; then
  printf 'fake chub help\\n'
  exit 0
fi
printf 'ok\\n'
""",
            executable=True,
        )
        self._write_file(
            ".timely-playbook/runtime/node_modules/.bin/chub-mcp",
            """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "${FAKE_LOG_DIR}/chub-mcp-args.log"
printf '%s\\n' "${CHUB_DIR:-}" >> "${FAKE_LOG_DIR}/chub-mcp-env.log"
printf 'mcp ok\\n'
""",
            executable=True,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _copy_repo_file(self, relative_path: str) -> None:
        source = self.repo_root / relative_path
        target = self.root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        target.chmod(0o755 if target.suffix == ".sh" else 0o644)

    def _write_file(self, relative_path: str, content: str, executable: bool = False) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755 if executable else 0o644)

    def _seed_cached_search_index(self, chub_home: Path) -> None:
        path = chub_home / "sources" / "community" / "search-index.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")

    def _run_script(
        self,
        script: str,
        *args: str,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        merged_env = {
            **os.environ,
            "FAKE_LOG_DIR": str(self.log_dir),
        }
        if env:
            merged_env.update(env)
        return subprocess.run(
            ["bash", str(self.root / script), *args],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
            env=merged_env,
        )

    def test_chub_build_uses_custom_chub_dir_and_builds_local_dist(self) -> None:
        chub_home = self.root / "custom-chub"
        self._seed_cached_search_index(chub_home)

        self._run_script(
            ".timely-core/scripts/chub.sh",
            "build",
            "--validate-only",
            env={"CHUB_DIR": str(chub_home)},
        )

        registry_path = chub_home / "timely-source" / "timely-playbook" / "registry.json"
        dist_marker = chub_home / "timely-dist" / ".built"
        args_log = (self.log_dir / "chub-args.log").read_text(encoding="utf-8").splitlines()
        env_log = (self.log_dir / "chub-env.log").read_text(encoding="utf-8").splitlines()

        self.assertTrue(registry_path.exists())
        self.assertTrue(dist_marker.exists())
        self.assertEqual(len(args_log), 1)
        self.assertIn("build", args_log[0])
        self.assertIn((chub_home / "timely-source").as_posix(), args_log[0])
        self.assertIn((chub_home / "timely-dist").as_posix(), args_log[0])
        self.assertEqual(env_log, [str(chub_home)])

    def test_chub_search_builds_before_running_search(self) -> None:
        chub_home = self.root / ".chub"
        self._seed_cached_search_index(chub_home)

        result = self._run_script(".timely-core/scripts/chub.sh", "search", "timely-playbook", "--json")

        args_log = (self.log_dir / "chub-args.log").read_text(encoding="utf-8").splitlines()
        self.assertEqual(result.stdout.strip(), "ok")
        self.assertEqual(len(args_log), 2)
        self.assertTrue(args_log[0].startswith("build "))
        self.assertEqual(args_log[1], "search timely-playbook --json")
        self.assertTrue((chub_home / "timely-dist" / ".built").exists())

    def test_chub_mcp_builds_then_execs_mcp_binary(self) -> None:
        chub_home = self.root / "mcp-chub"
        self._seed_cached_search_index(chub_home)

        result = self._run_script(
            ".timely-core/scripts/chub-mcp.sh",
            "--stdio",
            env={"CHUB_DIR": str(chub_home)},
        )

        args_log = (self.log_dir / "chub-args.log").read_text(encoding="utf-8").splitlines()
        mcp_args = (self.log_dir / "chub-mcp-args.log").read_text(encoding="utf-8").splitlines()
        mcp_env = (self.log_dir / "chub-mcp-env.log").read_text(encoding="utf-8").splitlines()

        self.assertEqual(result.stdout.strip(), "mcp ok")
        self.assertEqual(len(args_log), 1)
        self.assertTrue(args_log[0].startswith("build "))
        self.assertEqual(mcp_args, ["--stdio"])
        self.assertEqual(mcp_env, [str(chub_home)])
        self.assertTrue((chub_home / "timely-dist" / ".built").exists())


class CommunitySearchIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.chub_dir = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_sync_community_search_index_uses_cached_file(self) -> None:
        target = self.chub_dir / "sources" / "community" / "search-index.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('{"cached":true}', encoding="utf-8")

        result = timely_registry.sync_community_search_index(self.chub_dir)

        self.assertEqual(result["status"], "cached")
        self.assertEqual(target.read_text(encoding="utf-8"), '{"cached":true}')

    def test_sync_community_search_index_reports_warning_on_download_error(self) -> None:
        with patch("urllib.request.urlopen", side_effect=OSError("network down")):
            result = timely_registry.sync_community_search_index(self.chub_dir, force=True)

        self.assertEqual(result["status"], "warning")
        self.assertIn("network down", result["message"])
        self.assertFalse((self.chub_dir / "sources" / "community" / "search-index.json").exists())

    def test_sync_community_search_index_writes_downloaded_payload(self) -> None:
        with patch("urllib.request.urlopen", return_value=_FakeResponse(b'{"fresh":true}')):
            result = timely_registry.sync_community_search_index(self.chub_dir, force=True)

        target = self.chub_dir / "sources" / "community" / "search-index.json"
        self.assertEqual(result["status"], "synced")
        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(encoding="utf-8"), '{"fresh":true}')


if __name__ == "__main__":
    unittest.main()
