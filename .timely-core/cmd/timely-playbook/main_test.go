package main

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"gopkg.in/yaml.v3"
)

func buildTestBinary(t *testing.T) string {
	t.Helper()

	binPath := filepath.Join(t.TempDir(), "timely-playbook")
	cmd := exec.Command("go", "build", "-o", binPath, ".")
	cmd.Dir = "."
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("go build failed: %v\n%s", err, output)
	}
	return binPath
}

func writeTestFile(t *testing.T, root, relative, content string) {
	t.Helper()

	path := filepath.Join(root, relative)
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatalf("mkdir %s: %v", path, err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatalf("write %s: %v", path, err)
	}
}

func TestCLIUsageAndHelp(t *testing.T) {
	binPath := buildTestBinary(t)

	t.Run("no args", func(t *testing.T) {
		cmd := exec.Command(binPath)
		output, err := cmd.CombinedOutput()
		if err != nil {
			t.Fatalf("unexpected error: %v\n%s", err, output)
		}
		text := string(output)
		if !strings.Contains(text, "usage: timely-playbook <command> [args]") {
			t.Fatalf("expected usage output, got:\n%s", text)
		}
		if !strings.Contains(text, "  - init-config") {
			t.Fatalf("expected command list in usage output, got:\n%s", text)
		}
	})

	t.Run("explicit help", func(t *testing.T) {
		cmd := exec.Command(binPath, "--help")
		output, err := cmd.CombinedOutput()
		if err != nil {
			t.Fatalf("unexpected error: %v\n%s", err, output)
		}
		text := string(output)
		if !strings.Contains(text, "commands:") {
			t.Fatalf("expected help output, got:\n%s", text)
		}
		if !strings.Contains(text, "  - seed") {
			t.Fatalf("expected seed command in help output, got:\n%s", text)
		}
	})
}

func TestInitConfigWritesRootTrackerPaths(t *testing.T) {
	binPath := buildTestBinary(t)
	root := t.TempDir()

	cmd := exec.Command(
		binPath,
		"init-config",
		"--owner", "Alice Example",
		"--email", "alice@example.com",
		"--repo", "demo-repo",
	)
	cmd.Dir = root
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("init-config failed: %v\n%s", err, output)
	}

	data, err := os.ReadFile(filepath.Join(root, configFileName))
	if err != nil {
		t.Fatalf("read config: %v", err)
	}

	var cfg playbookConfig
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		t.Fatalf("unmarshal config: %v", err)
	}

	if cfg.OwnerName != "Alice Example" {
		t.Fatalf("unexpected owner name: %q", cfg.OwnerName)
	}
	if cfg.OwnerEmail != "alice@example.com" {
		t.Fatalf("unexpected owner email: %q", cfg.OwnerEmail)
	}
	if cfg.RepoName != "demo-repo" {
		t.Fatalf("unexpected repo name: %q", cfg.RepoName)
	}
	if cfg.DocsDir != ".timely-playbook/local" {
		t.Fatalf("unexpected docs dir: %q", cfg.DocsDir)
	}
	if cfg.JournalPath != ".timely-playbook/local/timely-trackers/test-run-journal.md" {
		t.Fatalf("unexpected journal path: %q", cfg.JournalPath)
	}
	if cfg.LedgerPath != ".timely-playbook/local/timely-trackers/agent-control-ledger.md" {
		t.Fatalf("unexpected ledger path: %q", cfg.LedgerPath)
	}
	if cfg.BacklogPath != ".timely-playbook/local/timely-trackers/todo-backlog.md" {
		t.Fatalf("unexpected backlog path: %q", cfg.BacklogPath)
	}
}

