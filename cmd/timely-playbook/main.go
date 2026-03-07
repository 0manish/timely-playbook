package main

import (
	"flag"
	"fmt"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"gopkg.in/yaml.v3"
)

const configFileName = "timely-playbook.yaml"

var commandRegistry = []string{
	"help",
	"init-config",
	"package",
	"append",
	"run-weekly",
	"remind",
	"seed",
}

func printUsage() {
	fmt.Println("usage: timely-playbook <command> [args]")
	fmt.Println("commands:")
	for _, command := range commandRegistry {
		fmt.Println("  -", command)
	}
}

type playbookConfig struct {
	OwnerName           string `yaml:"owner_name"`
	OwnerEmail          string `yaml:"owner_email"`
	RepoName            string `yaml:"repo_name"`
	DocsDir             string `yaml:"docs_dir"`
	LogDir              string `yaml:"log_dir"`
	JournalPath         string `yaml:"journal_path"`
	LedgerPath          string `yaml:"ledger_path"`
	BacklogPath         string `yaml:"backlog_path"`
	CeremonyAgendasPath string `yaml:"ceremony_agendas_path"`
}

func main() {
	root, err := os.Getwd()
	if err != nil {
		fatal("could not determine working directory", err)
	}

	if len(os.Args) < 2 {
		printUsage()
		return
	}

	switch os.Args[1] {
	case "help", "-h", "--help":
		printUsage()
		return
	case "init-config":
		handleInitConfig(root, os.Args[2:])
	case "package":
		handlePackage(root, os.Args[2:])
	case "append":
		handleAppend(root, os.Args[2:])
	case "run-weekly":
		handleRunWeekly(root, os.Args[2:])
	case "remind":
		handleRemind(root, os.Args[2:])
	case "seed":
		handleSeed(root, os.Args[2:])
	default:
		fmt.Printf("unknown command: %s\n", os.Args[1])
		fmt.Println("known commands:", strings.Join(commandRegistry, ", "))
		os.Exit(1)
	}
}

func handleInitConfig(root string, args []string) {
	fs := flag.NewFlagSet("init-config", flag.ExitOnError)
	owner := fs.String("owner", "{{OWNER_NAME}}", "owner name to stamp into template snapshots")
	email := fs.String("email", "{{OWNER_EMAIL}}", "owner email to stamp into template snapshots")
	repo := fs.String("repo", filepath.Base(root), "repo name to stamp into template snapshots")
	docsDir := fs.String("docs-dir", ".", "docs directory root relative to repo")
	logDir := fs.String("log-dir", "run-logs", "run-logs output directory")
	journal := fs.String("journal-path", "timely-trackers/test-run-journal.md", "journal file path")
	ledger := fs.String("ledger-path", "timely-trackers/agent-control-ledger.md", "ledger file path")
	backlog := fs.String("backlog-path", "timely-trackers/todo-backlog.md", "backlog file path")
	agendas := fs.String("ceremony-agendas", "timely-trackers/ceremony-agendas.md", "ceremony agendas path")
	if err := fs.Parse(args); err != nil {
		fatal("failed to parse flags", err)
	}

	cfg := playbookConfig{
		OwnerName:           *owner,
		OwnerEmail:          *email,
		RepoName:            *repo,
		DocsDir:             *docsDir,
		LogDir:              *logDir,
		JournalPath:         *journal,
		LedgerPath:          *ledger,
		BacklogPath:         *backlog,
		CeremonyAgendasPath: *agendas,
	}

	path := filepath.Join(root, configFileName)
	if err := writeConfig(path, cfg); err != nil {
		fatal("could not write config", err)
	}

	fmt.Println("wrote", path)
}

