package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/sticklane/agentprof/internal/claude"
	"github.com/sticklane/agentprof/internal/costsummary"
	"github.com/sticklane/agentprof/internal/merge"
	"github.com/sticklane/agentprof/internal/naming"
	"github.com/sticklane/agentprof/internal/output"
	"github.com/sticklane/agentprof/internal/schema"
)

// cmdClaude emits canonical samples from Claude Code transcripts (R4-R8).
func cmdClaude(args []string, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("claude", flag.ContinueOnError)
	fs.SetOutput(stderr)
	dir := fs.String("claude-dir", defaultClaudeDir(), "Claude Code data directory")
	days := fs.Int("days", 30, "include sessions active within the last N days")
	since := fs.String("since", "", "absolute RFC3339 cutoff (mutually exclusive with an explicit --days)")
	mergePath := fs.String("merge", "", "JSONL rolling-cache path: merge fresh samples in, evicting samples older than 7d")
	summaryPath := fs.String("summary", "", "write the pre-aggregated Cost (7d) summary JSON to this path")
	nameTurns := fs.Bool("name-turns", false, "rename uninformative turn frames via one cached haiku call")
	reprimeThreshold := fs.Int("reprime-threshold", claude.DefaultReprimeThreshold, "cache_write_tokens above which a non-first main-loop call is labeled reprime=true (0 disables)")
	keepPending := fs.Bool("keep-pending", false, "keep one tool:(pending) sample per unmatched tool call instead of consolidating them into a single pending_calls count")
	out := fs.String("o", "", "output path: .pb.gz writes a pprof profile, anything else JSONL (default stdout)")
	frameDenylist := fs.String("frame-denylist", defaultFrameDenylist(), "path to a frame denylist file (one substring per line); any frame containing a listed string is redacted before emit")
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
			fmt.Fprintln(stderr, "agentprof claude: --since and --days are mutually exclusive")
			return 2
		}
		t, err := time.Parse(time.RFC3339, *since)
		if err != nil {
			fmt.Fprintf(stderr, "agentprof claude: invalid --since %q: %v\n", *since, err)
			return 2
		}
		cutoff = t
	}
	if *mergePath != "" && strings.HasSuffix(*out, ".pb.gz") {
		fmt.Fprintln(stderr, "agentprof claude: --merge requires a JSONL -o path, not .pb.gz (pprof cannot round-trip per-sample time)")
		return 2
	}

	denied, err := claude.LoadDenylist(*frameDenylist)
	if err != nil {
		fmt.Fprintf(stderr, "agentprof claude: %v\n", err)
		return 1
	}

	samples, turns, stats, err := claude.CollectWithOptions(*dir, cutoff, claude.Options{
		ReprimeThreshold: *reprimeThreshold,
		KeepPending:      *keepPending,
	})
	if err != nil {
		fmt.Fprintf(stderr, "agentprof claude: %v\n", err)
		return 1
	}
	if stats.Skipped > 0 {
		fmt.Fprintf(stderr, "skipped %d unparseable lines\n", stats.Skipped)
	}
	if stats.Pending > 0 {
		disposition := "consolidated into tool:(pending)"
		if *keepPending {
			disposition = "kept as tool:(pending)"
		}
		fmt.Fprintf(stderr, "%d unmatched tool call(s) %s\n", stats.Pending, disposition)
	}
	// Redact denylisted frames before any emit path (merge, summary, or direct);
	// re-applied after --name-turns below since renaming rewrites turn frames,
	// and again over the merged set (which folds in the unscrubbed rolling cache).
	claude.ScrubFrames(samples, denied)

	if *mergePath != "" {
		return mergeClaude(samples, denied, *mergePath, *out, *summaryPath, stdout, stderr)
	}

	if len(samples) == 0 {
		fmt.Fprintln(stderr, "agentprof claude: no samples found (check --claude-dir and --days)")
		return 1
	}
	if *out == "summary" {
		if err := writeSummary(samples, stdout); err != nil {
			fmt.Fprintf(stderr, "agentprof claude: %v\n", err)
			return 1
		}
		return 0
	}
	if *nameTurns {
		nameTurnFrames(samples, turns, stderr)
		claude.ScrubFrames(samples, denied)
	}
	if err := output.Write(samples, *out, stdout); err != nil {
		fmt.Fprintf(stderr, "agentprof claude: %v\n", err)
		return 1
	}
	// Without --merge the summary groups the fresh Collect() output directly (R3).
	if *summaryPath != "" {
		if err := writeCostSummary(samples, samples, *summaryPath); err != nil {
			fmt.Fprintf(stderr, "agentprof claude: %v\n", err)
			return 1
		}
	}
	return 0
}

