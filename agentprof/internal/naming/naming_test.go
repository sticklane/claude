package naming_test

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/sticklane/agentprof/internal/claude"
	"github.com/sticklane/agentprof/internal/naming"
)

// fakeNamer returns canned names and records how it was called.
type fakeNamer struct {
	names map[string]string
	err   error
	calls [][]naming.Candidate
}

func (f *fakeNamer) Name(cands []naming.Candidate) (map[string]string, error) {
	f.calls = append(f.calls, cands)
	return f.names, f.err
}

func cand(prompt, replyHead string) naming.Candidate {
	return naming.Candidate{ID: naming.Key(prompt, replyHead), Prompt: prompt, ReplyHead: replyHead}
}

func TestKeyIsSHA256OfPromptNulReplyHead(t *testing.T) {
	want := fmt.Sprintf("%x", sha256.Sum256([]byte("fix bug\x00done")))
	if got := naming.Key("fix bug", "done"); got != want {
		t.Errorf("Key = %q, want %q", got, want)
	}
}

func TestResolveInvokesNamerOnceForMissesAndWritesSortedCache(t *testing.T) {
	cachePath := filepath.Join(t.TempDir(), "agentprof", "turn-names.json")
	a, b := cand("zz last", ""), cand("aa first", "")
	f := &fakeNamer{names: map[string]string{a.ID: "rename z turn", b.ID: "rename a turn"}}

	got := naming.Resolve([]naming.Candidate{a, b}, f, cachePath, io.Discard)

	if len(f.calls) != 1 || len(f.calls[0]) != 2 {
		t.Fatalf("namer calls = %v, want one call with both candidates", f.calls)
	}
	if got[a.ID] != "rename z turn" || got[b.ID] != "rename a turn" {
		t.Errorf("Resolve = %v", got)
	}
	data, err := os.ReadFile(cachePath)
	if err != nil {
		t.Fatalf("cache file not written: %v", err)
	}
	var m map[string]string
	if err := json.Unmarshal(data, &m); err != nil {
		t.Fatalf("cache file not valid JSON: %v", err)
	}
	if len(m) != 2 || m[a.ID] != "rename z turn" {
		t.Errorf("cache contents = %v", m)
	}
	// Keys must be serialized in sorted order (byte-stable reruns).
	iA, iB := strings.Index(string(data), a.ID), strings.Index(string(data), b.ID)
	if (a.ID < b.ID) != (iA < iB) {
		t.Errorf("cache keys not sorted: %s", data)
	}
}

func TestResolveHitsCacheWithoutInvokingNamer(t *testing.T) {
	cachePath := filepath.Join(t.TempDir(), "turn-names.json")
	c := cand("small prompt", "reply")
	seed, _ := json.Marshal(map[string]string{c.ID: "cached name"})
	if err := os.WriteFile(cachePath, seed, 0o644); err != nil {
		t.Fatal(err)
	}
	f := &fakeNamer{}

	got := naming.Resolve([]naming.Candidate{c}, f, cachePath, io.Discard)

	if len(f.calls) != 0 {
		t.Errorf("namer invoked on a full cache hit: %v", f.calls)
	}
	if got[c.ID] != "cached name" {
		t.Errorf("Resolve = %v, want cache hit", got)
	}
	after, _ := os.ReadFile(cachePath)
	if string(after) != string(seed) {
		t.Errorf("cache rewritten on a pure-hit run:\nbefore %s\nafter  %s", seed, after)
	}
}

func TestResolveTreatsCorruptCacheAsEmptyWithWarning(t *testing.T) {
	cachePath := filepath.Join(t.TempDir(), "turn-names.json")
	if err := os.WriteFile(cachePath, []byte("{not json"), 0o644); err != nil {
		t.Fatal(err)
	}
	c := cand("p", "r")
	f := &fakeNamer{names: map[string]string{c.ID: "fresh name"}}
	var warn strings.Builder

	got := naming.Resolve([]naming.Candidate{c}, f, cachePath, &warn)

	if got[c.ID] != "fresh name" {
		t.Errorf("Resolve = %v, want namer result despite corrupt cache", got)
	}
	if warn.Len() == 0 {
		t.Error("corrupt cache must produce a warning")
	}
}