func handlePackage(root string, args []string) {
	fs := flag.NewFlagSet("package", flag.ExitOnError)
	output := fs.String("output", "dist/timely-template", "output path for the template bundle")
	templated := fs.Bool("templated", false, "keep placeholders like {{OWNER_NAME}} in exported files")
	includeLogs := fs.Bool("include-logs", false, "include run-logs/ in template output")
	if err := fs.Parse(args); err != nil {
		fatal("failed to parse flags", err)
	}

	root, err := filepath.Abs(root)
	if err != nil {
		fatal("could not resolve root", err)
	}

	cfg, cfgErr := readConfig(root)
	if cfgErr != nil {
		cfg = defaultConfig(root)
		if !*templated {
			fmt.Println("warning: could not read config, placeholder values will be injected as defaults")
		}
	}

	if *output == "" {
		fatal("--output must be provided", nil)
	}
	absOutput := *output
	if !filepath.IsAbs(absOutput) {
		absOutput = filepath.Join(root, absOutput)
	}
	absOutput = filepath.Clean(absOutput)
	relOutput := "dist/timely-template"
	if filepath.IsAbs(*output) {
		relOutput, _ = filepath.Rel(root, *output)
		relOutput = filepath.ToSlash(relOutput)
	} else {
		relOutput = *output
	}
	emit := "inject"
	if *templated {
		emit = "keep placeholders"
	}

	if err := packageTemplate(root, absOutput, relOutput, *templated, *includeLogs, cfg); err != nil {
		fatal("package failed", err)
	}

	fmt.Printf("packaged template bundle to %s (%s)\n", absOutput, emit)
}

func handleSeed(root string, args []string) {
	fs := flag.NewFlagSet("seed", flag.ExitOnError)
	output := fs.String("output", "", "destination path for the new repository")
	templated := fs.Bool("templated", true, "keep placeholders like {{OWNER_NAME}} in seeded files")
	includeLogs := fs.Bool("include-logs", false, "include run-logs/ in template output")
	allowExisting := fs.Bool("allow-existing", false, "overwrite an existing destination directory")
	initGit := fs.Bool("init-git", false, "run `git init` in the seeded directory")
	owner := fs.String("owner", "", "owner name to stamp into generated timely-playbook.yaml")
	email := fs.String("email", "", "owner email to stamp into generated timely-playbook.yaml")
	repo := fs.String("repo", "", "repo name to stamp into generated timely-playbook.yaml")
	if err := fs.Parse(args); err != nil {
		fatal("failed to parse flags", err)
	}

	if *output == "" {
		fatal("--output is required", nil)
	}

	cfg, cfgErr := readConfig(root)
	if cfgErr != nil {
		cfg = defaultConfig(root)
	}
	if *owner != "" {
		cfg.OwnerName = *owner
	}
	if *email != "" {
		cfg.OwnerEmail = *email
	}
	if *repo != "" {
		cfg.RepoName = *repo
	}

	absOutput := *output
	if !filepath.IsAbs(absOutput) {
		absOutput = filepath.Join(root, absOutput)
	}

	if !*allowExisting {
		if info, err := os.Stat(absOutput); err == nil && info.IsDir() {
			children, err := os.ReadDir(absOutput)
			if err != nil {
				fatal("could not inspect destination directory", err)
			}
			if len(children) > 0 {
				fatal("destination already exists and is not empty; use --allow-existing", nil)
			}
		}
	}

	relOutput := "dist/timely-template"
	if filepath.IsAbs(*output) {
		relOutput, _ = filepath.Rel(root, *output)
		relOutput = filepath.ToSlash(relOutput)
	} else {
		relOutput = *output
	}

	if err := packageTemplate(root, absOutput, relOutput, *templated, *includeLogs, cfg); err != nil {
		fatal("seed failed", err)
	}

	if err := writeConfig(filepath.Join(absOutput, configFileName), cfg); err != nil {
		fatal("could not write seeded config", err)
	}

	if *initGit {
		git := exec.Command("git", "-C", absOutput, "init")
		git.Stdout = os.Stdout
		git.Stderr = os.Stderr
		if err := git.Run(); err != nil {
			fatal("failed to run git init", err)
		}
	}

	fmt.Printf("seeded repository at %s (templated=%t)\n", absOutput, *templated)
}

