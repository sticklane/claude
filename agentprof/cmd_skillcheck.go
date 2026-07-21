package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/sticklane/agentprof/internal/claude"
	"github.com/sticklane/agentprof/internal/judge"
)

// triggerAgg holds one skill's trigger/population counts (R10).
type triggerAgg struct {
	Correct            int `json:"correct"`
	Misfired           int `json:"misfired"`
	Unresolvable       int `json:"unresolvable"`
	ExplicitInvocation int `json:"explicit_invocation"`
	SelfChained        int `json:"self_chained"`
	PossibleMisses     int `json:"possible_misses"`
}

// outcomeAgg holds one skill's outcome counts (R10).
type outcomeAgg struct {
	Success int `json:"success"`
	Failure int `json:"failure"`
	Unknown int `json:"unknown"`
}

// finding is one non-obvious per-invocation verdict with a transcript citation
// (R10): every verdict other than `correct`/`success` carries one.
type finding struct {
	Session       string `json:"session"`
	Verdict       string `json:"verdict"`
	Evidence      string `json:"evidence"`
	TranscriptRef string `json:"transcript_ref"`
}

// skillReport is one skill's aggregate report, grouped per the Report shape.
type skillReport struct {
	Skill       string     `json:"skill"`
	Invocations int        `json:"invocations"`
	Trigger     triggerAgg `json:"trigger"`
	Outcome     outcomeAgg `json:"outcome"`
	Findings    []finding  `json:"findings"`
}

// cmdSkillcheck runs `agentprof skillcheck` (R1): it walks Claude Code
// transcripts, classifies each Skill invocation's trigger and (for
// correctly-triggered ones) outcome, flags possible misses, and emits a
// per-skill report as JSON (default) or a table.
func cmdSkillcheck(args []string, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("skillcheck", flag.ContinueOnError)
	fs.SetOutput(stderr)
	fs.Usage = func() { skillcheckUsage(stderr) }
	claudeDir := fs.String("claude-dir", defaultClaudeDir(), "Claude Code data directory")
	days := fs.Int("days", 30, "include sessions active within the last N days")
	since := fs.String("since", "", "absolute RFC3339 cutoff (mutually exclusive with an explicit --days)")
	skill := fs.String("skill", "", "restrict the report to a single skill by name")
	judgeTier := fs.String("judge-tier", "scout", "outcome judge tier: scout|deep|frontier (session is rejected — a fresh subprocess has no model to inherit)")
	out := fs.String("o", "", "output path (default stdout)")
	format := fs.String("format", "json", "output format: json (default) or table")
	if err := fs.Parse(args); err != nil {
		return 2
	}

	daysExplicit := false
	fs.Visit(func(f *flag.Flag) {
		if f.Name == "days" {
			daysExplicit = true
		}
	})
	cutoff := time.Now().AddDate(0, 0, -*days)
	if *since != "" {
		if daysExplicit {
			fmt.Fprintln(stderr, "agentprof skillcheck: --since and --days are mutually exclusive")
			return 2
		}
		t, err := time.Parse(time.RFC3339, *since)
		if err != nil {
			fmt.Fprintf(stderr, "agentprof skillcheck: invalid --since %q: %v\n", *since, err)
			return 2
		}
		cutoff = t
	}
	if *format != "json" && *format != "table" {
		fmt.Fprintf(stderr, "agentprof skillcheck: unknown --format %q (want json or table)\n", *format)
		return 2
	}
	outcomeModel, err := resolveJudgeTierToModel(*judgeTier)
	if err != nil {
		fmt.Fprintf(stderr, "agentprof skillcheck: %v\n", err)
		return 2
	}

	cwd, err := os.Getwd()
	if err != nil {
		fmt.Fprintf(stderr, "agentprof skillcheck: %v\n", err)
		return 1
	}
	r := Resolver{Cwd: cwd, PluginCacheRoot: defaultPluginCacheRoot()}
	j := newSkillcheckJudge(defaultJudgeScratchRoot())

	reports, err := runSkillcheck(*claudeDir, cutoff, *skill, outcomeModel, r, j)
	if err != nil {
		fmt.Fprintf(stderr, "agentprof skillcheck: %v\n", err)
		return 1
	}

	var rendered []byte
	if *format == "table" {
		rendered = []byte(renderReportsTable(reports))
	} else {
		rendered, err = renderReportsJSON(reports)
		if err != nil {
			fmt.Fprintf(stderr, "agentprof skillcheck: %v\n", err)
			return 1
		}
		rendered = append(rendered, '\n')
	}
	if *out == "" || *out == "-" {
		if _, err := stdout.Write(rendered); err != nil {
			fmt.Fprintf(stderr, "agentprof skillcheck: %v\n", err)
			return 1
		}
		return 0
	}
	if err := os.WriteFile(*out, rendered, 0o644); err != nil {
		fmt.Fprintf(stderr, "agentprof skillcheck: %v\n", err)
		return 1
	}
	return 0
}

