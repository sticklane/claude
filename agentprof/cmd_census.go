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
	"text/tabwriter"
	"time"

	"github.com/sticklane/agentprof/internal/census"
)

// censusReport is one window's cross-harness usage picture. Unused names the
// installed skills nothing reached for; AuthoringOnly names those whose only
// records edited the skill's own source, which is not use.
type censusReport struct {
	Window        string         `json:"window"`
	Sessions      map[string]int `json:"sessions"`
	Skills        []census.Stat  `json:"skills"`
	Tools         []census.Stat  `json:"tools"`
	Unused        []string       `json:"unused"`
	AuthoringOnly []string       `json:"authoring_only"`
}

func cmdCensus(args []string, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("census", flag.ContinueOnError)
	fs.SetOutput(stderr)
	fs.Usage = func() { censusUsage(stderr) }
	home, _ := os.UserHomeDir()
	claudeDir := fs.String("claude-dir", filepath.Join(home, ".claude", "projects"), "Claude Code projects directory")
	codexDir := fs.String("codex-dir", filepath.Join(home, ".codex", "sessions"), "Codex sessions directory")
	agyDir := fs.String("antigravity-dir", filepath.Join(home, ".gemini", "antigravity-cli"), "Antigravity CLI data directory")
	skillsDir := fs.String("skills-dir", filepath.Join(home, ".claude", "skills"), "installed skills directory, for the unused-skill list")
	days := fs.Int("days", 14, "window size in days")
	since := fs.String("since", "", "absolute window start (RFC3339); mutually exclusive with --days")
	kind := fs.String("kind", "skill", "what to count: skill or all")
	format := fs.String("format", "table", "output format: table or json")
	out := fs.String("o", "", "write to this path instead of stdout")
	if err := fs.Parse(args); err != nil {
		return 2
	}

	cutoff := time.Now().AddDate(0, 0, -*days)
	if *since != "" {
		if isSet(fs, "days") {
			fmt.Fprintln(stderr, "agentprof census: --since and --days are mutually exclusive")
			return 2
		}
		parsed, err := time.Parse(time.RFC3339, *since)
		if err != nil {
			fmt.Fprintf(stderr, "agentprof census: invalid --since %q: %v\n", *since, err)
			return 2
		}
		cutoff = parsed
	}

	installed := installedSkills(*skillsDir)
	activations, sessions := collectActivations(*claudeDir, *codexDir, *agyDir, cutoff, knownSet(installed), stderr)
	stats := census.Aggregate(activations)
	report := censusReport{
		Window:        fmt.Sprintf("since %s", cutoff.Format(time.RFC3339)),
		Sessions:      sessions,
		Skills:        filterKind(stats, census.KindSkill),
		Unused:        census.Unused(installed, stats),
		AuthoringOnly: authoringOnly(stats),
	}
	if *kind == "all" {
		report.Tools = filterKind(stats, census.KindTool)
	}

	w := stdout
	if *out != "" {
		f, err := os.Create(*out)
		if err != nil {
			fmt.Fprintf(stderr, "agentprof census: %v\n", err)
			return 1
		}
		defer f.Close()
		w = f
	}
	if *format == "json" {
		enc := json.NewEncoder(w)
		enc.SetIndent("", "  ")
		if err := enc.Encode(report); err != nil {
			fmt.Fprintf(stderr, "agentprof census: %v\n", err)
			return 1
		}
		return 0
	}
	writeCensusTable(w, report)
	return 0
}

func collectActivations(claudeDir, codexDir, agyDir string, cutoff time.Time, known map[string]bool, stderr io.Writer) ([]census.Activation, map[string]int) {
	var all []census.Activation
	read := func(harness string, fn func(string, time.Time) ([]census.Activation, error), dir string) {
		acts, err := fn(dir, cutoff)
		if err != nil {
			fmt.Fprintf(stderr, "agentprof census: %s: %v\n", harness, err)
			return
		}
		all = append(all, acts...)
	}
	read("claude", func(dir string, c time.Time) ([]census.Activation, error) {
		return census.ReadClaude(dir, c, known)
	}, claudeDir)
	read("codex", census.ReadCodex, codexDir)
	read("antigravity", census.ReadAntigravity, agyDir)

	sessions := map[string]int{}
	seen := map[string]bool{}
	for _, a := range all {
		key := a.Harness + "/" + a.Session
		if !seen[key] {
			seen[key] = true
			sessions[a.Harness]++
		}
	}
	return all, sessions
}