func handleAppend(root string, args []string) {
	if len(args) < 1 {
		fmt.Println("usage: timely-playbook append <journal|ledger|backlog> [flags]")
		os.Exit(1)
	}

	cfg, cfgErr := readConfig(root)
	if cfgErr != nil {
		cfg = defaultConfig(root)
	}

	switch args[0] {
	case "journal":
		fs := flag.NewFlagSet("append journal", flag.ExitOnError)
		runID := fs.String("run-id", "", "run identifier")
		trigger := fs.String("trigger", "Manual", "run trigger")
		scope := fs.String("scope", "", "validation scope")
		commands := fs.String("commands", "", "commands run")
		result := fs.String("result", "Pass", "Pass|Fail")
		evidence := fs.String("evidence", "", "evidence paths")
		if err := fs.Parse(args[1:]); err != nil {
			fatal("failed to parse flags", err)
		}

		if *runID == "" {
			fatal("--run-id is required", nil)
		}

		row := []string{
			*runID,
			time.Now().Format("2006-01-02"),
			*trigger,
			*scope,
			*commands,
			*result,
			*evidence,
		}

		header := []string{"Run ID", "Date", "Trigger", "Scope", "Command(s)", "Result", "Evidence"}
		if err := appendMarkdownRow(filepath.Join(root, cfg.JournalPath), header, row); err != nil {
			fatal("failed to append journal entry", err)
		}
		fmt.Println("appended journal entry")

	case "ledger":
		fs := flag.NewFlagSet("append ledger", flag.ExitOnError)
		date := fs.String("date", time.Now().Format("2006-01-02"), "entry date")
		decision := fs.String("decision", "", "decision summary")
		context := fs.String("context", "", "context / link")
		owner := fs.String("owner", cfg.OwnerName, "decision owner")
		if err := fs.Parse(args[1:]); err != nil {
			fatal("failed to parse flags", err)
		}

		if *decision == "" {
			fatal("--decision is required", nil)
		}

		row := []string{*date, *decision, *context, *owner}
		header := []string{"Date", "Decision", "Context / Link", "Owner"}
		if err := appendMarkdownRow(filepath.Join(root, cfg.LedgerPath), header, row); err != nil {
			fatal("failed to append ledger entry", err)
		}
		fmt.Println("appended ledger entry")

	case "backlog":
		fs := flag.NewFlagSet("append backlog", flag.ExitOnError)
		priority := fs.String("priority", "Medium", "priority")
		item := fs.String("item", "", "backlog item")
		context := fs.String("context", "", "context / link")
		owner := fs.String("owner", cfg.OwnerName, "item owner")
		due := fs.String("due", "", "due date")
		status := fs.String("status", "Todo", "status")
		if err := fs.Parse(args[1:]); err != nil {
			fatal("failed to parse flags", err)
		}

		if *item == "" {
			fatal("--item is required", nil)
		}

		row := []string{*priority, *item, *context, *owner, *due, *status}
		header := []string{"Priority", "Item", "Context / Link", "Owner", "Due Date", "Status"}
		if err := appendMarkdownRow(filepath.Join(root, cfg.BacklogPath), header, row); err != nil {
			fatal("failed to append backlog entry", err)
		}
		fmt.Println("appended backlog item")
	default:
		fmt.Println("usage: timely-playbook append <journal|ledger|backlog> [flags]")
		os.Exit(1)
	}
}