func TestPackageTemplatePreservesBootstrapAssetsAndSupportsInjectedPackaging(t *testing.T) {
	root := t.TempDir()

	writeTestFile(t, root, "AGENTS.md", "Owner Smoke Test\n")
	writeTestFile(t, root, "SKILLS.md", "# Skills\n")
	writeTestFile(t, root, "README.md", "# Timely Playbook\n\n- [Guide](TimelyPlaybook.md)\n- [How-to](HOWTO.md)\n")
	writeTestFile(t, root, ".gitignore", ".chub/\nnode_modules/\n")
	writeTestFile(t, root, "package.json", "{\"name\":\"demo\"}\n")
	writeTestFile(t, root, "package-lock.json", "{}\n")
	writeTestFile(t, root, ".node-version", "22.22.0\n")
	writeTestFile(t, root, ".nvmrc", "22.22.0\n")
	writeTestFile(t, root, "scripts/bootstrap-timely-template.sh", "#!/usr/bin/env bash\n")
	writeTestFile(t, root, "scripts/chub.sh", "#!/usr/bin/env bash\n")
	writeTestFile(t, root, "scripts/install-agent-skill.sh", "#!/usr/bin/env bash\n")
	writeTestFile(t, root, "scripts/install-codex-skill.sh", "#!/usr/bin/env bash\n")
	writeTestFile(t, root, ".vscode/tasks.json", "{\"version\":\"2.0.0\",\"tasks\":[]}\n")
	writeTestFile(t, root, "cmd/timely-playbook/main.go", "package main\n")
	writeTestFile(t, root, "cmd/timely-playbook/go.mod", "module timely-playbook\n")
	writeTestFile(t, root, "skills/chub-context-hub/SKILL.md", "---\nname: chub-context-hub\ndescription: test skill\n---\n")
	writeTestFile(t, root, "skills/chub-context-hub/agents/openai.yaml", "interface:\n  display_name: \"Context Hub\"\n")
	writeTestFile(t, root, "timely-trackers/test-run-journal.md", "# Journal\n")
	writeTestFile(t, root, "templates/todo-backlog.md", "# Backlog template\n")
	writeTestFile(t, root, ".orchestrator/STATUS.md", "# Status\n")
	writeTestFile(t, root, "run-logs/20260307/summary.md", "# Summary\n")
	writeTestFile(t, root, "dist/ignored.md", "# ignored\n")
	writeTestFile(t, root, "node_modules/ignored.txt", "ignored\n")
	writeTestFile(t, root, ".bin/timely-playbook", "ignored\n")
	writeTestFile(t, root, "vendor/ignored.txt", "ignored\n")

	cfg := defaultConfig(root)
	cfg.OwnerName = "Alice Example"
	cfg.OwnerEmail = "alice@example.com"
	cfg.RepoName = "demo-repo"

	templatedOutput := filepath.Join(t.TempDir(), "templated")
	if err := packageTemplate(root, templatedOutput, "dist/timely-template", true, false, cfg); err != nil {
		t.Fatalf("templated package failed: %v", err)
	}

	for _, relative := range []string{
		".timely-core/cmd/timely-playbook/main.go",
		".timely-core/cmd/timely-playbook/go.mod",
		".timely-core/scripts/bootstrap-timely-template.sh",
		".timely-core/scripts/chub.sh",
		".timely-core/scripts/install-agent-skill.sh",
		".timely-playbook/bin/timely-playbook",
		".timely-playbook/bin/chub.sh",
		".timely-playbook/bin/install-agent-skill.sh",
		".timely-playbook/local/AGENTS.md",
		".timely-playbook/local/SKILLS.md",
		".timely-playbook/local/skills/chub-context-hub/SKILL.md",
		".timely-playbook/local/skills/chub-context-hub/agents/openai.yaml",
		".timely-playbook/runtime/package.json",
		".timely-playbook/runtime/package-lock.json",
		".timely-playbook/config.yaml",
		".timely-core/manifest.json",
		".gitignore",
		"README.md",
		"AGENTS.md",
		"SKILLS.md",
	} {
		if _, err := os.Stat(filepath.Join(templatedOutput, relative)); err != nil {
			t.Fatalf("expected packaged file %s: %v", relative, err)
		}
	}

	templatedAgents, err := os.ReadFile(filepath.Join(templatedOutput, ".timely-playbook", "local", "AGENTS.md"))
	if err != nil {
		t.Fatalf("read templated AGENTS.md: %v", err)
	}
	if !strings.Contains(string(templatedAgents), "Smoke Test") {
		t.Fatalf("expected placeholders to remain in templated package, got: %s", templatedAgents)
	}

	rootReadme, err := os.ReadFile(filepath.Join(templatedOutput, "README.md"))
	if err != nil {
		t.Fatalf("read generated root README.md: %v", err)
	}
	if !strings.Contains(string(rootReadme), "# Timely Playbook") {
		t.Fatalf("expected root README title, got:\n%s", rootReadme)
	}
	if !strings.Contains(string(rootReadme), "(.timely-core/TimelyPlaybook.md)") {
		t.Fatalf("expected root README links to point at .timely-core content, got:\n%s", rootReadme)
	}

	for _, relative := range []string{
		"run-logs/20260307/summary.md",
		"dist/ignored.md",
		"node_modules/ignored.txt",
		".bin/timely-playbook",
		"vendor/ignored.txt",
		".timely-core/tests/__pycache__/ignored.pyc",
	} {
		if _, err := os.Stat(filepath.Join(templatedOutput, relative)); !os.IsNotExist(err) {
			t.Fatalf("expected %s to be excluded, stat err=%v", relative, err)
		}
	}

	injectedOutput := filepath.Join(t.TempDir(), "injected")
	if err := packageTemplate(root, injectedOutput, "dist/timely-template", false, true, cfg); err != nil {
		t.Fatalf("injected package failed: %v", err)
	}

	injectedAgents, err := os.ReadFile(filepath.Join(injectedOutput, ".timely-playbook", "local", "AGENTS.md"))
	if err != nil {
		t.Fatalf("read injected AGENTS.md: %v", err)
	}
	if !strings.Contains(string(injectedAgents), "Alice Example") {
		t.Fatalf("expected injected owner name, got: %s", injectedAgents)
	}
	if _, err := os.Stat(filepath.Join(injectedOutput, ".timely-core", "run-logs", "20260307", "summary.md")); err != nil {
		t.Fatalf("expected legacy run log to be included in the core snapshot when includeLogs=true: %v", err)
	}
}

