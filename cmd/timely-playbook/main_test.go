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
	if cfg.DocsDir != "." {
		t.Fatalf("unexpected docs dir: %q", cfg.DocsDir)
	}
	if cfg.JournalPath != "timely-trackers/test-run-journal.md" {
		t.Fatalf("unexpected journal path: %q", cfg.JournalPath)
	}
	if cfg.LedgerPath != "timely-trackers/agent-control-ledger.md" {
		t.Fatalf("unexpected ledger path: %q", cfg.LedgerPath)
	}
	if cfg.BacklogPath != "timely-trackers/todo-backlog.md" {
		t.Fatalf("unexpected backlog path: %q", cfg.BacklogPath)
	}
}

func TestPackageTemplatePreservesBootstrapAssetsAndSupportsInjectedPackaging(t *testing.T) {
	root := t.TempDir()

	writeTestFile(t, root, "AGENTS.md", "Owner {{OWNER_NAME}}\n")
	writeTestFile(t, root, "SKILLS.md", "# Skills\n")
	writeTestFile(t, root, "package.json", "{\"name\":\"demo\"}\n")
	writeTestFile(t, root, "scripts/bootstrap-timely-template.sh", "#!/usr/bin/env bash\n")
	writeTestFile(t, root, "scripts/chub.sh", "#!/usr/bin/env bash\n")
	writeTestFile(t, root, "scripts/install-codex-skill.sh", "#!/usr/bin/env bash\n")
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
		"AGENTS.md",
		"SKILLS.md",
		"package.json",
		"scripts/bootstrap-timely-template.sh",
		"scripts/chub.sh",
		"scripts/install-codex-skill.sh",
		"cmd/timely-playbook/main.go",
		"cmd/timely-playbook/go.mod",
		"skills/chub-context-hub/SKILL.md",
		"skills/chub-context-hub/agents/openai.yaml",
	} {
		if _, err := os.Stat(filepath.Join(templatedOutput, relative)); err != nil {
			t.Fatalf("expected packaged file %s: %v", relative, err)
		}
	}

	templatedAgents, err := os.ReadFile(filepath.Join(templatedOutput, "AGENTS.md"))
	if err != nil {
		t.Fatalf("read templated AGENTS.md: %v", err)
	}
	if !strings.Contains(string(templatedAgents), "{{OWNER_NAME}}") {
		t.Fatalf("expected placeholders to remain in templated package, got: %s", templatedAgents)
	}

	for _, relative := range []string{
		"run-logs/20260307/summary.md",
		"dist/ignored.md",
		"node_modules/ignored.txt",
		".bin/timely-playbook",
		"vendor/ignored.txt",
	} {
		if _, err := os.Stat(filepath.Join(templatedOutput, relative)); !os.IsNotExist(err) {
			t.Fatalf("expected %s to be excluded, stat err=%v", relative, err)
		}
	}

	injectedOutput := filepath.Join(t.TempDir(), "injected")
	if err := packageTemplate(root, injectedOutput, "dist/timely-template", false, true, cfg); err != nil {
		t.Fatalf("injected package failed: %v", err)
	}

	injectedAgents, err := os.ReadFile(filepath.Join(injectedOutput, "AGENTS.md"))
	if err != nil {
		t.Fatalf("read injected AGENTS.md: %v", err)
	}
	if !strings.Contains(string(injectedAgents), "Alice Example") {
		t.Fatalf("expected injected owner name, got: %s", injectedAgents)
	}
	if _, err := os.Stat(filepath.Join(injectedOutput, "run-logs/20260307/summary.md")); err != nil {
		t.Fatalf("expected run log to be included when includeLogs=true: %v", err)
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
