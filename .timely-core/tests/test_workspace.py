from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[1]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from tools.workspace import resolve_workspace, validate_core_manifest


class WorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_validate_core_manifest_ignores_python_cache_files(self) -> None:
        core_dir = self.root / ".timely-core"
        core_dir.mkdir(parents=True, exist_ok=True)
        source = core_dir / "module.py"
        source.write_text("print('ok')\n", encoding="utf-8")

        manifest = {
            "schema_version": 1,
            "generated_at": "2026-03-07T00:00:00Z",
            "source_root": self.root.as_posix(),
            "files": {
                "module.py": hashlib.sha256(source.read_bytes()).hexdigest(),
            },
        }
        (core_dir / "manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")

        cache_dir = core_dir / "__pycache__"
        cache_dir.mkdir(exist_ok=True)
        (cache_dir / "module.cpython-311.pyc").write_text("compiled\n", encoding="utf-8")
        (core_dir / "module.pyc").write_text("compiled\n", encoding="utf-8")

        validate_core_manifest(resolve_workspace(repo_root=self.root))

    def test_resolve_workspace_prefers_relocated_tree_without_env(self) -> None:
        (self.root / ".timely-core").mkdir(parents=True, exist_ok=True)
        (self.root / ".timely-playbook" / "local").mkdir(parents=True, exist_ok=True)
        (self.root / ".timely-playbook" / "runtime").mkdir(parents=True, exist_ok=True)

        workspace = resolve_workspace(repo_root=self.root)

        self.assertTrue(workspace.relocated)
        self.assertEqual(workspace.core_dir, self.root / ".timely-core")
        self.assertEqual(workspace.local_dir, self.root / ".timely-playbook" / "local")
        self.assertEqual(workspace.runtime_dir, self.root / ".timely-playbook" / "runtime")
        self.assertEqual(workspace.config_path, self.root / ".timely-playbook" / "config.yaml")
        self.assertEqual(workspace.cxdb_path, self.root / ".timely-playbook" / "local" / ".cxdb" / "cxdb.sqlite3")
        self.assertEqual(workspace.leann_index_path, self.root / ".timely-playbook" / "local" / ".leann" / "index.json")


if __name__ == "__main__":
    unittest.main()