func TestResolveValidatesNames(t *testing.T) {
	cases := []struct {
		name string
		raw  string
		want string // "" means rejected
	}{
		{"trims and lowercases", "  Fix Auth Bug  ", "fix auth bug"},
		{"allows slash dot underscore dash", "run tests/unit_v1.2-rc", "run tests/unit_v1.2-rc"},
		{"rejects empty", "   ", ""},
		{"rejects too long", strings.Repeat("x", 49), ""},
		{"rejects leading dash", "-bad name", ""},
		{"rejects colon", "fix: bug", ""},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			cachePath := filepath.Join(t.TempDir(), "turn-names.json")
			c := cand("prompt "+tc.name, "")
			f := &fakeNamer{names: map[string]string{c.ID: tc.raw}}
			got := naming.Resolve([]naming.Candidate{c}, f, cachePath, io.Discard)
			name, ok := got[c.ID]
			if tc.want == "" {
				if ok {
					t.Errorf("invalid name %q accepted as %q", tc.raw, name)
				}
				if _, err := os.Stat(cachePath); err == nil {
					data, _ := os.ReadFile(cachePath)
					var m map[string]string
					json.Unmarshal(data, &m)
					if _, cached := m[c.ID]; cached {
						t.Errorf("rejected name cached: %s", data)
					}
				}
			} else if name != tc.want {
				t.Errorf("name = %q (ok=%v), want %q", name, ok, tc.want)
			}
		})
	}
}

func TestResolveNamerFailureDegradesToCacheHitsWithWarning(t *testing.T) {
	cachePath := filepath.Join(t.TempDir(), "turn-names.json")
	hit, miss := cand("cached prompt", ""), cand("missing prompt", "")
	seed, _ := json.Marshal(map[string]string{hit.ID: "cached name"})
	if err := os.WriteFile(cachePath, seed, 0o644); err != nil {
		t.Fatal(err)
	}
	f := &fakeNamer{err: fmt.Errorf("claude CLI absent")}
	var warn strings.Builder

	got := naming.Resolve([]naming.Candidate{hit, miss}, f, cachePath, &warn)

	if got[hit.ID] != "cached name" {
		t.Errorf("cache hit lost on namer failure: %v", got)
	}
	if _, ok := got[miss.ID]; ok {
		t.Errorf("failed namer produced a name: %v", got)
	}
	if warn.Len() == 0 {
		t.Error("namer failure must warn on stderr")
	}
}

func TestResolveDedupesCandidatesByID(t *testing.T) {
	cachePath := filepath.Join(t.TempDir(), "turn-names.json")
	c := cand("same prompt", "same reply")
	f := &fakeNamer{names: map[string]string{c.ID: "one name"}}

	naming.Resolve([]naming.Candidate{c, c}, f, cachePath, io.Discard)

	if len(f.calls) != 1 || len(f.calls[0]) != 1 {
		t.Errorf("namer got %v, want a single deduped candidate", f.calls)
	}
}

func TestCachePathAndConfigDirHonorXDGCacheHome(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("XDG_CACHE_HOME", tmp)
	if got, want := naming.CachePath(), filepath.Join(tmp, "agentprof", "turn-names.json"); got != want {
		t.Errorf("CachePath = %q, want %q", got, want)
	}
	if got, want := naming.ConfigDir(), filepath.Join(tmp, "agentprof", "claude-config"); got != want {
		t.Errorf("ConfigDir = %q, want %q", got, want)
	}
}

func TestRewriteFramesPropagatesThroughSubagentStacks(t *testing.T) {
	samples, _, _, err := claude.Collect("../../testdata/claude-dir", time.Time{})
	if err != nil {
		t.Fatal(err)
	}

	naming.RewriteFrames(samples, "sess-0001", map[string]string{"t01 · start": "t01 · scaffold the build"})

	var mainHit, depth1Hit, depth2Hit bool
	for _, s := range samples {
		joined := strings.Join(s.Stack, " / ")
		if s.Labels["session"] == "sess-0001" && strings.Contains(joined, "t01 · start") {
			t.Errorf("old frame survives in sess-0001 stack: %v", s.Stack)
		}
		if strings.Contains(joined, "t01 · scaffold the build") {
			switch {
			case strings.HasSuffix(joined, "build / main / claude-fable-5"):
				mainHit = true // msg_a1
			case strings.HasSuffix(joined, "agent:scout / claude-fable-5"):
				depth1Hit = true // agent-A
			case strings.HasSuffix(joined, "agent:workflow-subagent / claude-fable-5"):
				depth2Hit = true // agent-W (run-linked workflow subagent)
			}
		}
	}
	if !mainHit || !depth1Hit || !depth2Hit {
		t.Errorf("rename must reach main + both subagent stacks; main=%v depth1=%v depth2=%v", mainHit, depth1Hit, depth2Hit)
	}
}

func TestRewriteFramesLeavesOtherSessionsAlone(t *testing.T) {
	samples, _, _, err := claude.Collect("../../testdata/claude-dir", time.Time{})
	if err != nil {
		t.Fatal(err)
	}

	// sess-0002 also has a "t01 · ..." frame; renaming sess-0001 must not
	// touch it even if the frame text matched.
	naming.RewriteFrames(samples, "sess-0001", map[string]string{"t01 · hello": "t01 · should not apply"})

	for _, s := range samples {
		if strings.Contains(strings.Join(s.Stack, " / "), "should not apply") {
			t.Errorf("rename leaked across sessions: %v", s.Stack)
		}
	}
}