func TestMigrateLayoutPreservesEditableLocalFiles(t *testing.T) {
	root := t.TempDir()

	writeTestFile(t, root, "AGENTS.md", "# Repo guardrail\n\nOwner Smoke Test\n")
	writeTestFile(t, root, "SKILLS.md", "# Repo skills\n")
	writeTestFile(t, root, ".orchestrator/ownership.yaml", "owners:\n  - docs\n")
	writeTestFile(t, root, ".orchestrator/state.json", "{\"tasks\":[]}\n")
	writeTestFile(t, root, "timely-trackers/test-run-journal.md", "# Journal\n")
	writeTestFile(t, root, "timely-trackers/agent-control-ledger.md", "# Ledger\n")
	writeTestFile(t, root, "timely-trackers/todo-backlog.md", "# Backlog\n")
	writeTestFile(t, root, "timely-trackers/ceremony-agendas.md", "# Agendas\n")
	writeTestFile(t, root, "skills/chub-context-hub/SKILL.md", "# Skill bundle\n")
	writeTestFile(t, root, "scripts/chub.sh", "#!/usr/bin/env bash\n")
	writeTestFile(t, root, "package.json", "{\"name\":\"demo\"}\n")
	writeTestFile(t, root, "package-lock.json", "{}\n")
	writeTestFile(t, root, ".node-version", "22.22.0\n")
	writeTestFile(t, root, ".nvmrc", "22.22.0\n")
	writeTestFile(t, root, "cmd/timely-playbook/main.go", "package main\n")
	writeTestFile(t, root, "cmd/timely-playbook/go.mod", "module timely-playbook\n")

	cfg := legacyDefaultConfig(root)
	cfg.OwnerName = "Alice Example"
	cfg.OwnerEmail = "alice@example.com"
	cfg.RepoName = "demo-repo"

	if err := migrateLayout(root, cfg); err != nil {
		t.Fatalf("migrateLayout failed: %v", err)
	}

	localAgents, err := os.ReadFile(filepath.Join(root, ".timely-playbook", "local", "AGENTS.md"))
	if err != nil {
		t.Fatalf("read migrated local AGENTS.md: %v", err)
	}
	if !strings.Contains(string(localAgents), "Alice Example") {
		t.Fatalf("expected migrated local AGENTS.md to preserve source content, got:\n%s", localAgents)
	}
	if strings.Contains(string(localAgents), "Canonical content: `.timely-playbook/local/AGENTS.md`.") {
		t.Fatalf("expected migrated local AGENTS.md to keep original content instead of the generated stub")
	}

	localSkills, err := os.ReadFile(filepath.Join(root, ".timely-playbook", "local", "SKILLS.md"))
	if err != nil {
		t.Fatalf("read migrated local SKILLS.md: %v", err)
	}
	if !strings.Contains(string(localSkills), "# Repo skills") {
		t.Fatalf("expected migrated local SKILLS.md to preserve source content, got:\n%s", localSkills)
	}

	if _, err := os.Stat(filepath.Join(root, ".timely-playbook", "local", ".orchestrator", "ownership.yaml")); err != nil {
		t.Fatalf("expected migrated ownership config: %v", err)
	}
	if _, err := os.Stat(filepath.Join(root, ".timely-playbook", "migration-backups")); err != nil {
		t.Fatalf("expected migration backup directory: %v", err)
	}
	if _, err := os.Stat(filepath.Join(root, ".timely-playbook", "config.yaml")); err != nil {
		t.Fatalf("expected relocated config: %v", err)
	}
	if _, err := os.Stat(filepath.Join(root, ".timely-core", "manifest.json")); err != nil {
		t.Fatalf("expected core manifest after migration: %v", err)
	}
	if _, err := os.Stat(filepath.Join(root, "scripts")); !os.IsNotExist(err) {
		t.Fatalf("expected legacy scripts directory to be removed after migration, stat err=%v", err)
	}
	if _, err := os.Stat(filepath.Join(root, legacyConfigFileName)); !os.IsNotExist(err) {
		t.Fatalf("expected legacy config file to be removed after migration, stat err=%v", err)
	}

	rootAgents, err := os.ReadFile(filepath.Join(root, "AGENTS.md"))
	if err != nil {
		t.Fatalf("read generated root AGENTS.md stub: %v", err)
	}
	if !strings.Contains(string(rootAgents), "Canonical content: `.timely-playbook/local/AGENTS.md`.") {
		t.Fatalf("expected root AGENTS.md stub after migration, got:\n%s", rootAgents)
	}
}

