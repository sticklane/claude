package claude_test

import (
	"testing"

	"github.com/sticklane/agentprof/internal/claude"
)

// toolResultLineWithFlag is a user line carrying the tool_result for tu1 with a
// top-level boolean flag set — "isMeta" or "isSidechain". This is the shape a
// subagent / Agent-tool result takes in real transcripts, where the result
// arrives on a meta or sidechain user line rather than the main conversation.
func toolResultLineWithFlag(ts, flag string) string {
	return `{"type":"user","timestamp":"` + ts + `","cwd":"/z/app","sessionId":"sess-z","` + flag + `":true,"message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"tu1","content":"done"}]}}`
}

// TestToolResultOnMetaOrSidechainLineMatchesToolUse covers task 08: a tool_use
// whose tool_result arrives on an isMeta or isSidechain user line must still
// match its call. Before the fix, the parser skipped such lines before
// populating the tool-result set, so the call went unmatched and was counted
// pending (Stats.Pending == 1, plus a tool:(pending) sample) — the mechanical
// source of the ~8,854 pending-sample volume from Agent-tool result shapes.
// After the fix the result matches, dropping the pending count to zero.
func TestToolResultOnMetaOrSidechainLineMatchesToolUse(t *testing.T) {
	for _, flag := range []string{"isMeta", "isSidechain"} {
		t.Run(flag, func(t *testing.T) {
			dir := writeMain(t,
				`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"go"}}`,
				toolUseLine("2026-07-01T09:00:10.000Z"),
				toolResultLineWithFlag("2026-07-01T09:00:10.250Z", flag),
			)

			samples, _, stats, err := claude.CollectWithOptions(dir, anyCutoff, claude.Options{})
			if err != nil {
				t.Fatalf("CollectWithOptions: %v", err)
			}
			if stats.Pending != 0 {
				t.Errorf("Stats.Pending = %d, want 0 (a tool_result on a %s line should match its tool_use)", stats.Pending, flag)
			}
			if got := pendingSamples(samples); len(got) != 0 {
				t.Errorf("got %d tool:(pending) samples, want 0 (%s result should match): %v", len(got), flag, stacks(samples))
			}
		})
	}
}
