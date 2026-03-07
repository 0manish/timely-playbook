package main

import (
	"archive/tar"
	"compress/gzip"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"

	"gopkg.in/yaml.v3"
)

const (
	configFileName       = ".timely-playbook/config.yaml"
	legacyConfigFileName = "timely-playbook.yaml"
	defaultCoreDirName   = ".timely-core"
	defaultTimelyDirName = ".timely-playbook"
)

var markdownLinkPattern = regexp.MustCompile(`\]\(([^)]+)\)`)

type workspacePaths struct {
	Root             string
	CoreDir          string
	TimelyDir        string
	LocalDir         string
	RuntimeDir       string
	BinDir           string
	ConfigPath       string
	LegacyConfigPath string
	ChubDir          string
	BackupDir        string
}

type sourceLayout struct {
	Root        string
	CoreRoot    string
	LocalRoot   string
	RuntimeRoot string
	Relocated   bool
}

type coreManifest struct {
	SchemaVersion int               `json:"schema_version"`
	GeneratedAt   string            `json:"generated_at"`
	SourceRoot    string            `json:"source_root"`
	SourceCommit  string            `json:"source_commit,omitempty"`
	Files         map[string]string `json:"files"`
}

func resolveWorkspace(root string) workspacePaths {
	root = cleanAbsPath(root)
	timelyDir := envOr("TIMELY_PLAYBOOK_DIR", filepath.Join(root, defaultTimelyDirName))
	coreDir := envOr("TIMELY_CORE_DIR", filepath.Join(root, defaultCoreDirName))
	localDir := envOr("TIMELY_LOCAL_DIR", filepath.Join(timelyDir, "local"))
	runtimeDir := envOr("TIMELY_RUNTIME_DIR", filepath.Join(timelyDir, "runtime"))
	binDir := envOr("TIMELY_BIN_DIR", filepath.Join(timelyDir, "bin"))
	configPath := envOr("TIMELY_CONFIG_PATH", filepath.Join(root, configFileName))
	return workspacePaths{
		Root:             root,
		CoreDir:          coreDir,
		TimelyDir:        timelyDir,
		LocalDir:         localDir,
		RuntimeDir:       runtimeDir,
		BinDir:           binDir,
		ConfigPath:       configPath,
		LegacyConfigPath: filepath.Join(root, legacyConfigFileName),
		ChubDir:          envOr("TIMELY_CHUB_DIR", filepath.Join(root, ".chub")),
		BackupDir:        filepath.Join(timelyDir, "migration-backups"),
	}
}

func cleanAbsPath(path string) string {
	if path == "" {
		return ""
	}
	abs, err := filepath.Abs(path)
	if err != nil {
		return filepath.Clean(path)
	}
	return filepath.Clean(abs)
}

func envOr(key, fallback string) string {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback
	}
	if filepath.IsAbs(value) {
		return filepath.Clean(value)
	}
	return filepath.Clean(value)
}

func legacyDefaultConfig(root string) playbookConfig {
	return playbookConfig{
		OwnerName:           "Smoke Test",
		OwnerEmail:          "smoke@example.com",
		RepoName:            filepath.Base(root),
		DocsDir:             ".",
		LogDir:              "run-logs",
		JournalPath:         "timely-trackers/test-run-journal.md",
		LedgerPath:          "timely-trackers/agent-control-ledger.md",
		BacklogPath:         "timely-trackers/todo-backlog.md",
		CeremonyAgendasPath: "timely-trackers/ceremony-agendas.md",
	}
}

func defaultConfig(root string) playbookConfig {
	return playbookConfig{
		OwnerName:           "Smoke Test",
		OwnerEmail:          "smoke@example.com",
		RepoName:            filepath.Base(root),
		DocsDir:             filepath.ToSlash(filepath.Join(defaultTimelyDirName, "local")),
		LogDir:              filepath.ToSlash(filepath.Join(defaultTimelyDirName, "local", "run-logs")),
		JournalPath:         filepath.ToSlash(filepath.Join(defaultTimelyDirName, "local", "timely-trackers", "test-run-journal.md")),
		LedgerPath:          filepath.ToSlash(filepath.Join(defaultTimelyDirName, "local", "timely-trackers", "agent-control-ledger.md")),
		BacklogPath:         filepath.ToSlash(filepath.Join(defaultTimelyDirName, "local", "timely-trackers", "todo-backlog.md")),
		CeremonyAgendasPath: filepath.ToSlash(filepath.Join(defaultTimelyDirName, "local", "timely-trackers", "ceremony-agendas.md")),
	}
}

func configForEmission(root string, base playbookConfig) playbookConfig {
	cfg := defaultConfig(root)
	if strings.TrimSpace(base.OwnerName) != "" {
		cfg.OwnerName = base.OwnerName
	}
	if strings.TrimSpace(base.OwnerEmail) != "" {
		cfg.OwnerEmail = base.OwnerEmail
	}
	if strings.TrimSpace(base.RepoName) != "" {
		cfg.RepoName = base.RepoName
	}
	return cfg
}

