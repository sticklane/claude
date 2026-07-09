package main

import (
	"encoding/json"
	"fmt"
	"io"
	"sort"
	"strings"

	"github.com/sticklane/agentprof/internal/schema"
)

// summaryRow is one aggregated (session, model) cost row emitted by
// `claude -o summary` (workboard-model-costs R1). Field order fixes the JSON
// key order.
type summaryRow struct {
	Session          string `json:"session"`
	Model            string `json:"model"`
	InputTokens      int64  `json:"input_tokens"`
	OutputTokens     int64  `json:"output_tokens"`
	CacheReadTokens  int64  `json:"cache_read_tokens"`
	CacheWriteTokens int64  `json:"cache_write_tokens"`
	CostMicrousd     int64  `json:"cost_microusd"`
	Priced           bool   `json:"priced"`
}

// summarize aggregates samples into one row per distinct (session, model),
// summing the token-class and cost values (R1). Subagent spend already carries
// the parent session's id on Labels["session"], so aggregating that label
// attributes it to the spawning session (R2). A pair is priced unless a sample
// marks Labels["priced"] == "false", in which case its cost stays 0 (R3). Rows
// are sorted by (session, model) for deterministic output.
func summarize(samples []schema.Sample) []summaryRow {
	type key struct{ session, model string }
	agg := map[key]*summaryRow{}
	for _, s := range samples {
		leaf := s.Stack[len(s.Stack)-1]
		// EXCLUDE tool:/role:/stage: leaf frames from the (session, model)
		// rollup — mirroring costsummary.modelLeaf's marker set. Such samples
		// carry no token/cost values, so folding them in would only emit a
		// spurious zero-cost row (task 07 decision: exclude, not relabel).
		if isMarkerLeaf(leaf) {
			continue
		}
		k := key{s.Labels["session"], leaf}
		row := agg[k]
		if row == nil {
			row = &summaryRow{Session: k.session, Model: k.model, Priced: true}
			agg[k] = row
		}
		row.InputTokens += s.Values["input_tokens"]
		row.OutputTokens += s.Values["output_tokens"]
		row.CacheReadTokens += s.Values["cache_read_tokens"]
		row.CacheWriteTokens += s.Values["cache_write_tokens"]
		row.CostMicrousd += s.Values["cost_microusd"]
		if s.Labels["priced"] == "false" {
			row.Priced = false
		}
	}
	rows := make([]summaryRow, 0, len(agg))
	for _, row := range agg {
		rows = append(rows, *row)
	}
	sort.Slice(rows, func(i, j int) bool {
		if rows[i].Session != rows[j].Session {
			return rows[i].Session < rows[j].Session
		}
		return rows[i].Model < rows[j].Model
	})
	return rows
}

// isMarkerLeaf reports whether a stack leaf is a tool:/role:/stage: frame
// rather than a model-call leaf — the same non-model frame set costsummary's
// modelLeaf skips.
func isMarkerLeaf(f string) bool {
	return strings.HasPrefix(f, "tool:") || strings.HasPrefix(f, "role:") || strings.HasPrefix(f, "stage:")
}

// writeSummary marshals the aggregated rows as a JSON array to stdout (R1).
func writeSummary(samples []schema.Sample, stdout io.Writer) error {
	b, err := json.Marshal(summarize(samples))
	if err != nil {
		return err
	}
	_, err = fmt.Fprintln(stdout, string(b))
	return err
}
