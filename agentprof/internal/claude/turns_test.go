package claude_test

import (
	"strings"
	"testing"

	"github.com/sticklane/agentprof/internal/claude"
)

const fakeSecret = "cfut_FAKEfake1234FAKEfake1234"

func userLine(ts, content string) string {
	return `{"type":"user","timestamp":"` + ts + `","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"` + content + `"}}`
}

func collectTurns(t *testing.T, dir string) []claude.Turn {
	t.Helper()
	_, turns, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	return turns
}

func findTurn(t *testing.T, turns []claude.Turn, session string, ordinal int) claude.Turn {
	t.Helper()
	for _, tr := range turns {
		if tr.Session == session && tr.Ordinal == ordinal {
			return tr
		}
	}
	t.Fatalf("no turn (%s, %d) in %v", session, ordinal, turns)
	return claude.Turn{}
}

func TestCollectScrubsSecretsInTurnFrames(t *testing.T) {
	dir := writeMain(t,
		userLine("2026-07-01T09:00:00Z", "api token "+fakeSecret+" leaked"),
		assistantLine("m1"),
	)

	samples, turns, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	if len(samples) != 1 {
		t.Fatalf("got %d samples, want 1", len(samples))
	}
	want := "t01 · api token [redacted] leaked"
	if got := samples[0].Stack[1]; got != want {
		t.Errorf("turn frame = %q, want %q", got, want)
	}
	tr := findTurn(t, turns, "sess-z", 1)
	if strings.Contains(tr.Prompt, "cfut_") {
		t.Errorf("Turn.Prompt leaks the secret: %q", tr.Prompt)
	}
	if tr.Prompt != "api token [redacted] leaked" {
		t.Errorf("Turn.Prompt = %q, want scrubbed prompt", tr.Prompt)
	}
}

func TestCollectSnippetTruncatesBeforeStraddlingRedactionMarker(t *testing.T) {
	// After scrubbing, the [redacted] marker occupies runes 35-44: it
	// straddles the 40-rune cut, so the snippet must end right before it.
	pre := strings.Repeat("a", 34) + " "
	dir := writeMain(t,
		userLine("2026-07-01T09:00:00Z", pre+fakeSecret+" tail more words here"),
		assistantLine("m1"),
	)

	samples, turns, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	want := "t01 · " + pre + "…"
	if got := samples[0].Stack[1]; got != want {
		t.Errorf("turn frame = %q, want %q (cut before straddling marker)", got, want)
	}
	// The marker is truncated out of the shown snippet, so this turn is NOT
	// a naming candidate (6 words, no command extraction).
	if tr := findTurn(t, turns, "sess-z", 1); tr.Candidate {
		t.Errorf("turn with marker truncated out must not be a candidate: %+v", tr)
	}
}

func TestCollectMarksCandidateTurns(t *testing.T) {
	// 5 words; the secret starts at rune 41, so its marker lies wholly
	// beyond the 40-rune snippet window.
	longSecretBeyondWindow := strings.Repeat("a", 10) + " " + strings.Repeat("b", 10) + " " +
		strings.Repeat("c", 10) + " " + strings.Repeat("d", 8) + " " + fakeSecret
	dir := writeMain(t,
		userLine("2026-07-01T09:00:00Z", "fix the auth bug"),                                                                  // t01: 4 words -> candidate
		userLine("2026-07-01T09:00:01Z", "fix the auth bug now"),                                                              // t02: 5 words -> not
		userLine("2026-07-01T09:00:02Z", "<command-name>/go</command-name><command-args></command-args>"),                     // t03: command, redaction-free -> not
		userLine("2026-07-01T09:00:03Z", "<command-name>/go</command-name><command-args>"+fakeSecret+" x y z</command-args>"), // t04: command but redacted snippet -> candidate
		userLine("2026-07-01T09:00:04Z", longSecretBeyondWindow),                                                              // t05: marker wholly beyond 40-rune window -> not
		assistantLine("m1"),
	)

	turns := collectTurns(t, dir)
	wantCandidates := map[int]bool{1: true, 2: false, 3: false, 4: true, 5: false}
	for ord, want := range wantCandidates {
		if got := findTurn(t, turns, "sess-z", ord).Candidate; got != want {
			t.Errorf("turn %02d candidate = %v, want %v", ord, got, want)
		}
	}
}

func TestCollectExposesTurnNamingContextFromFixture(t *testing.T) {
	_, turns, _, err := claude.Collect(fixtureDir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}

	t01 := findTurn(t, turns, "sess-0001", 1)
	if t01.Frame != "t01 · start" || t01.Prompt != "start" {
		t.Errorf("sess-0001 t01 = %+v, want frame 't01 · start', prompt 'start'", t01)
	}
	if t01.ReplyHead != "Spawning a scout." {
		t.Errorf("sess-0001 t01 reply head = %q, want first assistant text", t01.ReplyHead)
	}
	if !t01.Candidate {
		t.Error("sess-0001 t01 ('start', one word) must be a naming candidate")
	}

	t02 := findTurn(t, turns, "sess-0001", 2)
	if t02.Candidate {
		t.Error("sess-0001 t02 (redaction-free slash command) must not be a candidate")
	}

	// No synthetic t00 entries: they are never naming candidates.
	for _, tr := range turns {
		if tr.Ordinal == 0 {
			t.Errorf("synthetic t00 exposed as naming context: %+v", tr)
		}
	}
}

func TestCollectCapturesFirstAssistantTextAsReplyHeadOnly(t *testing.T) {
	first := `{"type":"assistant","timestamp":"2026-07-01T09:01:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"id":"m1","model":"claude-fable-5","content":[{"type":"text","text":"first reply with ` + fakeSecret + `"}],"usage":{"input_tokens":10,"output_tokens":1}}}`
	second := `{"type":"assistant","timestamp":"2026-07-01T09:02:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"id":"m2","model":"claude-fable-5","content":[{"type":"text","text":"second reply"}],"usage":{"input_tokens":10,"output_tokens":1}}}`
	dir := writeMain(t,
		userLine("2026-07-01T09:00:00Z", "hi"),
		first,
		second,
	)

	tr := findTurn(t, collectTurns(t, dir), "sess-z", 1)
	if tr.ReplyHead != "first reply with [redacted]" {
		t.Errorf("reply head = %q, want scrubbed FIRST assistant text", tr.ReplyHead)
	}
}

func TestCollectTruncatesNamingContextToFiveHundredRunes(t *testing.T) {
	long := strings.Repeat("é ", 300) // 600 runes, no truncation ambiguity
	dir := writeMain(t,
		userLine("2026-07-01T09:00:00Z", strings.TrimSpace(long)),
		assistantLine("m1"),
	)

	tr := findTurn(t, collectTurns(t, dir), "sess-z", 1)
	if n := len([]rune(tr.Prompt)); n != 500 {
		t.Errorf("Turn.Prompt is %d runes, want 500", n)
	}
}