func writeConfig(path string, cfg playbookConfig) error {
	data, err := yaml.Marshal(cfg)
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o644)
}

func mergeConfigDefaults(cfg, defaults playbookConfig, root string) playbookConfig {
	if cfg.OwnerName == "" {
		cfg.OwnerName = defaults.OwnerName
	}
	if cfg.OwnerEmail == "" {
		cfg.OwnerEmail = defaults.OwnerEmail
	}
	if cfg.RepoName == "" {
		cfg.RepoName = defaults.RepoName
	}
	if cfg.DocsDir == "" {
		cfg.DocsDir = defaults.DocsDir
	}
	if cfg.LogDir == "" {
		cfg.LogDir = defaults.LogDir
	}
	if cfg.JournalPath == "" {
		cfg.JournalPath = defaults.JournalPath
	}
	if cfg.LedgerPath == "" {
		cfg.LedgerPath = defaults.LedgerPath
	}
	if cfg.BacklogPath == "" {
		cfg.BacklogPath = defaults.BacklogPath
	}
	if cfg.CeremonyAgendasPath == "" {
		cfg.CeremonyAgendasPath = defaults.CeremonyAgendasPath
	}
	if cfg.RepoName == "" {
		cfg.RepoName = filepath.Base(root)
	}
	return cfg
}

func readConfig(root string) (playbookConfig, error) {
	workspace := resolveWorkspace(root)

	if data, err := os.ReadFile(workspace.ConfigPath); err == nil {
		var cfg playbookConfig
		if err := yaml.Unmarshal(data, &cfg); err != nil {
			return playbookConfig{}, err
		}
		return mergeConfigDefaults(cfg, defaultConfig(root), root), nil
	}

	data, err := os.ReadFile(workspace.LegacyConfigPath)
	if err != nil {
		return playbookConfig{}, err
	}
	var cfg playbookConfig
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return playbookConfig{}, err
	}
	return mergeConfigDefaults(cfg, legacyDefaultConfig(root), root), nil
}

func normalizeSourceLayout(root string) (sourceLayout, error) {
	root = cleanAbsPath(root)
	relocatedCore := filepath.Join(root, defaultCoreDirName)
	relocatedLocal := filepath.Join(root, defaultTimelyDirName, "local")
	relocatedRuntime := filepath.Join(root, defaultTimelyDirName, "runtime")
	if fileExists(filepath.Join(relocatedCore, "cmd", "timely-playbook", "main.go")) {
		return sourceLayout{
			Root:        root,
			CoreRoot:    relocatedCore,
			LocalRoot:   relocatedLocal,
			RuntimeRoot: relocatedRuntime,
			Relocated:   true,
		}, nil
	}
	if fileExists(filepath.Join(root, "cmd", "timely-playbook", "main.go")) {
		return sourceLayout{
			Root:        root,
			CoreRoot:    root,
			LocalRoot:   root,
			RuntimeRoot: root,
			Relocated:   false,
		}, nil
	}
	return sourceLayout{}, fmt.Errorf("%s is not a timely-playbook source or package", root)
}

func fileExists(path string) bool {
	info, err := os.Stat(path)
	return err == nil && !info.IsDir()
}

func pathExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func packageTemplate(root, output, relOutput string, keepPlaceholders, includeLogs bool, cfg playbookConfig) error {
	source, err := normalizeSourceLayout(root)
	if err != nil {
		return err
	}
	output = cleanAbsPath(output)

	if err := os.RemoveAll(output); err != nil {
		return err
	}
	if err := os.MkdirAll(output, 0o755); err != nil {
		return err
	}

	cfg = configForEmission(output, cfg)
	replacements := placeholderReplacements(cfg)
	if keepPlaceholders {
		replacements = map[string]string{}
	}

	workspace := resolveWorkspace(output)
	if err := os.MkdirAll(workspace.CoreDir, 0o755); err != nil {
		return err
	}

	if err := copyCoreSnapshot(source, workspace.CoreDir, relOutput, includeLogs, keepPlaceholders, replacements); err != nil {
		return err
	}
	if err := copyEditableLocal(source, workspace.LocalDir, keepPlaceholders, replacements); err != nil {
		return err
	}
	if err := copyRuntimeFiles(source, workspace.RuntimeDir, keepPlaceholders, replacements); err != nil {
		return err
	}
	if err := writeConfig(workspace.ConfigPath, cfg); err != nil {
		return err
	}
	if err := writeLaunchers(output); err != nil {
		return err
	}
	if err := writeRootStubs(output); err != nil {
		return err
	}
	if err := writeRootWorkflowDispatchers(source, output); err != nil {
		return err
	}
	if err := writeRootTaskDispatcher(source, output); err != nil {
		return err
	}
	if err := writeCoreManifest(workspace.CoreDir, source.Root); err != nil {
		return err
	}
	return nil
}

