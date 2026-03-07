from __future__ import annotations

import subprocess
import tempfile
import tarfile
import unittest
from pathlib import Path


class PlaybookPackagingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.repo_root = Path(__file__).resolve().parents[1]

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_cmd(self, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(args),
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_packaged_template_bootstrap_script_seeds_repo(self) -> None:
        bin_path = self.workspace / "timely-playbook"
        self.run_cmd("go", "build", "-o", str(bin_path), ".", cwd=self.repo_root / "cmd" / "timely-playbook")

        template_dir = self.workspace / "timely-template"
        self.run_cmd(str(bin_path), "package", "--output", str(template_dir), "--templated", cwd=self.repo_root)

        self.assertTrue((template_dir / "scripts" / "bootstrap-timely-template.sh").exists())
        self.assertTrue((template_dir / "cmd" / "timely-playbook" / "main.go").exists())
        self.assertTrue((template_dir / "SKILLS.md").exists())

        seeded_dir = self.workspace / "seeded"
        self.run_cmd(
            "bash",
            str(template_dir / "scripts" / "bootstrap-timely-template.sh"),
            "--source",
            str(template_dir),
            "--output",
            str(seeded_dir),
            "--owner",
            "Test User",
            "--email",
            "test@example.com",
            "--repo",
            "demo-repo",
            "--inject",
            "--init-git",
            cwd=self.workspace,
        )

        self.assertTrue((seeded_dir / "timely-playbook.yaml").exists())
        self.assertTrue((seeded_dir / "AGENTS.md").exists())
        self.assertTrue((seeded_dir / "SKILLS.md").exists())
        self.assertTrue((seeded_dir / "scripts" / "chub.sh").exists())
        self.assertTrue((seeded_dir / "scripts" / "install-codex-skill.sh").exists())
        self.assertTrue((seeded_dir / "skills" / "chub-context-hub" / "SKILL.md").exists())
        self.assertTrue((seeded_dir / ".git" / "HEAD").exists())

        config_text = (seeded_dir / "timely-playbook.yaml").read_text(encoding="utf-8")
        self.assertIn("owner_name: Test User", config_text)
        self.assertIn("owner_email: test@example.com", config_text)
        self.assertIn("repo_name: demo-repo", config_text)

    def test_packaged_template_keeps_placeholders_and_version_files(self) -> None:
        bin_path = self.workspace / "timely-playbook"
        self.run_cmd("go", "build", "-o", str(bin_path), ".", cwd=self.repo_root / "cmd" / "timely-playbook")

        template_dir = self.workspace / "timely-template"
        self.run_cmd(str(bin_path), "package", "--output", str(template_dir), "--templated", cwd=self.repo_root)

        self.assertTrue((template_dir / ".nvmrc").exists())
        self.assertTrue((template_dir / ".node-version").exists())
        self.assertTrue((template_dir / "package-lock.json").exists())
        self.assertTrue((template_dir / "scripts" / "install-codex-skill.sh").exists())
        self.assertTrue((template_dir / "skills" / "chub-context-hub" / "SKILL.md").exists())
        self.assertTrue((template_dir / "skills" / "chub-context-hub" / "agents" / "openai.yaml").exists())
        self.assertFalse((template_dir / "run-logs").exists())

        agents_text = (template_dir / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("{{OWNER_NAME}}", agents_text)

        archive_path = self.workspace / "timely-template.tgz"
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(template_dir, arcname="timely-template")

        extract_dir = self.workspace / "extracted"
        extract_dir.mkdir()
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=extract_dir, filter="data")

        extracted = extract_dir / "timely-template"
        self.assertTrue((extracted / "scripts" / "bootstrap-timely-template.sh").exists())
        self.assertTrue((extracted / ".nvmrc").exists())
        self.assertTrue((extracted / "cmd" / "timely-playbook" / "main.go").exists())
        self.assertTrue((extracted / "skills" / "chub-context-hub" / "SKILL.md").exists())
        self.assertFalse((extracted / "run-logs").exists())

    def test_context_hub_skill_installer_copies_repo_skill_bundle(self) -> None:
        bin_path = self.workspace / "timely-playbook"
        self.run_cmd("go", "build", "-o", str(bin_path), ".", cwd=self.repo_root / "cmd" / "timely-playbook")

        template_dir = self.workspace / "timely-template"
        self.run_cmd(str(bin_path), "package", "--output", str(template_dir), "--templated", cwd=self.repo_root)

        installed_root = self.workspace / "codex-home" / "skills"
        result = self.run_cmd(
            "bash",
            str(template_dir / "scripts" / "install-codex-skill.sh"),
            "chub-context-hub",
            "--dest",
            str(installed_root),
            "--copy",
            cwd=self.workspace,
        )

        self.assertIn("Restart Codex to pick up new skills.", result.stdout)
        installed_skill = installed_root / "chub-context-hub"
        self.assertTrue((installed_skill / "SKILL.md").exists())
        self.assertTrue((installed_skill / "agents" / "openai.yaml").exists())


if __name__ == "__main__":
    unittest.main()
