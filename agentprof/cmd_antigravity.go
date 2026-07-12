package main

import (
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"

	"github.com/sticklane/agentprof/internal/antigravity"
	"github.com/sticklane/agentprof/internal/output"
)

// cmdAntigravity emits canonical samples from Antigravity CLI conversation
// databases (Solution item 4). It mirrors cmdClaude's flag shape for
// --antigravity-dir, --days/--since, and -o, reusing internal/output and
// summary.go unchanged. --merge and --summary are explicitly out of scope.
func cmdAntigravity(args []string, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("antigravity", flag.ContinueOnError)
	fs.SetOutput(stderr)
	dir := fs.String("antigravity-dir", defaultAntigravityDir(), "Antigravity CLI data directory")
	days := fs.Int("days", 30, "include sessions active within the last N days")
	since := fs.String("since", "", "absolute RFC3339 cutoff (mutually exclusive with an explicit --days)")
	out := fs.String("o", "", "output path: .pb.gz writes a pprof profile, anything else JSONL (default stdout)")
	if err := fs.Parse(args); err != nil {
		return 2
	}

	// Usage checks run before Collect so a rejected invocation writes nothing.
	daysExplicit := false
	fs.Visit(func(f *flag.Flag) {
		if f.Name == "days" {
			daysExplicit = true
		}
	})
	cutoff := time.Now().AddDate(0, 0, -*days)
	if *since != "" {
		if daysExplicit {
			fmt.Fprintln(stderr, "agentprof antigravity: --since and --days are mutually exclusive")
			return 2
		}
		t, err := time.Parse(time.RFC3339, *since)
		if err != nil {
			fmt.Fprintf(stderr, "agentprof antigravity: invalid --since %q: %v\n", *since, err)
			return 2
		}
		cutoff = t
	}

	samples, skipped, err := antigravity.Collect(*dir, cutoff)
	if err != nil {
		fmt.Fprintf(stderr, "agentprof antigravity: %v\n", err)
		return 1
	}
	if skipped > 0 {
		fmt.Fprintf(stderr, "skipped %d unparseable databases\n", skipped)
	}

	// Zero-sample guard lives here in package main, matching cmd_claude.go.
	if len(samples) == 0 {
		fmt.Fprintln(stderr, "agentprof antigravity: no samples found (check --antigravity-dir and --days)")
		return 1
	}
	if *out == "summary" {
		if err := writeSummary(samples, stdout); err != nil {
			fmt.Fprintf(stderr, "agentprof antigravity: %v\n", err)
			return 1
		}
		return 0
	}
	if err := output.Write(samples, *out, stdout); err != nil {
		fmt.Fprintf(stderr, "agentprof antigravity: %v\n", err)
		return 1
	}
	return 0
}

// defaultAntigravityDir is $HOME/.gemini/antigravity-cli, or the bare relative
// path if the home directory cannot be determined.
func defaultAntigravityDir() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return filepath.Join(".gemini", "antigravity-cli")
	}
	return filepath.Join(home, ".gemini", "antigravity-cli")
}