func TestPackageTemplateFromRelocatedSourceGeneratesRootDispatchers(t *testing.T) {
	root := t.TempDir()

	writeTestFile(t, root, ".timely-core/cmd/timely-playbook/main.go", "package main\n")
	writeTestFile(t, root, ".timely-core/cmd/timely-playbook/go.mod", "module timely-playbook\n")
	writeTestFile(t, root, ".timely-core/scripts/chub.sh", "#!/usr/bin/env bash\n")
	writeTestFile(t, root, ".timely-core/scripts/chub-mcp.sh", "#!/usr/bin/env bash\n")
	writeTestFile(t, root, ".timely-core/scripts/bootstrap-smoke.sh", "#!/usr/bin/env bash\n")
	writeTestFile(t, root, ".timely-core/scripts/bootstrap-timely-template.sh", "#!/usr/bin/env bash\n")
	writeTestFile(t, root, ".timely-core/scripts/run-markdownlint.sh", "#!/usr/bin/env bash\n")
	writeTestFile(t, root, ".timely-core/scripts/check-doc-links.sh", "#!/usr/bin/env bash\n")
	writeTestFile(t, root, ".timely-core/scripts/install-agent-skill.sh", "#!/usr/bin/env bash\n")
	writeTestFile(t, root, ".timely-core/scripts/install-codex-skill.sh", "#!/usr/bin/env bash\n")
	writeTestFile(t, root, ".timely-core/README.md", "# Timely Playbook\n\n- [Guide](TimelyPlaybook.md)\n")
	writeTestFile(t, root, ".gitignore", ".chub/\nnode_modules/\n")
	writeTestFile(t, root, ".timely-playbook/local/AGENTS.md", "# Local guardrail\n")
	writeTestFile(t, root, ".timely-playbook/local/SKILLS.md", "# Local skills\n")
	writeTestFile(t, root, ".timely-playbook/local/.orchestrator/ownership.yaml", "owners:\n  - docs\n")
	writeTestFile(t, root, ".timely-playbook/local/timely-trackers/test-run-journal.md", "# Journal\n")
	writeTestFile(t, root, ".timely-playbook/local/skills/chub-context-hub/SKILL.md", "# Skill\n")
	writeTestFile(t, root, ".timely-playbook/local/.vscode/tasks.json", strings.Join([]string{
		"{",
		"  \"version\": \"2.0.0\",",
		"  \"tasks\": [",
		"    {",
		"      \"label\": \"Orchestrator: plan\",",
		"      \"type\": \"shell\",",
		"      \"command\": \"python tools/orchestrator/orchestrator.py plan 'Set repo goal'\"",
		"    },",
		"    {",
		"      \"label\": \"Chub: build Timely mirror\",",
		"      \"type\": \"shell\",",
		"      \"command\": \"bash scripts/chub.sh build\"",
		"    }",
		"  ]",
		"}",
	}, "\n"))
	writeTestFile(t, root, ".timely-playbook/runtime/package.json", "{\"name\":\"demo\"}\n")
	writeTestFile(t, root, ".timely-playbook/runtime/package-lock.json", "{}\n")
	writeTestFile(t, root, ".timely-playbook/runtime/.node-version", "22.22.0\n")
	writeTestFile(t, root, ".timely-playbook/runtime/.nvmrc", "22.22.0\n")

	output := filepath.Join(t.TempDir(), "packaged")
	cfg := defaultConfig(root)
	if err := packageTemplate(root, output, "dist/timely-template", true, false, cfg); err != nil {
		t.Fatalf("packageTemplate failed: %v", err)
	}

	rootTasks, err := os.ReadFile(filepath.Join(output, ".vscode", "tasks.json"))
	if err != nil {
		t.Fatalf("read root tasks: %v", err)
	}
	rootTasksText := string(rootTasks)
	if !strings.Contains(rootTasksText, "python .timely-playbook/bin/orchestrator.py plan 'Set repo goal'") {
		t.Fatalf("expected orchestrator task to point at generated launcher, got:\n%s", rootTasksText)
	}
	if !strings.Contains(rootTasksText, "bash .timely-playbook/bin/chub.sh build") {
		t.Fatalf("expected chub task to point at generated launcher, got:\n%s", rootTasksText)
	}

	rootCI, err := os.ReadFile(filepath.Join(output, ".github", "workflows", "ci.yml"))
	if err != nil {
		t.Fatalf("read root workflow: %v", err)
	}
	rootCIText := string(rootCI)
	if !strings.Contains(rootCIText, "npm ci --prefix .timely-playbook/runtime") {
		t.Fatalf("expected relocated runtime install in generated workflow, got:\n%s", rootCIText)
	}
	if !strings.Contains(rootCIText, "bash .timely-playbook/bin/bootstrap-smoke.sh --smoke") {
		t.Fatalf("expected relocated smoke launcher in generated workflow, got:\n%s", rootCIText)
	}

	rootReadme, err := os.ReadFile(filepath.Join(output, "README.md"))
	if err != nil {
		t.Fatalf("read root README: %v", err)
	}
	if !strings.Contains(string(rootReadme), "(.timely-core/TimelyPlaybook.md)") {
		t.Fatalf("expected generated root README to rewrite core doc links, got:\n%s", rootReadme)
	}

	rootGitignore, err := os.ReadFile(filepath.Join(output, ".gitignore"))
	if err != nil {
		t.Fatalf("read root .gitignore: %v", err)
	}
	if !strings.Contains(string(rootGitignore), ".chub/") {
		t.Fatalf("expected root .gitignore to be copied into packaged output, got:\n%s", rootGitignore)
	}

	if _, err := os.Stat(filepath.Join(output, ".timely-playbook", "local", ".vscode", "tasks.json")); err != nil {
		t.Fatalf("expected canonical local task file to be packaged: %v", err)
	}
}

