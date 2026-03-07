#!/usr/bin/env python3
from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("TIMELY_REPO_ROOT", str(ROOT))
os.environ.setdefault("TIMELY_CORE_DIR", str(ROOT / ".timely-core"))
os.environ.setdefault("TIMELY_PLAYBOOK_DIR", str(ROOT / ".timely-playbook"))
os.environ.setdefault("TIMELY_LOCAL_DIR", str(ROOT / ".timely-playbook" / "local"))
os.environ.setdefault("TIMELY_RUNTIME_DIR", str(ROOT / ".timely-playbook" / "runtime"))
os.environ.setdefault("TIMELY_CONFIG_PATH", str(ROOT / ".timely-playbook" / "config.yaml"))
core_dir = Path(os.environ["TIMELY_CORE_DIR"])
if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))
from tools.workspace import validate_core_manifest
validate_core_manifest()
runpy.run_path(str(core_dir / "tools" / "orchestrator" / "orchestrator.py"), run_name="__main__")