func placeholderReplacements(cfg playbookConfig) map[string]string {
	return map[string]string{
		"Smoke Test":                      cfg.OwnerName,
		"smoke@example.com":               cfg.OwnerEmail,
		"smoke-project":                   cfg.RepoName,
		".timely-playbook/local":          cfg.DocsDir,
		".timely-playbook/local/run-logs": cfg.LogDir,
		".timely-playbook/local/timely-trackers/test-run-journal.md":     cfg.JournalPath,
		".timely-playbook/local/timely-trackers/agent-control-ledger.md": cfg.LedgerPath,
		".timely-playbook/local/timely-trackers/todo-backlog.md":         cfg.BacklogPath,
		".timely-playbook/local/timely-trackers/ceremony-agendas.md":     cfg.CeremonyAgendasPath,
	}
}

func copyCoreSnapshot(source sourceLayout, outputCore, relOutput string, includeLogs, keepPlaceholders bool, replacements map[string]string) error {
	if source.Relocated {
		return copyTree(source.CoreRoot, outputCore, keepPlaceholders, replacements, func(rel string, d fs.DirEntry) bool {
			return rel != "manifest.json"
		})
	}

	exclude := map[string]struct{}{
		".git":                   {},
		".chub":                  {},
		defaultCoreDirName:       {},
		defaultTimelyDirName:     {},
		"dist":                   {},
		".orchestrator/upstream": {},
		".bin":                   {},
		"fullstack-projects":     {},
		"node_modules":           {},
		"vendor":                 {},
		"cmd/dist":               {},
		legacyConfigFileName:     {},
	}
	if !includeLogs {
		exclude["run-logs"] = struct{}{}
	}

	return copyTree(source.Root, outputCore, keepPlaceholders, replacements, func(rel string, d fs.DirEntry) bool {
		if rel == "" {
			return true
		}
		if relOutput != "." && (rel == relOutput || strings.HasPrefix(rel, relOutput+"/")) {
			return false
		}
		parts := strings.Split(rel, "/")
		if len(parts) > 0 {
			if _, ok := exclude[parts[0]]; ok {
				return false
			}
			for i := 1; i < len(parts); i++ {
				if _, ok := exclude[strings.Join(parts[:i+1], "/")]; ok {
					return false
				}
			}
		}
		return true
	})
}

func copyEditableLocal(source sourceLayout, outputLocal string, keepPlaceholders bool, replacements map[string]string) error {
	selected := []string{
		"AGENTS.md",
		"SKILLS.md",
		".orchestrator",
		"timely-trackers",
		"skills/chub-context-hub",
		".github/workflows",
		".vscode/tasks.json",
	}
	for _, rel := range selected {
		sourceBase := source.Root
		if source.Relocated {
			sourceBase = source.LocalRoot
		}
		if err := copySelectedPath(sourceBase, outputLocal, rel, keepPlaceholders, replacements); err != nil {
			return err
		}
	}
	return nil
}

func copyRuntimeFiles(source sourceLayout, outputRuntime string, keepPlaceholders bool, replacements map[string]string) error {
	selected := []string{
		"package.json",
		"package-lock.json",
		".node-version",
		".nvmrc",
	}
	for _, rel := range selected {
		sourceBase := source.Root
		if source.Relocated {
			sourceBase = source.RuntimeRoot
		}
		if err := copySelectedPath(sourceBase, outputRuntime, rel, keepPlaceholders, replacements); err != nil {
			return err
		}
	}
	return nil
}

func copySelectedPath(sourceBase, targetBase, rel string, keepPlaceholders bool, replacements map[string]string) error {
	srcPath := filepath.Join(sourceBase, filepath.FromSlash(rel))
	if !pathExists(srcPath) {
		return nil
	}
	info, err := os.Stat(srcPath)
	if err != nil {
		return err
	}
	if info.IsDir() {
		return copyTree(srcPath, filepath.Join(targetBase, filepath.FromSlash(rel)), keepPlaceholders, replacements, func(rel string, d fs.DirEntry) bool {
			if strings.HasPrefix(filepath.ToSlash(filepath.Join(filepath.ToSlash(rel), "")), ".orchestrator/upstream") {
				return false
			}
			return true
		})
	}
	return copyFile(srcPath, filepath.Join(targetBase, filepath.FromSlash(rel)), keepPlaceholders, replacements)
}