// runSkillcheck is the testable core: it scans every in-window transcript under
// claudeDir, wires task 01's SkillInvocations → task 02's trigger
// classification → (for correctly-triggered invocations only) task 03's outcome
// classification, and assembles the per-skill report. skillFilter (when
// non-empty) restricts the result to one skill. outcomeModel is the concrete
// judge model for outcome scoring (trigger scoring uses its own deep tier).
func runSkillcheck(claudeDir string, cutoff time.Time, skillFilter, outcomeModel string, r Resolver, j judge.Judge) ([]skillReport, error) {
	userTurns, err := userTurnsBySession(claudeDir, cutoff)
	if err != nil {
		return nil, err
	}
	paths, err := transcriptPaths(claudeDir, cutoff)
	if err != nil {
		return nil, err
	}

	aggs := map[string]*skillReport{}
	agg := func(name string) *skillReport {
		if aggs[name] == nil {
			aggs[name] = &skillReport{Skill: name}
		}
		return aggs[name]
	}

	for _, path := range paths {
		session := strings.TrimSuffix(filepath.Base(path), ".jsonl")
		invs, err := claude.SkillInvocations(path)
		if err != nil {
			return nil, err
		}
		turns := userTurns[session]
		// The accessor exposes no per-invocation user-turn text, so ground every
		// model-auto-trigger judgment in the session's user turns (see task 04
		// report Decisions — a reversible default until the accessor links them).
		grounding := strings.Join(turns, "\n")

		inputs := make([]TriggerInput, len(invs))
		for i, inv := range invs {
			inputs[i] = TriggerInput{Invocation: inv, UserTurn: grounding}
		}
		results, err := ClassifyTriggers(inputs, r, j)
		if err != nil {
			return nil, err
		}

		for i, res := range results {
			inv := invs[i]
			sr := agg(res.Name)
			sr.Invocations++
			switch res.Class {
			case ClassCorrectlyTriggered:
				sr.Trigger.Correct++
				verdict, evidence, scored := scoreOutcome(inv, r, j, outcomeModel)
				if !scored {
					break
				}
				switch verdict {
				case OutcomeSuccess:
					sr.Outcome.Success++
				case OutcomeFailure:
					sr.Outcome.Failure++
					sr.Findings = append(sr.Findings, finding{session, "failure", evidence, path})
				case OutcomeUnknown:
					sr.Outcome.Unknown++
					sr.Findings = append(sr.Findings, finding{session, "unknown", evidence, path})
				}
			case ClassMisfired:
				sr.Trigger.Misfired++
				sr.Findings = append(sr.Findings, finding{session, "misfired", resultExcerpt(inv), path})
			case ClassUnresolvable:
				sr.Trigger.Unresolvable++
				ev := fmt.Sprintf("SKILL.md not found for %q at either resolution path", inv.Name)
				sr.Findings = append(sr.Findings, finding{session, "unresolvable", ev, path})
			case ClassExplicitInvocation:
				sr.Trigger.ExplicitInvocation++
			case ClassSelfChained:
				sr.Trigger.SelfChained++
			}
		}

		misses, err := DetectPossibleMisses(turns, r)
		if err != nil {
			return nil, err
		}
		for _, m := range misses {
			sr := agg(m.Skill)
			sr.Trigger.PossibleMisses++
			ev := fmt.Sprintf("user turn matched phrase %q with no %s invocation: %s", m.Phrase, m.Skill, truncate(m.UserTurn, 120))
			sr.Findings = append(sr.Findings, finding{session, "possible_miss", ev, path})
		}
	}

	reports := make([]skillReport, 0, len(aggs))
	for name, sr := range aggs {
		if skillFilter != "" && name != skillFilter {
			continue
		}
		reports = append(reports, *sr)
	}
	sort.Slice(reports, func(a, b int) bool { return reports[a].Skill < reports[b].Skill })
	return reports, nil
}