func TestInstallRuntimeAndPrepareChubRunsDefaultSetup(t *testing.T) {
	root := t.TempDir()
	npmLog := filepath.Join(root, "npm.log")
	chubLog := filepath.Join(root, "chub.log")

	writeTestFile(t, root, ".timely-playbook/runtime/package.json", "{\"name\":\"demo\"}\n")
	writeTestFile(t, root, ".timely-playbook/bin/chub.sh", strings.TrimSpace(`
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" > "__CHUB_LOG__"
mkdir -p "__CHUB_DIST__"
touch "__CHUB_DIST__/.built"
`)+"\n")
	if err := os.Chmod(filepath.Join(root, ".timely-playbook", "bin", "chub.sh"), 0o755); err != nil {
		t.Fatalf("chmod chub wrapper: %v", err)
	}

	fakeBin := filepath.Join(root, "fake-bin")
	if err := os.MkdirAll(fakeBin, 0o755); err != nil {
		t.Fatalf("mkdir fake-bin: %v", err)
	}
	npmScript := strings.NewReplacer(
		"__NPM_LOG__", npmLog,
		"__RUNTIME_DIR__", filepath.Join(root, ".timely-playbook", "runtime"),
	).Replace(strings.TrimSpace(`
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" > "__NPM_LOG__"
mkdir -p "__RUNTIME_DIR__/node_modules/.bin"
touch "__RUNTIME_DIR__/node_modules/.bin/chub"
chmod +x "__RUNTIME_DIR__/node_modules/.bin/chub"
`) + "\n")
	writeTestFile(t, root, "fake-bin/npm", npmScript)
	if err := os.Chmod(filepath.Join(fakeBin, "npm"), 0o755); err != nil {
		t.Fatalf("chmod fake npm: %v", err)
	}

	chubScript := strings.NewReplacer(
		"__CHUB_LOG__", chubLog,
		"__CHUB_DIST__", filepath.Join(root, ".chub", "timely-dist"),
	).Replace(strings.TrimSpace(`
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" > "__CHUB_LOG__"
mkdir -p "__CHUB_DIST__"
touch "__CHUB_DIST__/.built"
`) + "\n")
	if err := os.WriteFile(filepath.Join(root, ".timely-playbook", "bin", "chub.sh"), []byte(chubScript), 0o755); err != nil {
		t.Fatalf("rewrite chub wrapper: %v", err)
	}

	originalPath := os.Getenv("PATH")
	if err := os.Setenv("PATH", fakeBin+string(os.PathListSeparator)+originalPath); err != nil {
		t.Fatalf("set PATH: %v", err)
	}
	defer func() {
		_ = os.Setenv("PATH", originalPath)
	}()

	if err := installRuntimeAndPrepareChub(root); err != nil {
		t.Fatalf("installRuntimeAndPrepareChub failed: %v", err)
	}

	npmArgs, err := os.ReadFile(npmLog)
	if err != nil {
		t.Fatalf("read npm log: %v", err)
	}
	if !strings.Contains(string(npmArgs), "ci --prefix "+filepath.Join(root, ".timely-playbook", "runtime")) {
		t.Fatalf("expected npm ci against the relocated runtime, got:\n%s", npmArgs)
	}

	chubArgs, err := os.ReadFile(chubLog)
	if err != nil {
		t.Fatalf("read chub log: %v", err)
	}
	if strings.TrimSpace(string(chubArgs)) != "build" {
		t.Fatalf("expected initial chub build, got:\n%s", chubArgs)
	}
	if _, err := os.Stat(filepath.Join(root, ".chub", "timely-dist", ".built")); err != nil {
		t.Fatalf("expected chub dist marker after default setup: %v", err)
	}
}