func copyTree(srcRoot, dstRoot string, keepPlaceholders bool, replacements map[string]string, include func(rel string, d fs.DirEntry) bool) error {
	return filepath.WalkDir(srcRoot, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(srcRoot, path)
		if err != nil {
			return err
		}
		rel = filepath.ToSlash(rel)
		if rel == "." {
			return nil
		}
		if strings.Contains(rel, "__pycache__") || strings.HasSuffix(rel, ".pyc") {
			if d.IsDir() {
				return fs.SkipDir
			}
			return nil
		}
		if include != nil && !include(rel, d) {
			if d.IsDir() {
				return fs.SkipDir
			}
			return nil
		}
		target := filepath.Join(dstRoot, filepath.FromSlash(rel))
		if d.IsDir() {
			return os.MkdirAll(target, 0o755)
		}
		return copyFile(path, target, keepPlaceholders, replacements)
	})
}

func copyFile(srcPath, dstPath string, keepPlaceholders bool, replacements map[string]string) error {
	data, err := os.ReadFile(srcPath)
	if err != nil {
		return err
	}
	if !keepPlaceholders && isText(data) {
		text := string(data)
		for key, value := range replacements {
			text = strings.ReplaceAll(text, key, value)
		}
		data = []byte(text)
	}
	if err := os.MkdirAll(filepath.Dir(dstPath), 0o755); err != nil {
		return err
	}
	return os.WriteFile(dstPath, data, 0o644)
}

func writeLaunchers(root string) error {
	workspace := resolveWorkspace(root)
	launchers := map[string]string{
		filepath.Join(workspace.BinDir, "timely-playbook"):              timelyPlaybookLauncher(),
		filepath.Join(workspace.BinDir, "chub.sh"):                      launcherShell("exec bash \"$ROOT_DIR/.timely-core/scripts/chub.sh\" \"$@\""),
		filepath.Join(workspace.BinDir, "chub-mcp.sh"):                  launcherShell("exec bash \"$ROOT_DIR/.timely-core/scripts/chub-mcp.sh\" \"$@\""),
		filepath.Join(workspace.BinDir, "bootstrap-timely-template.sh"): launcherShell("exec bash \"$ROOT_DIR/.timely-core/scripts/bootstrap-timely-template.sh\" \"$@\""),
		filepath.Join(workspace.BinDir, "bootstrap-smoke.sh"):           launcherShell("exec bash \"$ROOT_DIR/.timely-core/scripts/bootstrap-smoke.sh\" \"$@\""),
		filepath.Join(workspace.BinDir, "run-markdownlint.sh"):          launcherShell("exec bash \"$ROOT_DIR/.timely-core/scripts/run-markdownlint.sh\" \"$@\""),
		filepath.Join(workspace.BinDir, "check-doc-links.sh"):           launcherShell("exec bash \"$ROOT_DIR/.timely-core/scripts/check-doc-links.sh\" \"$@\""),
		filepath.Join(workspace.BinDir, "install-agent-skill.sh"):       launcherShell("exec bash \"$ROOT_DIR/.timely-core/scripts/install-agent-skill.sh\" \"$@\""),
		filepath.Join(workspace.BinDir, "install-codex-skill.sh"):       launcherShell("exec bash \"$ROOT_DIR/.timely-core/scripts/install-codex-skill.sh\" \"$@\""),
	}
	for path, content := range launchers {
		if err := writeExecutable(path, content); err != nil {
			return err
		}
	}
	return writeExecutable(filepath.Join(workspace.BinDir, "orchestrator.py"), orchestratorLauncher())
}

func timelyPlaybookLauncher() string {
	return strings.TrimSpace(`
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CACHE_DIR="$ROOT_DIR/.timely-playbook/runtime/cache"
BIN_PATH="$CACHE_DIR/timely-playbook"
mkdir -p "$CACHE_DIR"
(cd "$ROOT_DIR/.timely-core/cmd/timely-playbook" && go build -o "$BIN_PATH" .)
exec "$BIN_PATH" "$@"
`) + "\n"
}

func launcherShell(command string) string {
	return strings.TrimSpace(fmt.Sprintf(`
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export TIMELY_REPO_ROOT="${TIMELY_REPO_ROOT:-$ROOT_DIR}"
export TIMELY_CORE_DIR="${TIMELY_CORE_DIR:-$ROOT_DIR/.timely-core}"
export TIMELY_PLAYBOOK_DIR="${TIMELY_PLAYBOOK_DIR:-$ROOT_DIR/.timely-playbook}"
export TIMELY_LOCAL_DIR="${TIMELY_LOCAL_DIR:-$ROOT_DIR/.timely-playbook/local}"
export TIMELY_RUNTIME_DIR="${TIMELY_RUNTIME_DIR:-$ROOT_DIR/.timely-playbook/runtime}"
export TIMELY_CONFIG_PATH="${TIMELY_CONFIG_PATH:-$ROOT_DIR/.timely-playbook/config.yaml}"
export PYTHONPATH="$ROOT_DIR/.timely-core${PYTHONPATH:+:$PYTHONPATH}"

%s
`, command)) + "\n"
}