// mergeClaude folds fresh samples into the JSONL rolling cache at mergePath
// and writes the merged, 7d-evicted result to out. Both zero-sample guards are
// bypassed (R2): a missing cache is zero samples, an empty fresh pass is not an
// error, and an empty merged result writes a valid empty JSONL file directly
// rather than routing through output.Write's zero-sample error.
func mergeClaude(fresh []schema.Sample, denied []string, mergePath, out, summaryPath string, stdout, stderr io.Writer) int {
	existing, err := readCache(mergePath)
	if err != nil {
		fmt.Fprintf(stderr, "agentprof claude: %v\n", err)
		return 1
	}
	merged := merge.Merge(existing, fresh, time.Now())
	// The rolling cache may hold frames written before the denylist existed (or
	// before a substring was added), so scrub the merged set — not just fresh —
	// before it reaches output.Write or the cost summary.
	claude.ScrubFrames(merged, denied)
	if len(merged) == 0 {
		if err := writeEmptyJSONL(out, stdout); err != nil {
			fmt.Fprintf(stderr, "agentprof claude: %v\n", err)
			return 1
		}
	} else if err := output.Write(merged, out, stdout); err != nil {
		fmt.Fprintf(stderr, "agentprof claude: %v\n", err)
		return 1
	}
	// The summary groups the final merged, post-eviction rolling window; only
	// sessions_added counts fresh. Writing works even when merged is empty (R3).
	if summaryPath != "" {
		if err := writeCostSummary(merged, fresh, summaryPath); err != nil {
			fmt.Fprintf(stderr, "agentprof claude: %v\n", err)
			return 1
		}
	}
	return 0
}

// writeCostSummary aggregates forGrouping into the Cost (7d) summary JSON
// (sessions_added counted from fresh) and writes it to path (R3).
func writeCostSummary(forGrouping, fresh []schema.Sample, path string) error {
	b, err := json.MarshalIndent(costsummary.Build(forGrouping, fresh), "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(b, '\n'), 0o644)
}

// readCache reads the existing rolling-cache JSONL; a missing file is treated
// as zero existing samples, not an error (R2).
func readCache(path string) ([]schema.Sample, error) {
	f, err := os.Open(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil, nil
		}
		return nil, err
	}
	defer f.Close()
	samples, _, err := schema.Read(f)
	return samples, err
}

// writeEmptyJSONL writes a valid empty JSONL result for an empty merged set:
// stdout gets nothing, a real path is truncated to zero bytes.
func writeEmptyJSONL(path string, stdout io.Writer) error {
	if path == "" || path == "-" {
		return nil
	}
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	return f.Close()
}

// nameTurnFrames renames candidate turns' frames to "tNN · <name>" in place,
// keyed by (session, ordinal); unresolved turns keep their snippet frames
// (frame-naming SPEC R3).
func nameTurnFrames(samples []schema.Sample, turns []claude.Turn, stderr io.Writer) {
	var cands []naming.Candidate
	for _, t := range turns {
		if t.Candidate {
			cands = append(cands, naming.Candidate{ID: naming.Key(t.Prompt, t.ReplyHead), Prompt: t.Prompt, ReplyHead: t.ReplyHead})
		}
	}
	if len(cands) == 0 {
		return
	}
	namer := &naming.CLINamer{ConfigDir: naming.ConfigDir()}
	names := naming.Resolve(cands, namer, naming.CachePath(), stderr)

	renames := map[string]map[string]string{} // session -> old frame -> new frame
	for _, t := range turns {
		if !t.Candidate {
			continue
		}
		name, ok := names[naming.Key(t.Prompt, t.ReplyHead)]
		if !ok {
			continue
		}
		if renames[t.Session] == nil {
			renames[t.Session] = map[string]string{}
		}
		renames[t.Session][t.Frame] = fmt.Sprintf("t%02d · %s", t.Ordinal, name)
	}
	for session, m := range renames {
		naming.RewriteFrames(samples, session, m)
	}
}

// defaultClaudeDir is $HOME/.claude, or the bare relative path if the home
// directory cannot be determined.
func defaultClaudeDir() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ".claude"
	}
	return filepath.Join(home, ".claude")
}

// defaultFrameDenylist is $HOME/.config/agentprof/frame-denylist. A missing
// file is treated as no denylist (LoadDenylist), so this default is safe even
// when nothing is configured.
func defaultFrameDenylist() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return filepath.Join(".config", "agentprof", "frame-denylist")
	}
	return filepath.Join(home, ".config", "agentprof", "frame-denylist")
}
