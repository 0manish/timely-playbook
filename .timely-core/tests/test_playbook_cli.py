from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import tempfile
import tarfile
import unittest
from pathlib import Path


class PlaybookPackagingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.repo_root = Path(__file__).resolve().parents[2]

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_cmd(
        self,
        *args: str,
        cwd: Path,
        env: dict[str, str] | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(args),
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
            env={**os.environ, **env} if env else None,
        )

    def current_release_platform(self) -> tuple[str, str] | None:
        system_name = platform.system()
        machine = platform.machine()
        if system_name == "Linux":
            os_name = "linux"
        elif system_name == "Darwin":
            os_name = "darwin"
        else:
            return None

        if machine == "x86_64":
            arch_name = "amd64"
        elif machine in {"arm64", "aarch64"}:
            arch_name = "arm64"
        else:
            return None

        return os_name, arch_name

    def write_release_assets(self, bin_path: Path, template_dir: Path, release_dir: Path) -> tuple[Path, Path]:
        template_asset = release_dir / "timely-template.tgz"
        with tarfile.open(template_asset, "w:gz") as tar:
            tar.add(template_dir, arcname="timely-template")

        release_platform = self.current_release_platform()
        if release_platform is None:
            self.skipTest("unsupported platform for release asset test")
        os_name, arch_name = release_platform

        binary_asset = release_dir / f"timely-playbook_{os_name}_{arch_name}.tar.gz"
        with tarfile.open(binary_asset, "w:gz") as tar:
            tar.add(bin_path, arcname="timely-playbook")

        checksums = {
            binary_asset.name: hashlib.sha256(binary_asset.read_bytes()).hexdigest(),
            template_asset.name: hashlib.sha256(template_asset.read_bytes()).hexdigest(),
        }
        checksum_lines = [
            f"{checksums[binary_asset.name]}  {binary_asset.name}",
            f"{checksums[template_asset.name]}  {template_asset.name}",
        ]
        (release_dir / "timely-checksums.txt").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
        return binary_asset, template_asset

    def test_packaged_template_bootstrap_script_seeds_repo(self) -> None:
        bin_path = self.workspace / "timely-playbook"
        self.run_cmd("go", "build", "-o", str(bin_path), ".", cwd=self.repo_root / ".timely-core" / "cmd" / "timely-playbook")

        template_dir = self.workspace / "timely-template"
        self.run_cmd(str(bin_path), "package", "--output", str(template_dir), "--templated", cwd=self.repo_root)

        self.assertTrue((template_dir / ".timely-playbook" / "bin" / "bootstrap-timely-template.sh").exists())
        self.assertTrue((template_dir / ".timely-playbook" / "bin" / "bootstrap-timely-release.sh").exists())
        self.assertTrue((template_dir / ".timely-core" / "cmd" / "timely-playbook" / "main.go").exists())
        self.assertTrue((template_dir / ".timely-playbook" / "local" / "SKILLS.md").exists())
        self.assertTrue((template_dir / ".github" / "workflows" / "release.yml").exists())
        self.assertTrue((template_dir / ".timely-playbook" / "local" / ".cxdb" / "README.md").exists())
        self.assertTrue((template_dir / ".timely-playbook" / "local" / ".leann" / "README.md").exists())
        self.assertTrue((template_dir / "README.md").exists())

        seeded_dir = self.workspace / "seeded"
        self.run_cmd(
            "bash",
            str(template_dir / ".timely-playbook" / "bin" / "bootstrap-timely-template.sh"),
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

        self.assertTrue((seeded_dir / "AGENTS.md").exists())
        self.assertTrue((seeded_dir / "SKILLS.md").exists())
        self.assertTrue((seeded_dir / "README.md").exists())
        self.assertTrue((seeded_dir / ".gitignore").exists())
        self.assertTrue((seeded_dir / ".timely-playbook" / "config.yaml").exists())
        self.assertTrue((seeded_dir / ".timely-core" / "manifest.json").exists())
        self.assertTrue((seeded_dir / ".timely-playbook" / "bin" / "chub.sh").exists())
        self.assertTrue((seeded_dir / ".timely-playbook" / "bin" / "bootstrap-timely-release.sh").exists())
        self.assertTrue((seeded_dir / ".github" / "workflows" / "release.yml").exists())
        self.assertTrue((seeded_dir / ".timely-playbook" / "runtime" / "node_modules" / ".bin" / "chub").exists())
        self.assertTrue((seeded_dir / ".chub" / "config.yaml").exists())
        self.assertTrue((seeded_dir / ".chub" / "timely-dist").exists())
        self.assertTrue((seeded_dir / ".timely-playbook" / "bin" / "install-agent-skill.sh").exists())
        self.assertTrue((seeded_dir / ".timely-playbook" / "bin" / "install-codex-skill.sh").exists())
        self.assertTrue((seeded_dir / ".timely-playbook" / "local" / "skills" / "chub-context-hub" / "SKILL.md").exists())
        self.assertTrue((seeded_dir / ".timely-playbook" / "local" / ".cxdb" / "README.md").exists())
        self.assertTrue((seeded_dir / ".timely-playbook" / "local" / ".leann" / "README.md").exists())
        self.assertTrue((seeded_dir / ".git" / "HEAD").exists())
        self.assertFalse((seeded_dir / "timely-playbook.yaml").exists())
        self.assertFalse((seeded_dir / "scripts").exists())
        self.assertFalse((seeded_dir / "tools").exists())
        self.assertFalse((seeded_dir / "package.json").exists())

        config_text = (seeded_dir / ".timely-playbook" / "config.yaml").read_text(encoding="utf-8")
        self.assertIn("owner_name: Test User", config_text)
        self.assertIn("owner_email: test@example.com", config_text)
        self.assertIn("repo_name: demo-repo", config_text)
        self.assertIn(".timely-playbook/local/timely-trackers/test-run-journal.md", config_text)

        root_readme = (seeded_dir / "README.md").read_text(encoding="utf-8")
        self.assertIn(".timely-core/TimelyPlaybook.md", root_readme)

        self.run_cmd("python", ".timely-playbook/bin/orchestrator.py", "context-sync", cwd=seeded_dir)
        self.assertTrue((seeded_dir / ".timely-playbook" / "local" / ".cxdb" / "cxdb.sqlite3").exists())
        self.assertTrue((seeded_dir / ".timely-playbook" / "local" / ".leann" / "index.json").exists())

    def test_packaged_template_keeps_placeholders_and_version_files(self) -> None:
        bin_path = self.workspace / "timely-playbook"
        self.run_cmd("go", "build", "-o", str(bin_path), ".", cwd=self.repo_root / ".timely-core" / "cmd" / "timely-playbook")

        template_dir = self.workspace / "timely-template"
        self.run_cmd(str(bin_path), "package", "--output", str(template_dir), "--templated", cwd=self.repo_root)

        self.assertTrue((template_dir / ".timely-playbook" / "runtime" / ".nvmrc").exists())
        self.assertTrue((template_dir / ".timely-playbook" / "runtime" / ".node-version").exists())
        self.assertTrue((template_dir / ".timely-playbook" / "runtime" / "package-lock.json").exists())
        self.assertTrue((template_dir / ".gitignore").exists())
        self.assertTrue((template_dir / ".github" / "workflows" / "release.yml").exists())
        self.assertTrue((template_dir / ".timely-playbook" / "bin" / "install-agent-skill.sh").exists())
        self.assertTrue((template_dir / ".timely-playbook" / "bin" / "bootstrap-timely-release.sh").exists())
        self.assertTrue((template_dir / ".timely-playbook" / "bin" / "install-codex-skill.sh").exists())
        self.assertTrue((template_dir / ".timely-playbook" / "local" / "skills" / "chub-context-hub" / "SKILL.md").exists())
        self.assertTrue((template_dir / ".timely-playbook" / "local" / "skills" / "chub-context-hub" / "agents" / "openai.yaml").exists())
        self.assertTrue((template_dir / ".timely-playbook" / "local" / ".cxdb" / "README.md").exists())
        self.assertTrue((template_dir / ".timely-playbook" / "local" / ".leann" / "README.md").exists())
        self.assertTrue((template_dir / "README.md").exists())
        self.assertFalse((template_dir / "run-logs").exists())

        agents_text = (template_dir / ".timely-playbook" / "local" / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Smoke Test", agents_text)

        archive_path = self.workspace / "timely-template.tgz"
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(template_dir, arcname="timely-template")

        extract_dir = self.workspace / "extracted"
        extract_dir.mkdir()
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=extract_dir, filter="data")

        extracted = extract_dir / "timely-template"
        self.assertTrue((extracted / ".timely-playbook" / "bin" / "bootstrap-timely-template.sh").exists())
        self.assertTrue((extracted / ".timely-playbook" / "bin" / "bootstrap-timely-release.sh").exists())
        self.assertTrue((extracted / ".timely-playbook" / "runtime" / ".nvmrc").exists())
        self.assertTrue((extracted / ".github" / "workflows" / "release.yml").exists())
        self.assertTrue((extracted / ".timely-core" / "cmd" / "timely-playbook" / "main.go").exists())
        self.assertTrue((extracted / ".timely-playbook" / "local" / "skills" / "chub-context-hub" / "SKILL.md").exists())
        self.assertTrue((extracted / ".gitignore").exists())
        self.assertTrue((extracted / "README.md").exists())
        self.assertFalse((extracted / "run-logs").exists())

    def test_release_bootstrap_script_seeds_repo_from_release_assets(self) -> None:
        bin_path = self.workspace / "timely-playbook"
        self.run_cmd("go", "build", "-o", str(bin_path), ".", cwd=self.repo_root / ".timely-core" / "cmd" / "timely-playbook")

        template_dir = self.workspace / "timely-template"
        self.run_cmd(str(bin_path), "package", "--output", str(template_dir), "--templated", cwd=self.repo_root)

        release_dir = self.workspace / "release"
        release_dir.mkdir()
        self.write_release_assets(bin_path, template_dir, release_dir)

        install_dir = self.workspace / "installed-bin"
        seeded_dir = self.workspace / "release-seeded"
        self.run_cmd(
            "bash",
            str(self.repo_root / ".timely-core" / "scripts" / "bootstrap-timely-release.sh"),
            "--asset-base-url",
            f"file://{release_dir}",
            "--output",
            str(seeded_dir),
            "--owner",
            "Release User",
            "--email",
            "release@example.com",
            "--repo",
            "release-demo",
            "--inject",
            "--init-git",
            "--install-dir",
            str(install_dir),
            "--skip-runtime-setup",
            cwd=self.workspace,
        )

        self.assertTrue((install_dir / "timely-playbook").exists())
        self.assertTrue((seeded_dir / ".timely-playbook" / "config.yaml").exists())
        self.assertTrue((seeded_dir / ".timely-playbook" / "bin" / "bootstrap-timely-release.sh").exists())
        self.assertTrue((seeded_dir / ".github" / "workflows" / "release.yml").exists())
        self.assertTrue((seeded_dir / ".git" / "HEAD").exists())

        config_text = (seeded_dir / ".timely-playbook" / "config.yaml").read_text(encoding="utf-8")
        self.assertIn("owner_name: Release User", config_text)
        self.assertIn("owner_email: release@example.com", config_text)
        self.assertIn("repo_name: release-demo", config_text)

        help_output = self.run_cmd(str(install_dir / "timely-playbook"), "help", cwd=self.workspace)
        self.assertIn("seed", help_output.stdout)

    def test_release_bootstrap_script_rejects_checksum_mismatch(self) -> None:
        bin_path = self.workspace / "timely-playbook"
        self.run_cmd("go", "build", "-o", str(bin_path), ".", cwd=self.repo_root / ".timely-core" / "cmd" / "timely-playbook")

        template_dir = self.workspace / "timely-template"
        self.run_cmd(str(bin_path), "package", "--output", str(template_dir), "--templated", cwd=self.repo_root)

        release_dir = self.workspace / "release-bad"
        release_dir.mkdir()
        binary_asset, template_asset = self.write_release_assets(bin_path, template_dir, release_dir)

        bad_checksums = "\n".join(
            [
                f"{'0' * 64}  {binary_asset.name}",
                f"{hashlib.sha256(template_asset.read_bytes()).hexdigest()}  {template_asset.name}",
            ]
        )
        (release_dir / "timely-checksums.txt").write_text(bad_checksums + "\n", encoding="utf-8")

        seeded_dir = self.workspace / "release-bad-seeded"
        result = self.run_cmd(
            "bash",
            str(self.repo_root / ".timely-core" / "scripts" / "bootstrap-timely-release.sh"),
            "--asset-base-url",
            f"file://{release_dir}",
            "--output",
            str(seeded_dir),
            "--owner",
            "Checksum User",
            "--email",
            "checksum@example.com",
            "--repo",
            "checksum-demo",
            "--skip-runtime-setup",
            "--skip-binary-install",
            cwd=self.workspace,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum mismatch", result.stderr)
        self.assertFalse((seeded_dir / ".timely-playbook" / "config.yaml").exists())

    def test_seeded_launcher_uses_installed_binary_when_go_is_missing(self) -> None:
        go_binary = shutil.which("go")
        bash_binary = shutil.which("bash")
        self.assertIsNotNone(go_binary)
        self.assertIsNotNone(bash_binary)

        bin_path = self.workspace / "timely-playbook"
        self.run_cmd("go", "build", "-o", str(bin_path), ".", cwd=self.repo_root / ".timely-core" / "cmd" / "timely-playbook")

        seeded_dir = self.workspace / "seeded-launcher"
        self.run_cmd(
            str(bin_path),
            "seed",
            "--output",
            str(seeded_dir),
            "--owner",
            "Launcher User",
            "--email",
            "launcher@example.com",
            "--repo",
            "launcher-demo",
            "--skip-runtime-setup",
            cwd=self.repo_root,
        )

        fallback_dir = self.workspace / "fallback-bin"
        fallback_dir.mkdir()
        shutil.copy2(bin_path, fallback_dir / "timely-playbook")
        for tool_name in ("dirname", "basename"):
            tool_path = shutil.which(tool_name)
            self.assertIsNotNone(tool_path)
            os.symlink(tool_path, fallback_dir / tool_name)
        env = {"PATH": str(fallback_dir)}

        result = self.run_cmd(
            str(bash_binary),
            ".timely-playbook/bin/timely-playbook",
            "help",
            cwd=seeded_dir,
            env=env,
        )

        self.assertIn("commands:", result.stdout)
        self.assertFalse((seeded_dir / ".timely-playbook" / "runtime" / "cache" / "timely-playbook").exists())

    def test_context_hub_skill_installer_copies_repo_skill_bundle(self) -> None:
        bin_path = self.workspace / "timely-playbook"
        self.run_cmd("go", "build", "-o", str(bin_path), ".", cwd=self.repo_root / ".timely-core" / "cmd" / "timely-playbook")

        template_dir = self.workspace / "timely-template"
        self.run_cmd(str(bin_path), "package", "--output", str(template_dir), "--templated", cwd=self.repo_root)

        installed_root = self.workspace / "agent-home" / "skills"
        result = self.run_cmd(
            "bash",
            str(template_dir / ".timely-playbook" / "bin" / "install-agent-skill.sh"),
            "chub-context-hub",
            "--dest",
            str(installed_root),
            "--copy",
            cwd=self.workspace,
        )

        self.assertIn("Restart your agent tool if it caches skills.", result.stdout)
        installed_skill = installed_root / "chub-context-hub"
        self.assertTrue((installed_skill / "SKILL.md").exists())
        self.assertTrue((installed_skill / "agents" / "openai.yaml").exists())

    def test_context_hub_skill_installer_uses_agent_skills_home_by_default(self) -> None:
        bin_path = self.workspace / "timely-playbook"
        self.run_cmd("go", "build", "-o", str(bin_path), ".", cwd=self.repo_root / ".timely-core" / "cmd" / "timely-playbook")

        template_dir = self.workspace / "timely-template"
        self.run_cmd(str(bin_path), "package", "--output", str(template_dir), "--templated", cwd=self.repo_root)

        agent_home = self.workspace / "agent-home"
        self.run_cmd(
            "bash",
            str(template_dir / ".timely-playbook" / "bin" / "install-agent-skill.sh"),
            "chub-context-hub",
            cwd=self.workspace,
            env={"AGENT_SKILLS_HOME": str(agent_home / "skills")},
        )

        installed_skill = agent_home / "skills" / "chub-context-hub"
        self.assertTrue((installed_skill / "SKILL.md").exists())
        self.assertTrue((installed_skill / "agents" / "openai.yaml").exists())

    def test_context_hub_codex_compat_installer_uses_codex_home(self) -> None:
        bin_path = self.workspace / "timely-playbook"
        self.run_cmd("go", "build", "-o", str(bin_path), ".", cwd=self.repo_root / ".timely-core" / "cmd" / "timely-playbook")

        template_dir = self.workspace / "timely-template"
        self.run_cmd(str(bin_path), "package", "--output", str(template_dir), "--templated", cwd=self.repo_root)

        codex_home = self.workspace / "codex-home"
        result = self.run_cmd(
            "bash",
            str(template_dir / ".timely-playbook" / "bin" / "install-codex-skill.sh"),
            "chub-context-hub",
            cwd=self.workspace,
            env={"CODEX_HOME": str(codex_home)},
        )

        self.assertIn("Restart your agent tool if it caches skills.", result.stdout)
        installed_skill = codex_home / "skills" / "chub-context-hub"
        self.assertTrue((installed_skill / "SKILL.md").exists())
        self.assertTrue((installed_skill / "agents" / "openai.yaml").exists())

    def test_packaged_context_hub_skill_uses_repo_root_wrapper_paths(self) -> None:
        bin_path = self.workspace / "timely-playbook"
        self.run_cmd("go", "build", "-o", str(bin_path), ".", cwd=self.repo_root / ".timely-core" / "cmd" / "timely-playbook")

        template_dir = self.workspace / "timely-template"
        self.run_cmd(str(bin_path), "package", "--output", str(template_dir), "--templated", cwd=self.repo_root)

        skill_text = (template_dir / ".timely-playbook" / "local" / "skills" / "chub-context-hub" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("../../scripts/", skill_text)
        self.assertIn("bash .timely-playbook/bin/chub.sh validate", skill_text)
        self.assertIn("bash .timely-playbook/bin/install-agent-skill.sh chub-context-hub", skill_text)

    def test_bootstrap_smoke_ignores_parent_timely_env(self) -> None:
        fake_parent = self.workspace / "fake-parent"
        (fake_parent / ".timely-core").mkdir(parents=True, exist_ok=True)
        (fake_parent / ".timely-playbook" / "local").mkdir(parents=True, exist_ok=True)
        (fake_parent / ".timely-playbook" / "runtime").mkdir(parents=True, exist_ok=True)
        (fake_parent / ".timely-playbook" / "bin").mkdir(parents=True, exist_ok=True)

        env = {
            "TIMELY_REPO_ROOT": str(fake_parent),
            "TIMELY_CORE_DIR": str(fake_parent / ".timely-core"),
            "TIMELY_PLAYBOOK_DIR": str(fake_parent / ".timely-playbook"),
            "TIMELY_LOCAL_DIR": str(fake_parent / ".timely-playbook" / "local"),
            "TIMELY_RUNTIME_DIR": str(fake_parent / ".timely-playbook" / "runtime"),
            "TIMELY_BIN_DIR": str(fake_parent / ".timely-playbook" / "bin"),
            "TIMELY_CONFIG_PATH": str(fake_parent / ".timely-playbook" / "config.yaml"),
        }

        result = self.run_cmd(
            "bash",
            str(self.repo_root / ".timely-core" / "scripts" / "bootstrap-smoke.sh"),
            "--smoke",
            cwd=self.repo_root,
            env=env,
        )

        self.assertIn("bootstrap smoke test passed", result.stdout)
        self.assertFalse((fake_parent / ".timely-playbook" / "config.yaml").exists())


if __name__ == "__main__":
    unittest.main()