func orchestratorLauncher() string {
	return strings.TrimSpace(`
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
`) + "\n"
}

func writeExecutable(path, content string) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	if err := os.WriteFile(path, []byte(content), 0o755); err != nil {
		return err
	}
	return os.Chmod(path, 0o755)
}

func rootReadmeContent(root string) (string, error) {
	workspace := resolveWorkspace(root)
	readmePath := filepath.Join(workspace.CoreDir, "README.md")
	data, err := os.ReadFile(readmePath)
	if err != nil {
		if os.IsNotExist(err) {
			return "# Timely Playbook\n\nCanonical content: `.timely-core/README.md`.\n", nil
		}
		return "", err
	}
	return rewriteRootReadmeLinks(string(data)), nil
}

func rewriteRootReadmeLinks(content string) string {
	return markdownLinkPattern.ReplaceAllStringFunc(content, func(match string) string {
		target := markdownLinkPattern.FindStringSubmatch(match)[1]
		rewritten := rewriteRootMarkdownTarget(target)
		return strings.Replace(match, target, rewritten, 1)
	})
}

func rewriteRootMarkdownTarget(target string) string {
	if target == "" || strings.HasPrefix(target, "#") || strings.HasPrefix(target, "/") {
		return target
	}
	if strings.Contains(target, "://") || strings.HasPrefix(target, "mailto:") {
		return target
	}

	pathPart, fragment, hasFragment := strings.Cut(target, "#")
	if strings.HasPrefix(pathPart, "../") {
		return target
	}
	if strings.HasPrefix(pathPart, "./") {
		pathPart = strings.TrimPrefix(pathPart, "./")
	}
	for _, prefix := range []string{".timely-core/", ".timely-playbook/", ".github/", ".vscode/", ".chub/"} {
		if strings.HasPrefix(pathPart, prefix) {
			return target
		}
	}
	if !strings.HasSuffix(pathPart, ".md") {
		return target
	}

	rewritten := filepath.ToSlash(filepath.Join(defaultCoreDirName, filepath.FromSlash(pathPart)))
	if hasFragment {
		return rewritten + "#" + fragment
	}
	return rewritten
}

func writeRootStubs(root string) error {
	rootReadme, err := rootReadmeContent(root)
	if err != nil {
		return err
	}
	stubs := map[string]string{
		filepath.Join(root, "README.md"): rootReadme,
		filepath.Join(root, "AGENTS.md"): "# Timely Playbook governance stub\n\nCanonical content: `.timely-playbook/local/AGENTS.md`.\n",
		filepath.Join(root, "SKILLS.md"): "# Timely Playbook skill registry stub\n\nCanonical content: `.timely-playbook/local/SKILLS.md`.\n",
	}
	for path, content := range stubs {
		if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
			return err
		}
	}
	return nil
}

