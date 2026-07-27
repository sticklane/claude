package census

import (
	"database/sql"
	"os"
	"path/filepath"
	"testing"
	"time"

	_ "modernc.org/sqlite"
)

func writeConversationDB(t *testing.T, blobs ...string) string {
	t.Helper()
	dir := t.TempDir()
	conv := filepath.Join(dir, "conversations")
	if err := os.MkdirAll(conv, 0o755); err != nil {
		t.Fatal(err)
	}
	db, err := sql.Open("sqlite", filepath.Join(conv, "conv-1.db"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if _, err := db.Exec("CREATE TABLE steps (idx integer PRIMARY KEY, metadata blob, render_info blob, step_payload blob)"); err != nil {
		t.Fatal(err)
	}
	for i, b := range blobs {
		if _, err := db.Exec("INSERT INTO steps (idx, step_payload) VALUES (?, ?)", i, []byte(b)); err != nil {
			t.Fatal(err)
		}
	}
	return dir
}

func TestReadAntigravityCountsAViewOfSkillSourceAsActivation(t *testing.T) {
	dir := writeConversationDB(t,
		`{"path":"/Users/x/claude/.claude/skills/drain/SKILL.md","toolAction":"Viewing drain/SKILL.md"}`)
	acts, err := ReadAntigravity(dir, time.Time{})
	if err != nil {
		t.Fatal(err)
	}
	got := find(t, acts, KindSkill, "drain")
	if got.Harness != "antigravity" {
		t.Errorf("Harness = %q, want antigravity", got.Harness)
	}
	if got.Authoring {
		t.Error("Authoring = true, want false for a view")
	}
	if got.Session != "conv-1" {
		t.Errorf("Session = %q, want conv-1", got.Session)
	}
}

func TestReadAntigravityMarksAnUpdateOfSkillSourceAsAuthoring(t *testing.T) {
	dir := writeConversationDB(t,
		`{"path":"/Users/x/claude/.claude/skills/critique/SKILL.md","toolAction":"Updating critique/SKILL.md"}`)
	acts, err := ReadAntigravity(dir, time.Time{})
	if err != nil {
		t.Fatal(err)
	}
	if !find(t, acts, KindSkill, "critique").Authoring {
		t.Error("Authoring = false, want true for an update")
	}
}

func TestReadAntigravityCountsOneActivationPerStepNotPerPathMention(t *testing.T) {
	dir := writeConversationDB(t,
		`{"path":"/x/skills/build/SKILL.md","toolAction":"Viewing build/SKILL.md","toolSummary":"read /x/skills/build/SKILL.md"}`)
	acts, err := ReadAntigravity(dir, time.Time{})
	if err != nil {
		t.Fatal(err)
	}
	if len(acts) != 1 {
		t.Errorf("got %d activations, want 1 — repeated paths in one step are one activation", len(acts))
	}
}

func TestReadAntigravityIgnoresStepsWithNoSkillPath(t *testing.T) {
	dir := writeConversationDB(t, `{"toolAction":"Running command","toolSummary":"go test ./..."}`)
	acts, err := ReadAntigravity(dir, time.Time{})
	if err != nil {
		t.Fatal(err)
	}
	if len(acts) != 0 {
		t.Errorf("got %d activations, want 0", len(acts))
	}
}

func TestReadAntigravitySkipsConversationsLastTouchedBeforeCutoff(t *testing.T) {
	dir := writeConversationDB(t,
		`{"path":"/x/skills/drain/SKILL.md","toolAction":"Viewing drain/SKILL.md"}`)
	stale := time.Now().Add(-72 * time.Hour)
	if err := os.Chtimes(filepath.Join(dir, "conversations", "conv-1.db"), stale, stale); err != nil {
		t.Fatal(err)
	}
	acts, err := ReadAntigravity(dir, time.Now().Add(-24*time.Hour))
	if err != nil {
		t.Fatal(err)
	}
	if len(acts) != 0 {
		t.Errorf("got %d activations, want 0 for a conversation older than the window", len(acts))
	}
}

func TestReadAntigravitySkipsUnreadableDatabaseWithoutFailing(t *testing.T) {
	dir := t.TempDir()
	conv := filepath.Join(dir, "conversations")
	if err := os.MkdirAll(conv, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(conv, "junk.db"), []byte("not a database"), 0o644); err != nil {
		t.Fatal(err)
	}
	acts, err := ReadAntigravity(dir, time.Time{})
	if err != nil {
		t.Fatalf("a corrupt db must be skipped, not fatal: %v", err)
	}
	if len(acts) != 0 {
		t.Errorf("got %d activations, want 0", len(acts))
	}
}