func TestValidateCoreManifestIgnoresPythonCacheFiles(t *testing.T) {
	root := t.TempDir()
	writeTestFile(t, root, ".timely-core/cmd/timely-playbook/main.go", "package main\n")
	writeTestFile(t, root, ".timely-core/module.py", "print('ok')\n")

	if err := writeCoreManifest(filepath.Join(root, ".timely-core"), root); err != nil {
		t.Fatalf("writeCoreManifest failed: %v", err)
	}

	writeTestFile(t, root, ".timely-core/__pycache__/module.cpython-311.pyc", "compiled\n")
	writeTestFile(t, root, ".timely-core/module.pyc", "compiled\n")

	if err := validateCoreManifest(root); err != nil {
		t.Fatalf("validateCoreManifest should ignore Python cache files, got: %v", err)
	}
}

func TestAppendMarkdownRowCreatesAndEscapesRows(t *testing.T) {
	t.Run("creates new table when file is missing", func(t *testing.T) {
		path := filepath.Join(t.TempDir(), "journal.md")
		headers := []string{"Run ID", "Command(s)", "Result"}
		row := []string{"run-1", "cmd|with|pipe", "Pass"}

		if err := appendMarkdownRow(path, headers, row); err != nil {
			t.Fatalf("appendMarkdownRow failed: %v", err)
		}

		text, err := os.ReadFile(path)
		if err != nil {
			t.Fatalf("read file: %v", err)
		}
		content := string(text)
		if !strings.Contains(content, "| Run ID | Command(s) | Result |") {
			t.Fatalf("expected header row, got:\n%s", content)
		}
		if !strings.Contains(content, "cmd\\|with\\|pipe") {
			t.Fatalf("expected escaped pipes in row, got:\n%s", content)
		}
	})

	t.Run("appends into existing table before trailing prose", func(t *testing.T) {
		path := filepath.Join(t.TempDir(), "journal.md")
		existing := strings.Join([]string{
			"# Journal",
			"",
			"| Run ID | Result |",
			"| --- | --- |",
			"| run-0 | Pass |",
			"",
			"Footer note.",
			"",
		}, "\n")
		if err := os.WriteFile(path, []byte(existing), 0o644); err != nil {
			t.Fatalf("write file: %v", err)
		}

		if err := appendMarkdownRow(path, []string{"Run ID", "Result"}, []string{"run-1", "Pass"}); err != nil {
			t.Fatalf("appendMarkdownRow failed: %v", err)
		}

		text, err := os.ReadFile(path)
		if err != nil {
			t.Fatalf("read file: %v", err)
		}
		content := string(text)
		first := strings.Index(content, "| run-0 | Pass |")
		second := strings.Index(content, "| run-1 | Pass |")
		footer := strings.Index(content, "Footer note.")
		if !(first >= 0 && second > first && footer > second) {
			t.Fatalf("expected appended row before footer, got:\n%s", content)
		}
	})
}