func writeRootWorkflowDispatchers(source sourceLayout, outputRoot string) error {
	ci := strings.TrimSpace(`
name: CI

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]
  workflow_dispatch:
  schedule:
    - cron: '0 2 * * 0'

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: actions/setup-node@v4
        with:
          node-version: '22.22.0'
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - name: Install Python deps
        run: |
          pip install -r .timely-core/requirements.txt
      - name: Install Timely runtime deps
        run: |
          npm ci --prefix .timely-playbook/runtime
      - name: Run orchestrator status refresh
        run: |
          python .timely-playbook/bin/orchestrator.py update-status
      - name: Validate repository
        run: |
          go test ./.timely-core/cmd/timely-playbook/...
          python -m unittest discover -s .timely-core/tests -p 'test_*.py'
          bash .timely-playbook/bin/chub.sh validate
          bash .timely-playbook/bin/run-markdownlint.sh
          bash .timely-playbook/bin/check-doc-links.sh
      - name: Package template
        run: |
          bash .timely-playbook/bin/timely-playbook package --output dist/timely-template --templated
      - name: Bootstrap smoke test
        run: |
          bash .timely-playbook/bin/bootstrap-smoke.sh --smoke
`) + "\n"

	autofix := strings.TrimSpace(`
name: Agent Autofix

on:
  workflow_run:
    workflows: ["CI"]
    types:
      - completed

jobs:
  autofix:
    if: >-
      github.event.workflow_run.conclusion == 'failure'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          repository: ${{ github.event.workflow_run.head_repository.full_name }}
          ref: ${{ github.event.workflow_run.head_branch }}
      - uses: actions/setup-node@v4
        with:
          node-version: '22.22.0'
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - name: Install tooling
        run: |
          npm ci --prefix .timely-playbook/runtime
          pip install -r .timely-core/requirements.txt
      - name: Attempt configured agent repair
        if: ${{ vars.TIMELY_AUTOFIX_COMMAND != '' }}
        env:
          TIMELY_AUTOFIX_COMMAND: ${{ vars.TIMELY_AUTOFIX_COMMAND }}
        run: |
          bash -lc "$TIMELY_AUTOFIX_COMMAND"
      - name: Attempt Codex repair
        if: ${{ vars.TIMELY_AUTOFIX_COMMAND == '' && (vars.TIMELY_AUTOFIX_PROVIDER == '' || vars.TIMELY_AUTOFIX_PROVIDER == 'codex') }}
        uses: openai/codex-autofix-action@v1
        with:
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          workdir: '.'
          instructions: >-
            CI failed. Read the logs, repair the issue, and open a PR describing
            the fix. Obey ownership rules in .timely-playbook/local/.orchestrator/ownership.yaml.
      - name: Provider hook missing
        if: ${{ vars.TIMELY_AUTOFIX_COMMAND == '' && vars.TIMELY_AUTOFIX_PROVIDER != '' && vars.TIMELY_AUTOFIX_PROVIDER != 'codex' }}
        run: |
          echo "TIMELY_AUTOFIX_PROVIDER='${{ vars.TIMELY_AUTOFIX_PROVIDER }}' is set,"
          echo "but no TIMELY_AUTOFIX_COMMAND repository variable is configured."
          echo "Add a provider-specific repair command or clear TIMELY_AUTOFIX_PROVIDER to use Codex."
          exit 1
`) + "\n"

	for _, item := range []struct {
		path    string
		content string
	}{
		{path: filepath.Join(outputRoot, ".github", "workflows", "ci.yml"), content: ci},
		{path: filepath.Join(outputRoot, ".github", "workflows", "autofix.yml"), content: autofix},
	} {
		if err := os.MkdirAll(filepath.Dir(item.path), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(item.path, []byte(item.content), 0o644); err != nil {
			return err
		}
	}

	_ = source
	return nil
}

func writeRootTaskDispatcher(source sourceLayout, outputRoot string) error {
	sourceTasks := filepath.Join(source.LocalRoot, ".vscode", "tasks.json")
	if !source.Relocated {
		sourceTasks = filepath.Join(source.Root, ".vscode", "tasks.json")
	}
	if !fileExists(sourceTasks) {
		return nil
	}
	data, err := os.ReadFile(sourceTasks)
	if err != nil {
		return err
	}
	text := string(data)
	replacements := map[string]string{
		"python tools/orchestrator/orchestrator.py": "python .timely-playbook/bin/orchestrator.py",
		"bash scripts/chub.sh":                      "bash .timely-playbook/bin/chub.sh",
		"bash scripts/chub-mcp.sh":                  "bash .timely-playbook/bin/chub-mcp.sh",
	}
	for oldValue, newValue := range replacements {
		text = strings.ReplaceAll(text, oldValue, newValue)
	}
	target := filepath.Join(outputRoot, ".vscode", "tasks.json")
	if err := os.MkdirAll(filepath.Dir(target), 0o755); err != nil {
		return err
	}
	return os.WriteFile(target, []byte(text), 0o644)
}

func writeCoreManifest(coreDir, sourceRoot string) error {
	files := map[string]string{}
	err := filepath.WalkDir(coreDir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			return nil
		}
		rel, err := filepath.Rel(coreDir, path)
		if err != nil {
			return err
		}
		rel = filepath.ToSlash(rel)
		if rel == "manifest.json" {
			return nil
		}
		sum, err := sha256File(path)
		if err != nil {
			return err
		}
		files[rel] = sum
		return nil
	})
	if err != nil {
		return err
	}
	manifest := coreManifest{
		SchemaVersion: 1,
		GeneratedAt:   time.Now().UTC().Format(time.RFC3339),
		SourceRoot:    sourceRoot,
		SourceCommit:  gitCommit(sourceRoot),
		Files:         files,
	}
	data, err := json.MarshalIndent(manifest, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(coreDir, "manifest.json"), append(data, '\n'), 0o644)
}

func validateCoreManifest(root string) error {
	workspace := resolveWorkspace(root)
	manifestPath := filepath.Join(workspace.CoreDir, "manifest.json")
	if !fileExists(manifestPath) {
		return nil
	}
	data, err := os.ReadFile(manifestPath)
	if err != nil {
		return err
	}
	var manifest coreManifest
	if err := json.Unmarshal(data, &manifest); err != nil {
		return err
	}
	expected := manifest.Files
	actual := map[string]string{}
	err = filepath.WalkDir(workspace.CoreDir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			return nil
		}
		rel, err := filepath.Rel(workspace.CoreDir, path)
		if err != nil {
			return err
		}
		rel = filepath.ToSlash(rel)
		if rel == "manifest.json" {
			return nil
		}
		if strings.Contains(rel, "__pycache__") || strings.HasSuffix(rel, ".pyc") {
			return nil
		}
		sum, err := sha256File(path)
		if err != nil {
			return err
		}
		actual[rel] = sum
		return nil
	})
	if err != nil {
		return err
	}
	if len(expected) != len(actual) {
		return fmt.Errorf("core manifest drift detected: expected %d files, found %d", len(expected), len(actual))
	}
	for rel, sum := range expected {
		if actual[rel] != sum {
			return fmt.Errorf("core manifest drift detected at %s", rel)
		}
	}
	return nil
}