func handleRunWeekly(root string, args []string) {
	fs := flag.NewFlagSet("run-weekly", flag.ExitOnError)
	dryRun := fs.Bool("dry-run", false, "print summary without writing files")
	if err := fs.Parse(args); err != nil {
		fatal("failed to parse flags", err)
	}

	cfg, cfgErr := readConfig(root)
	if cfgErr != nil {
		cfg = defaultConfig(root)
	}

	journalPath := filepath.Join(root, cfg.JournalPath)
	ledgerPath := filepath.Join(root, cfg.LedgerPath)
	backlogPath := filepath.Join(root, cfg.BacklogPath)

	ledgerItems, ledgerErr := countTableRows(ledgerPath)
	backlogItems, backlogErr := countTableRows(backlogPath)
	backlogOpen, backlogDue := 0, 0
	if backlogErr == nil {
		backlogRows := extractTableRows(backlogPath)
		for _, row := range backlogRows {
			if len(row) < 6 {
				continue
			}
			if row[5] != "Done" {
				backlogOpen++
			}
			if row[4] != "" {
				backlogDue++
			}
		}
	}

	lines := []string{
		"# Weekly status",
		"",
		fmt.Sprintf("- Date: %s", time.Now().Format("2006-01-02")),
		fmt.Sprintf("- Ledger items: %d", ledgerItems),
		fmt.Sprintf("- Backlog items: %d (open: %d)", backlogItems, backlogOpen),
	}
	if backlogDue > 0 {
		lines = append(lines, fmt.Sprintf("- Backlog items with due date: %d", backlogDue))
	}

	if *dryRun {
		fmt.Println(strings.Join(lines, "\n"))
		return
	}

	summaryPath := filepath.Join(root, cfg.LogDir, time.Now().Format("20060102"), "summary.md")
	if err := os.MkdirAll(filepath.Dir(summaryPath), 0o755); err != nil {
		fatal("could not create log directory", err)
	}
	if err := os.WriteFile(summaryPath, []byte(strings.Join(lines, "\n")+"\n"), 0o644); err != nil {
		fatal("could not write weekly summary", err)
	}

	scope := fmt.Sprintf("run-weekly snapshot (ledger=%d backlog=%d)", ledgerItems, backlogItems)
	journalRow := []string{
		time.Now().Format("2006-01-02"),
		time.Now().Format("2006-01-02"),
		"Manual",
		scope,
		"timely-playbook run-weekly",
		"Pass",
		summaryPath,
	}
	journalHeader := []string{"Run ID", "Date", "Trigger", "Scope", "Command(s)", "Result", "Evidence"}
	if err := appendMarkdownRow(journalPath, journalHeader, journalRow); err != nil {
		fatal("could not write weekly journal entry", err)
	}

	_ = ledgerErr
	_ = backlogErr
	fmt.Printf("wrote weekly summary to %s\n", summaryPath)
	fmt.Println("appended run-weekly entry to", journalPath)
}

func handleRemind(root string, args []string) {
	if len(args) > 0 {
		_ = args
	}
	cfg, cfgErr := readConfig(root)
	if cfgErr != nil {
		cfg = defaultConfig(root)
	}

	agendaPath := filepath.Join(root, cfg.CeremonyAgendasPath)
	data, err := os.ReadFile(agendaPath)
	if err != nil {
		if os.IsNotExist(err) {
			fmt.Printf("ceremony agendas not found at %s\n", cfg.CeremonyAgendasPath)
			return
		}
		fatal("could not read ceremony agenda", err)
	}
	fmt.Println(string(data))
}