func TestRunWeeklyWritesSummaryAndSupportsDryRun(t *testing.T) {
	binPath := buildTestBinary(t)
	root := t.TempDir()

	cfg := defaultConfig(root)
	cfg.OwnerName = "Alice Example"
	cfg.OwnerEmail = "alice@example.com"
	cfg.RepoName = "demo-repo"
	if err := writeConfig(filepath.Join(root, configFileName), cfg); err != nil {
		t.Fatalf("write config: %v", err)
	}

	writeTestFile(t, root, cfg.LedgerPath, strings.Join([]string{
		"# Ledger",
		"",
		"| Date | Decision | Context / Link | Owner |",
		"| --- | --- | --- | --- |",
		"| 2026-03-07 | Adopt verify path | TimelyPlaybook.md | Alice |",
		"",
	}, "\n"))
	writeTestFile(t, root, cfg.BacklogPath, strings.Join([]string{
		"# Backlog",
		"",
		"| Priority | Item | Context / Link | Owner | Due Date | Status |",
		"| --- | --- | --- | --- | --- | --- |",
		"| High | Add tests | TimelyPlaybook.md | Alice | 2026-03-08 | Todo |",
		"| Medium | Review docs | AGENTS.md | Alice |  | Done |",
		"",
	}, "\n"))
	writeTestFile(t, root, cfg.JournalPath, strings.Join([]string{
		"# Journal",
		"",
		"| Run ID | Date | Trigger | Scope | Command(s) | Result | Evidence |",
		"| --- | --- | --- | --- | --- | --- | --- |",
		"| existing-run | 2026-03-06 | Manual | Baseline | make validate | Pass | local |",
		"",
	}, "\n"))
	writeTestFile(t, root, cfg.CeremonyAgendasPath, "# Agendas\n")

	dryRun := exec.Command(binPath, "run-weekly", "--dry-run")
	dryRun.Dir = root
	dryOutput, err := dryRun.CombinedOutput()
	if err != nil {
		t.Fatalf("run-weekly --dry-run failed: %v\n%s", err, dryOutput)
	}
	dryText := string(dryOutput)
	if !strings.Contains(dryText, "- Ledger items: 1") {
		t.Fatalf("expected ledger count in dry-run output, got:\n%s", dryText)
	}
	if !strings.Contains(dryText, "- Backlog items: 2 (open: 1)") {
		t.Fatalf("expected backlog count in dry-run output, got:\n%s", dryText)
	}
	if _, err := os.Stat(filepath.Join(root, cfg.LogDir)); !os.IsNotExist(err) {
		t.Fatalf("dry-run should not create log dir, stat err=%v", err)
	}

	cmd := exec.Command(binPath, "run-weekly")
	cmd.Dir = root
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("run-weekly failed: %v\n%s", err, output)
	}

	todayDir := time.Now().Format("20060102")
	summaryPath := filepath.Join(root, cfg.LogDir, todayDir, "summary.md")
	summaryText, err := os.ReadFile(summaryPath)
	if err != nil {
		t.Fatalf("read weekly summary: %v", err)
	}
	if !strings.Contains(string(summaryText), "- Ledger items: 1") {
		t.Fatalf("unexpected summary contents:\n%s", summaryText)
	}
	if !strings.Contains(string(summaryText), "- Backlog items: 2 (open: 1)") {
		t.Fatalf("unexpected summary contents:\n%s", summaryText)
	}
	if !strings.Contains(string(summaryText), "- Backlog items with due date: 1") {
		t.Fatalf("unexpected summary contents:\n%s", summaryText)
	}

	journalText, err := os.ReadFile(filepath.Join(root, cfg.JournalPath))
	if err != nil {
		t.Fatalf("read journal: %v", err)
	}
	content := string(journalText)
	if !strings.Contains(content, "timely-playbook run-weekly") {
		t.Fatalf("expected run-weekly journal entry, got:\n%s", content)
	}
	if !strings.Contains(content, "run-weekly snapshot (ledger=1 backlog=2)") {
		t.Fatalf("expected run-weekly scope summary, got:\n%s", content)
	}
	if !strings.Contains(content, summaryPath) {
		t.Fatalf("expected summary path in journal, got:\n%s", content)
	}
}