// filterKind keeps the rows of one kind that record actual use. A name whose
// only records were source edits carries Total 0 and belongs in AuthoringOnly,
// not in a usage table where a zero row reads as noise.
func filterKind(stats []census.Stat, kind census.Kind) []census.Stat {
	out := []census.Stat{}
	for _, s := range stats {
		if s.Kind == kind && s.Total > 0 {
			out = append(out, s)
		}
	}
	return out
}

// authoringOnly names skills whose only records in the window edited their own
// source. They read as busy in a naive count and as unused here, which is what
// they are.
func authoringOnly(stats []census.Stat) []string {
	out := []string{}
	for _, s := range stats {
		if s.Kind == census.KindSkill && s.Total == 0 && s.Authoring > 0 {
			out = append(out, s.Name)
		}
	}
	sort.Strings(out)
	return out
}

func installedSkills(dir string) []string {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil
	}
	var out []string
	for _, e := range entries {
		if !e.IsDir() || strings.HasPrefix(e.Name(), "_") || strings.HasPrefix(e.Name(), ".") {
			continue
		}
		if _, err := os.Stat(filepath.Join(dir, e.Name(), "SKILL.md")); err != nil {
			continue
		}
		out = append(out, e.Name())
	}
	return out
}

// knownSet is nil for an unreadable skills directory, which tells the Claude
// reader to accept every command tag rather than silently counting none.
func knownSet(installed []string) map[string]bool {
	if len(installed) == 0 {
		return nil
	}
	out := make(map[string]bool, len(installed))
	for _, name := range installed {
		out[census.NormalizeName(name)] = true
	}
	return out
}

func isSet(fs *flag.FlagSet, name string) bool {
	found := false
	fs.Visit(func(f *flag.Flag) {
		if f.Name == name {
			found = true
		}
	})
	return found
}

func writeCensusTable(w io.Writer, r censusReport) {
	fmt.Fprintf(w, "%s — sessions:", r.Window)
	for _, h := range []string{"claude", "codex", "antigravity"} {
		fmt.Fprintf(w, " %s %d", h, r.Sessions[h])
	}
	fmt.Fprintln(w)

	tw := tabwriter.NewWriter(w, 0, 0, 2, ' ', 0)
	fmt.Fprintln(tw, "\nSKILL\tTOTAL\tCLAUDE\tCODEX\tAGY\tAUTO\tEXPL\tSESSIONS")
	for _, s := range r.Skills {
		fmt.Fprintf(tw, "%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n", s.Name, s.Total,
			s.ByHarness["claude"], s.ByHarness["codex"], s.ByHarness["antigravity"],
			s.Auto, s.Explicit, s.Sessions)
	}
	tw.Flush()

	if len(r.Tools) > 0 {
		tw = tabwriter.NewWriter(w, 0, 0, 2, ' ', 0)
		fmt.Fprintln(tw, "\nTOOL\tTOTAL\tCLAUDE\tCODEX\tSESSIONS")
		for _, s := range r.Tools {
			fmt.Fprintf(tw, "%s\t%d\t%d\t%d\t%d\n", s.Name, s.Total,
				s.ByHarness["claude"], s.ByHarness["codex"], s.Sessions)
		}
		tw.Flush()
		fmt.Fprintln(w, "\nantigravity records tool steps as model-authored verb phrases, not tool names; its tool column is omitted rather than guessed.")
	}

	if len(r.Unused) > 0 {
		fmt.Fprintf(w, "\nunused (installed, never reached for): %s\n", strings.Join(r.Unused, " "))
	}
	if len(r.AuthoringOnly) > 0 {
		fmt.Fprintf(w, "authoring-only (edited, never used): %s\n", strings.Join(r.AuthoringOnly, " "))
	}
}

func censusUsage(w io.Writer) {
	fmt.Fprint(w, `usage: agentprof census [flags]

Counts skill activations (and, with --kind all, tool calls) across Claude
Code, Codex, and Antigravity for one window.

Flags:
  --claude-dir PATH       Claude Code projects directory
  --codex-dir PATH        Codex sessions directory
  --antigravity-dir PATH  Antigravity CLI data directory
  --skills-dir PATH       installed skills, for the unused list
  --days N                window size in days (default 14)
  --since RFC3339         absolute window start; excludes --days
  --kind skill|all        count skills only, or skills and tools
  --format table|json     output format (default table)
  -o PATH                 write to a file instead of stdout
`)
}