func packageTemplate(root, output, relOutput string, keepPlaceholders, includeLogs bool, cfg playbookConfig) error {
	if strings.HasSuffix(output, string(filepath.Separator)) {
		output = strings.TrimRight(output, string(filepath.Separator))
	}
	root = filepath.Clean(root)
	output = filepath.Clean(output)

	if err := os.RemoveAll(output); err != nil {
		return err
	}
	if err := os.MkdirAll(output, 0o755); err != nil {
		return err
	}

	exclude := map[string]struct{}{
		".git":                   {},
		".chub":                  {},
		"dist":                   {},
		".orchestrator/upstream": {},
		".bin":                   {},
		"fullstack-projects":     {},
		"node_modules":           {},
		"vendor":                 {},
		"cmd/dist":               {},
	}
	if !includeLogs && cfg.LogDir != "" {
		exclude[cfg.LogDir] = struct{}{}
	}

	replacements := map[string]string{
		"{{OWNER_NAME}}":            cfg.OwnerName,
		"{{OWNER_EMAIL}}":           cfg.OwnerEmail,
		"{{REPO_NAME}}":             cfg.RepoName,
		"{{DOCS_DIR}}":              cfg.DocsDir,
		"{{LOG_DIR}}":               cfg.LogDir,
		"{{JOURNAL_PATH}}":          cfg.JournalPath,
		"{{LEDGER_PATH}}":           cfg.LedgerPath,
		"{{BACKLOG_PATH}}":          cfg.BacklogPath,
		"{{CEREMONY_AGENDAS_PATH}}": cfg.CeremonyAgendasPath,
	}
	if keepPlaceholders {
		replacements = map[string]string{}
	}

	currentDir, wdErr := os.Getwd()
	if wdErr != nil {
		return wdErr
	}
	if err := os.Chdir(root); err != nil {
		return err
	}
	defer func() {
		_ = os.Chdir(currentDir)
	}()

	return filepath.WalkDir(".", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if path == "." {
			return nil
		}
		cleanPath := filepath.Clean(path)
		if cleanPath == "." {
			return nil
		}
		absPath := filepath.Join(root, cleanPath)
		if absPath == output || strings.HasPrefix(absPath+string(filepath.Separator), output+string(filepath.Separator)) {
			if d.IsDir() {
				return fs.SkipDir
			}
			return nil
		}

		rel := filepath.ToSlash(cleanPath)
		if rel == ".." || strings.HasPrefix(rel, "../") {
			return nil
		}

		if shouldSkip(rel, relOutput, exclude) {
			if d.IsDir() {
				return fs.SkipDir
			}
			return nil
		}

		target := filepath.Join(output, rel)
		if d.IsDir() {
			return os.MkdirAll(target, 0o755)
		}

		data, readErr := os.ReadFile(absPath)
		if readErr != nil {
			return readErr
		}
		if !keepPlaceholders {
			if isText(data) {
				text := string(data)
				for k, v := range replacements {
					text = strings.ReplaceAll(text, k, v)
				}
				data = []byte(text)
			}
		}

		if err := os.MkdirAll(filepath.Dir(target), 0o755); err != nil {
			return err
		}
		return os.WriteFile(target, data, 0o644)
	})
}

func shouldSkip(rel, relOutput string, exclude map[string]struct{}) bool {
	norm := filepath.ToSlash(rel)
	if relOutput != "." && (norm == relOutput || strings.HasPrefix(norm, relOutput+"/")) {
		return true
	}
	if strings.HasPrefix(norm, "cmd/timely-playbook") {
		return false
	}
	parts := strings.Split(norm, "/")
	if len(parts) > 0 {
		if _, ok := exclude[parts[0]]; ok {
			return true
		}
		// For nested entries under a known excluded top directory.
		for i := 1; i < len(parts); i++ {
			if _, ok := exclude[strings.Join(parts[:i+1], "/")]; ok {
				return true
			}
		}
	}
	return false
}

func isText(data []byte) bool {
	if len(data) == 0 {
		return true
	}
	if len(data) > 1024*128 {
		data = data[:1024*128]
	}
	for _, b := range data {
		if b == 0 {
			return false
		}
		if b < 9 || b == 11 || b == 12 || (b > 13 && b < 32) {
			return false
		}
	}
	return true
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

func readConfig(root string) (playbookConfig, error) {
	path := filepath.Join(root, configFileName)
	data, err := os.ReadFile(path)
	if err != nil {
		return playbookConfig{}, err
	}

	var cfg playbookConfig
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return playbookConfig{}, err
	}
	if cfg.RepoName == "" {
		cfg.RepoName = filepath.Base(root)
	}
	if cfg.DocsDir == "" {
		cfg.DocsDir = "."
	}
	if cfg.LogDir == "" {
		cfg.LogDir = "run-logs"
	}
	if cfg.JournalPath == "" {
		cfg.JournalPath = "timely-trackers/test-run-journal.md"
	}
	if cfg.LedgerPath == "" {
		cfg.LedgerPath = "timely-trackers/agent-control-ledger.md"
	}
	if cfg.BacklogPath == "" {
		cfg.BacklogPath = "timely-trackers/todo-backlog.md"
	}
	if cfg.CeremonyAgendasPath == "" {
		cfg.CeremonyAgendasPath = "timely-trackers/ceremony-agendas.md"
	}
	return cfg, nil
}

func defaultConfig(root string) playbookConfig {
	return playbookConfig{
		OwnerName:           "{{OWNER_NAME}}",
		OwnerEmail:          "{{OWNER_EMAIL}}",
		RepoName:            filepath.Base(root),
		DocsDir:             ".",
		LogDir:              "run-logs",
		JournalPath:         "timely-trackers/test-run-journal.md",
		LedgerPath:          "timely-trackers/agent-control-ledger.md",
		BacklogPath:         "timely-trackers/todo-backlog.md",
		CeremonyAgendasPath: "timely-trackers/ceremony-agendas.md",
	}
}