// scoreOutcome runs task 03's outcome classification for one correctly-triggered
// invocation. scored is false when the skill no longer resolves (a race with
// SKILL.md removal), so the caller records no outcome.
func scoreOutcome(inv claude.SkillInvocation, r Resolver, j judge.Judge, outcomeModel string) (verdict OutcomeClass, evidence string, scored bool) {
	path, ok := r.resolve(inv.Name)
	if !ok {
		return "", "", false
	}
	oc, err := ClassifyOutcome(inv, path, j, outcomeModel)
	if err != nil {
		return "", "", false
	}
	return oc, resultExcerpt(inv), true
}

// resultExcerpt renders a one-line transcript excerpt for a finding's evidence.
func resultExcerpt(inv claude.SkillInvocation) string {
	r := strings.TrimSpace(inv.Result)
	if r == "" {
		return "(no tool_result captured for this invocation)"
	}
	if i := strings.IndexByte(r, '\n'); i >= 0 {
		r = r[:i]
	}
	return truncate(r, 160)
}

// truncate shortens s to at most n runes, appending an ellipsis when it cuts.
func truncate(s string, n int) string {
	runes := []rune(strings.TrimSpace(s))
	if len(runes) <= n {
		return string(runes)
	}
	return string(runes[:n]) + "…"
}

// resolveJudgeTierToModel maps a --judge-tier alias to the concrete model the
// `claude -p --model <model>` judge subprocess needs (R9). The mapping mirrors
// runtimes/claude-code.md's tier table (cited, not restated): scout→haiku,
// deep→opus, frontier→fable. `session` maps to `inherit`, which is unusable for
// a fresh subprocess with nothing to inherit, so it is rejected rather than
// silently downgraded to scout.
func resolveJudgeTierToModel(tier string) (string, error) {
	switch tier {
	case "scout":
		return "haiku", nil
	case "deep":
		return "opus", nil
	case "frontier":
		return "fable", nil
	case "session":
		return "", fmt.Errorf("--judge-tier session maps to `inherit`, unusable for a fresh judge subprocess; use scout, deep, or frontier")
	default:
		return "", fmt.Errorf("unknown --judge-tier %q (want scout, deep, or frontier)", tier)
	}
}

// renderReportsJSON marshals the per-skill reports as an indented JSON array.
func renderReportsJSON(reports []skillReport) ([]byte, error) {
	return json.MarshalIndent(reports, "", "  ")
}

// tableColumns fixes the table's column order (R13); the header names double as
// the parse keys a consumer splits on.
var tableColumns = []string{
	"skill", "invocations", "correct", "misfired", "unresolvable",
	"explicit_invocation", "self_chained", "possible_misses",
	"success", "failure", "unknown",
}

