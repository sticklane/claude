package census

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	_ "modernc.org/sqlite"
)

// toolAction is the human-readable verb phrase Antigravity records for each
// step. Its vocabulary is model-authored ("Viewing", "List", "Checking"), so
// it is read only to tell a source edit from a source read — never used as a
// tool name. Antigravity therefore contributes skill activations only, and the
// census reports its tool axis as unavailable rather than inventing one.
var toolAction = regexp.MustCompile(`"toolAction":"([A-Za-z]+)`)

var authoringVerbs = map[string]bool{
	"Updating": true, "Update": true, "Editing": true, "Edit": true,
	"Writing": true, "Write": true, "Creating": true, "Create": true,
}

// ReadAntigravity walks an Antigravity CLI data directory's per-conversation
// databases and returns each step that reached for a skill's SKILL.md. A
// database that cannot be opened or queried is skipped, never fatal — a live
// session holds a write lock on the conversation it is in.
func ReadAntigravity(dir string, cutoff time.Time) ([]Activation, error) {
	files, err := filepath.Glob(filepath.Join(dir, "conversations", "*.db"))
	if err != nil {
		return nil, err
	}
	var out []Activation
	for _, path := range files {
		out = append(out, readConversation(path, cutoff)...)
	}
	return out, nil
}

// readConversation filters by the database file's modification time: an
// Antigravity step carries no timestamp of its own, so the whole conversation
// is in or out of the window by when it was last written.
func readConversation(path string, cutoff time.Time) []Activation {
	info, err := os.Stat(path)
	if err != nil || info.ModTime().Before(cutoff) {
		return nil
	}
	db, err := sql.Open("sqlite", fmt.Sprintf("file:%s?mode=ro", path))
	if err != nil {
		return nil
	}
	defer db.Close()
	if err := db.Ping(); err != nil {
		return nil
	}
	rows, err := db.Query("SELECT metadata, render_info, step_payload FROM steps ORDER BY idx")
	if err != nil {
		return nil
	}
	defer rows.Close()

	session := strings.TrimSuffix(filepath.Base(path), ".db")
	var out []Activation
	for rows.Next() {
		var metadata, renderInfo, payload []byte
		if rows.Scan(&metadata, &renderInfo, &payload) != nil {
			continue
		}
		if act, ok := stepActivation(string(metadata)+string(renderInfo)+string(payload), session); ok {
			out = append(out, act)
		}
	}
	return out
}

// stepActivation reads one step's render blob. A step names at most one skill
// however many times its path appears across the blob's fields, so the first
// match decides.
func stepActivation(blob, session string) (Activation, bool) {
	m := skillPath.FindStringSubmatch(blob)
	if m == nil {
		return Activation{}, false
	}
	authoring := false
	if verb := toolAction.FindStringSubmatch(blob); verb != nil {
		authoring = authoringVerbs[verb[1]]
	}
	return Activation{
		Harness: "antigravity", Session: session,
		Kind: KindSkill, Name: m[1],
		Invocation: InvocationUnknown, Authoring: authoring,
	}, true
}