func appendMarkdownRow(path string, headers, row []string) error {
	if len(headers) == 0 {
		return fmt.Errorf("header row is required")
	}
	if len(row) != len(headers) {
		if len(row) < len(headers) {
			pad := make([]string, len(headers)-len(row))
			row = append(row, pad...)
		} else {
			row = row[:len(headers)]
		}
	}

	escaped := make([]string, len(row))
	for i, item := range row {
		escaped[i] = strings.ReplaceAll(item, "|", "\\|")
	}

	newRow := rowToMarkdown(escaped)

	existing, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return os.WriteFile(path, []byte(strings.Join([]string{rowToMarkdown(headers), tableSeparator(len(headers)), newRow, ""}, "\n")+"\n"), 0o644)
		}
		return err
	}

	lines := strings.Split(string(existing), "\n")
	sep := -1
	for i, l := range lines {
		if !strings.HasPrefix(strings.TrimSpace(l), "|") {
			continue
		}
		if !isTableSeparator(i+1, lines) {
			continue
		}
		sep = i + 1
		break
	}
	if sep == -1 {
		aug := append([]string{rowToMarkdown(headers), tableSeparator(len(headers)), newRow, ""}, lines...)
		return os.WriteFile(path, []byte(strings.Join(aug, "\n")), 0o644)
	}

	insertAt := sep + 1
	for insertAt < len(lines) && isMarkdownRow(lines[insertAt]) {
		insertAt++
	}
	result := make([]string, 0, len(lines)+1)
	result = append(result, lines[:insertAt]...)
	result = append(result, newRow)
	result = append(result, lines[insertAt:]...)

	return os.WriteFile(path, []byte(strings.Join(result, "\n")), 0o644)
}

func tableSeparator(columns int) string {
	parts := make([]string, columns)
	for i := range parts {
		parts[i] = " --- "
	}
	return rowToMarkdown(parts)
}

func rowToMarkdown(values []string) string {
	return "| " + strings.Join(values, " | ") + " |"
}

func isTableSeparator(idx int, lines []string) bool {
	if idx >= len(lines) {
		return false
	}
	line := strings.TrimSpace(lines[idx])
	if !strings.HasPrefix(line, "|") {
		return false
	}
	return strings.Contains(line, "---")
}

func isMarkdownRow(line string) bool {
	trim := strings.TrimSpace(line)
	if trim == "" {
		return false
	}
	return strings.HasPrefix(trim, "|") && strings.HasSuffix(trim, "|")
}

func countTableRows(path string) (int, error) {
	rows := extractTableRows(path)
	return len(rows), nil
}

func extractTableRows(path string) [][]string {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil
	}
	lines := strings.Split(string(data), "\n")
	start := -1
	for i := 0; i < len(lines)-1; i++ {
		if strings.HasPrefix(strings.TrimSpace(lines[i]), "|") && isTableSeparator(i+1, lines) {
			start = i + 2
			break
		}
	}
	if start == -1 {
		return nil
	}
	var out [][]string
	for i := start; i < len(lines); i++ {
		line := strings.TrimSpace(lines[i])
		if !isMarkdownRow(line) {
			break
		}
		cells := parseRow(line)
		out = append(out, cells)
	}
	return out
}

func parseRow(line string) []string {
	line = strings.TrimSpace(line)
	if strings.HasPrefix(line, "|") {
		line = strings.TrimPrefix(line, "|")
	}
	if strings.HasSuffix(line, "|") {
		line = strings.TrimSuffix(line, "|")
	}
	parts := strings.Split(line, "|")
	for i, p := range parts {
		parts[i] = strings.TrimSpace(strings.Trim(p, "\\"))
	}
	return parts
}

func fatal(message string, err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, message+":", err)
	} else {
		fmt.Fprintln(os.Stderr, message)
	}
	os.Exit(1)
}