func sha256File(path string) (string, error) {
	handle, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer handle.Close()

	hash := sha256.New()
	if _, err := io.Copy(hash, handle); err != nil {
		return "", err
	}
	return hex.EncodeToString(hash.Sum(nil)), nil
}

func gitCommit(root string) string {
	if !pathExists(filepath.Join(root, ".git")) {
		return ""
	}
	result := exec.Command("git", "-C", root, "rev-parse", "HEAD")
	output, err := result.Output()
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(output))
}

func handleRefreshCore(root string, args []string) {
	fs := flag.NewFlagSet("refresh-core", flag.ExitOnError)
	source := fs.String("source", "", "local path to a timely-playbook source or package")
	repoURL := fs.String("template-repo", "", "remote timely-playbook repo URL")
	archive := fs.String("archive", "", "path to a packaged timely-playbook archive")
	branch := fs.String("branch", "main", "branch to clone when --template-repo is used")
	if err := fs.Parse(args); err != nil {
		fatal("failed to parse flags", err)
	}

	sourceRoot, cleanup, err := resolveRefreshSource(*source, *repoURL, *archive, *branch)
	if err != nil {
		fatal("could not prepare source", err)
	}
	defer cleanup()

	cfg, cfgErr := readConfig(root)
	if cfgErr != nil {
		cfg = defaultConfig(root)
	}

	if err := refreshCore(root, sourceRoot, cfg); err != nil {
		fatal("refresh-core failed", err)
	}
	fmt.Printf("refreshed Timely core from %s\n", sourceRoot)
}

func resolveRefreshSource(source, repoURL, archivePath, branch string) (string, func(), error) {
	count := 0
	for _, value := range []string{source, repoURL, archivePath} {
		if strings.TrimSpace(value) != "" {
			count++
		}
	}
	if count != 1 {
		return "", func() {}, fmt.Errorf("provide exactly one of --source, --template-repo, or --archive")
	}
	if source != "" {
		return cleanAbsPath(source), func() {}, nil
	}
	if repoURL != "" {
		tmpDir, err := os.MkdirTemp("", "timely-refresh-*")
		if err != nil {
			return "", func() {}, err
		}
		target := filepath.Join(tmpDir, "timely-playbook")
		cmd := exec.Command("git", "clone", "--depth", "1", "--branch", branch, repoURL, target)
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		if err := cmd.Run(); err != nil {
			_ = os.RemoveAll(tmpDir)
			return "", func() {}, err
		}
		return target, func() { _ = os.RemoveAll(tmpDir) }, nil
	}
	tmpDir, err := os.MkdirTemp("", "timely-archive-*")
	if err != nil {
		return "", func() {}, err
	}
	extractedRoot, err := extractArchive(archivePath, tmpDir)
	if err != nil {
		_ = os.RemoveAll(tmpDir)
		return "", func() {}, err
	}
	return extractedRoot, func() { _ = os.RemoveAll(tmpDir) }, nil
}

func extractArchive(archivePath, targetDir string) (string, error) {
	file, err := os.Open(archivePath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	gzipReader, err := gzip.NewReader(file)
	if err != nil {
		return "", err
	}
	defer gzipReader.Close()

	tarReader := tar.NewReader(gzipReader)
	var topLevel string
	for {
		header, err := tarReader.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return "", err
		}
		targetPath := filepath.Join(targetDir, header.Name)
		cleanTarget := filepath.Clean(targetPath)
		if !strings.HasPrefix(cleanTarget, filepath.Clean(targetDir)+string(filepath.Separator)) && filepath.Clean(cleanTarget) != filepath.Clean(targetDir) {
			return "", fmt.Errorf("archive entry escapes target directory: %s", header.Name)
		}
		if topLevel == "" {
			parts := strings.Split(filepath.ToSlash(header.Name), "/")
			if len(parts) > 0 {
				topLevel = parts[0]
			}
		}
		switch header.Typeflag {
		case tar.TypeDir:
			if err := os.MkdirAll(cleanTarget, 0o755); err != nil {
				return "", err
			}
		case tar.TypeReg:
			if err := os.MkdirAll(filepath.Dir(cleanTarget), 0o755); err != nil {
				return "", err
			}
			output, err := os.OpenFile(cleanTarget, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, fs.FileMode(header.Mode))
			if err != nil {
				return "", err
			}
			if _, err := io.Copy(output, tarReader); err != nil {
				_ = output.Close()
				return "", err
			}
			if err := output.Close(); err != nil {
				return "", err
			}
		}
	}
	root := targetDir
	if topLevel != "" && pathExists(filepath.Join(targetDir, topLevel)) {
		root = filepath.Join(targetDir, topLevel)
	}
	return root, nil
}