// renderReportsTable renders the same per-skill aggregate as tab-separated
// columns (R13) rather than the JSON shape — parseable by splitting on
// whitespace.
func renderReportsTable(reports []skillReport) string {
	var b strings.Builder
	b.WriteString(strings.Join(tableColumns, "\t"))
	b.WriteByte('\n')
	for _, sr := range reports {
		cells := []string{
			sr.Skill,
			itoa(sr.Invocations),
			itoa(sr.Trigger.Correct),
			itoa(sr.Trigger.Misfired),
			itoa(sr.Trigger.Unresolvable),
			itoa(sr.Trigger.ExplicitInvocation),
			itoa(sr.Trigger.SelfChained),
			itoa(sr.Trigger.PossibleMisses),
			itoa(sr.Outcome.Success),
			itoa(sr.Outcome.Failure),
			itoa(sr.Outcome.Unknown),
		}
		b.WriteString(strings.Join(cells, "\t"))
		b.WriteByte('\n')
	}
	return b.String()
}

func itoa(n int) string { return fmt.Sprintf("%d", n) }

// transcriptPaths lists main transcripts under claudeDir/projects whose file
// mtime is at or after cutoff, in deterministic lexical order.
func transcriptPaths(claudeDir string, cutoff time.Time) ([]string, error) {
	matches, err := filepath.Glob(filepath.Join(claudeDir, "projects", "*", "*.jsonl"))
	if err != nil {
		return nil, err
	}
	var paths []string
	for _, m := range matches {
		info, err := os.Stat(m)
		if err != nil {
			continue
		}
		if info.ModTime().Before(cutoff) {
			continue
		}
		paths = append(paths, m)
	}
	sort.Strings(paths)
	return paths, nil
}

// userTurnsBySession groups every in-window main-transcript user turn's prompt
// text by session id, via the claude package's exported Collect (reusing its
// JSONL walking rather than re-implementing a second parser). Used to ground
// trigger judgments and to feed possible-miss detection.
func userTurnsBySession(claudeDir string, cutoff time.Time) (map[string][]string, error) {
	_, turns, _, err := claude.CollectWithOptions(claudeDir, cutoff, claude.Options{})
	if err != nil {
		return nil, err
	}
	out := map[string][]string{}
	for _, t := range turns {
		if strings.TrimSpace(t.Prompt) == "" {
			continue
		}
		out[t.Session] = append(out[t.Session], t.Prompt)
	}
	return out, nil
}

// newSkillcheckJudge builds the CLI-backed judge skillcheck grades with,
// isolated under a scratch ScratchRoot so grading subprocesses never write into
// the profiled ~/.claude tree (R12).
func newSkillcheckJudge(scratchRoot string) *judge.CLIJudge {
	return &judge.CLIJudge{ScratchRoot: scratchRoot}
}

// defaultJudgeScratchRoot is the OS temp-dir base under which each judge call
// gets a fresh CLAUDE_CONFIG_DIR.
func defaultJudgeScratchRoot() string {
	return filepath.Join(os.TempDir(), "agentprof-skillcheck-judge")
}

// defaultPluginCacheRoot is $HOME/.claude/plugins/cache, the plugin-cache half
// of the two-path skill resolution order.
func defaultPluginCacheRoot() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return filepath.Join(".claude", "plugins", "cache")
	}
	return filepath.Join(home, ".claude", "plugins", "cache")
}

// skillcheckUsage documents every flag (R1/R9/R11/R13).
func skillcheckUsage(w io.Writer) {
	fmt.Fprint(w, `usage: agentprof skillcheck [flags]

Audits skill trigger-accuracy and outcome from Claude Code transcripts.

Flags:
  --days N          include sessions active within the last N days (default 30)
  --since RFC3339   absolute cutoff instead of --days (mutually exclusive)
  --skill NAME      restrict the report to a single skill
  --judge-tier T    outcome judge tier: scout (default), deep, or frontier
                    (session is rejected — a fresh subprocess cannot inherit)
  -o PATH           write the report to PATH (default stdout)
  --format F        output format: json (default) or table
  --claude-dir DIR  Claude Code data directory (default ~/.claude)
`)
}