func refreshCore(root, sourceRoot string, cfg playbookConfig) error {
	source, err := normalizeSourceLayout(sourceRoot)
	if err != nil {
		return err
	}
	workspace := resolveWorkspace(root)
	cfg = configForEmission(root, cfg)
	replacements := placeholderReplacements(cfg)

	for _, path := range []string{workspace.CoreDir, workspace.RuntimeDir, workspace.BinDir, filepath.Join(root, ".github"), filepath.Join(root, ".vscode"), filepath.Join(root, "README.md"), filepath.Join(root, "AGENTS.md"), filepath.Join(root, "SKILLS.md")} {
		if err := os.RemoveAll(path); err != nil {
			return err
		}
	}

	if err := os.MkdirAll(workspace.LocalDir, 0o755); err != nil {
		return err
	}
	if err := copyCoreSnapshot(source, workspace.CoreDir, ".", false, false, replacements); err != nil {
		return err
	}
	if err := copyRuntimeFiles(source, workspace.RuntimeDir, false, replacements); err != nil {
		return err
	}
	if err := writeLaunchers(root); err != nil {
		return err
	}
	if err := writeRootStubs(root); err != nil {
		return err
	}
	if err := writeRootWorkflowDispatchers(source, root); err != nil {
		return err
	}
	if err := writeRootTaskDispatcher(source, root); err != nil {
		return err
	}
	if err := writeConfig(workspace.ConfigPath, cfg); err != nil {
		return err
	}
	return writeCoreManifest(workspace.CoreDir, source.Root)
}

func handleMigrateLayout(root string, args []string) {
	fs := flag.NewFlagSet("migrate-layout", flag.ExitOnError)
	force := fs.Bool("force", false, "allow migration when the destination already has relocated Timely directories")
	if err := fs.Parse(args); err != nil {
		fatal("failed to parse flags", err)
	}

	workspace := resolveWorkspace(root)
	if (pathExists(workspace.CoreDir) || pathExists(workspace.TimelyDir)) && !*force {
		fatal("destination already contains relocated Timely directories; rerun with --force to rebuild them", nil)
	}

	cfg, cfgErr := readConfig(root)
	if cfgErr != nil {
		cfg = legacyDefaultConfig(root)
	}
	if err := migrateLayout(root, cfg); err != nil {
		fatal("migrate-layout failed", err)
	}
	fmt.Printf("migrated Timely layout under %s and %s\n", workspace.CoreDir, workspace.TimelyDir)
}

func migrateLayout(root string, cfg playbookConfig) error {
	workspace := resolveWorkspace(root)
	backupRoot := filepath.Join(workspace.BackupDir, time.Now().UTC().Format("20060102-150405"))
	if err := os.MkdirAll(backupRoot, 0o755); err != nil {
		return err
	}

	backupPaths := []string{
		"AGENTS.md",
		"SKILLS.md",
		".orchestrator",
		".github",
		".vscode",
		"timely-trackers",
		"skills",
		"scripts",
		"tools",
		"package.json",
		"package-lock.json",
		".node-version",
		".nvmrc",
		legacyConfigFileName,
	}
	for _, rel := range backupPaths {
		src := filepath.Join(root, filepath.FromSlash(rel))
		if !pathExists(src) {
			continue
		}
		if err := copySelectedPath(root, backupRoot, rel, true, nil); err != nil {
			return err
		}
	}

	if err := refreshCore(root, root, cfg); err != nil {
		return err
	}
	if err := os.RemoveAll(workspace.LocalDir); err != nil {
		return err
	}
	if err := copyEditableLocal(sourceLayout{Root: backupRoot, LocalRoot: backupRoot}, workspace.LocalDir, false, placeholderReplacements(configForEmission(root, cfg))); err != nil {
		return err
	}
	if err := writeConfig(workspace.ConfigPath, configForEmission(root, cfg)); err != nil {
		return err
	}

	removePaths := []string{
		filepath.Join(root, ".orchestrator"),
		filepath.Join(root, "scripts"),
		filepath.Join(root, "tools"),
		filepath.Join(root, "package.json"),
		filepath.Join(root, "package-lock.json"),
		filepath.Join(root, ".node-version"),
		filepath.Join(root, ".nvmrc"),
		filepath.Join(root, legacyConfigFileName),
	}
	for _, path := range removePaths {
		if err := os.RemoveAll(path); err != nil {
			return err
		}
	}
	return nil
}

func sortedKeys(values map[string]string) []string {
	keys := make([]string, 0, len(values))
	for key := range values {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	return keys
}
