// Package naming resolves descriptive names for uninformative turn frames
// (frame-naming SPEC R3-R6): a content-addressed on-disk cache backed by one
// batched LLM subprocess call for misses. Any failure degrades to the
// original snippet frames; naming is never fatal.
package naming

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/sticklane/agentprof/internal/schema"
)

// Candidate is one uninformative turn's name context, as sent to the namer
// subprocess. ID is Key(Prompt, ReplyHead).
type Candidate struct {
	ID        string `json:"id"`
	Prompt    string `json:"prompt"`
	ReplyHead string `json:"reply_head"`
}

// Namer proposes names for candidates by ID. Returned names are unvalidated.
type Namer interface {
	Name(cands []Candidate) (map[string]string, error)
}

// Key is the content address of a name context (R5): SHA-256 hex of
// prompt + NUL + replyHead.
func Key(prompt, replyHead string) string {
	return fmt.Sprintf("%x", sha256.Sum256([]byte(prompt+"\x00"+replyHead)))
}

// nameRe is the accepted-name shape (R4), checked after trim + lowercase.
var nameRe = regexp.MustCompile(`^[a-z0-9][a-z0-9 /._-]*$`)

// acceptName normalizes a proposed name and reports whether it is acceptable:
// non-empty, at most 48 runes, matching nameRe.
func acceptName(raw string) (string, bool) {
	name := strings.ToLower(strings.TrimSpace(raw))
	if name == "" || len([]rune(name)) > 48 || !nameRe.MatchString(name) {
		return "", false
	}
	return name, true
}

// Resolve returns ID -> accepted name for the candidates: cache hits first,
// then one namer call for the deduped misses. Accepted new names are written
// back to the cache atomically with sorted keys; a pure-hit run leaves the
// cache file untouched. Failures warn and degrade to fewer names.
func Resolve(cands []Candidate, n Namer, cachePath string, warn io.Writer) map[string]string {
	cache := loadCache(cachePath, warn)
	resolved := map[string]string{}
	var misses []Candidate
	missSeen := map[string]bool{}
	for _, c := range cands {
		if name, ok := cache[c.ID]; ok {
			resolved[c.ID] = name
		} else if !missSeen[c.ID] {
			missSeen[c.ID] = true
			misses = append(misses, c)
		}
	}
	if len(misses) == 0 {
		return resolved
	}

	proposed, err := n.Name(misses)
	if err != nil {
		fmt.Fprintf(warn, "agentprof: turn naming failed, keeping snippet frames: %v\n", err)
		return resolved
	}
	added := false
	for _, c := range misses {
		if name, ok := acceptName(proposed[c.ID]); ok {
			resolved[c.ID] = name
			cache[c.ID] = name
			added = true
		}
	}
	if added {
		if err := writeCache(cachePath, cache); err != nil {
			fmt.Fprintf(warn, "agentprof: writing turn-name cache: %v\n", err)
		}
	}
	return resolved
}

// loadCache reads the flat ID->name JSON object at path; a missing file is an
// empty cache, a corrupt one warns and is treated as empty (R5).
func loadCache(path string, warn io.Writer) map[string]string {
	cache := map[string]string{}
	data, err := os.ReadFile(path)
	if err != nil {
		return cache
	}
	if err := json.Unmarshal(data, &cache); err != nil {
		fmt.Fprintf(warn, "agentprof: corrupt turn-name cache %s, starting empty: %v\n", path, err)
		return map[string]string{}
	}
	return cache
}

// writeCache atomically rewrites the cache with sorted keys (encoding/json
// serializes map keys in sorted order).
func writeCache(path string, cache map[string]string) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(cache, "", "  ")
	if err != nil {
		return err
	}
	tmp, err := os.CreateTemp(filepath.Dir(path), ".turn-names-*")
	if err != nil {
		return err
	}
	if _, err := tmp.Write(append(data, '\n')); err != nil {
		tmp.Close()
		os.Remove(tmp.Name())
		return err
	}
	if err := tmp.Close(); err != nil {
		os.Remove(tmp.Name())
		return err
	}
	return os.Rename(tmp.Name(), path)
}

// RewriteFrames applies frame renames to every sample of one session,
// main-transcript and linked subagent stacks alike (R3): any stack frame
// equal to a renames key becomes its value.
func RewriteFrames(samples []schema.Sample, session string, renames map[string]string) {
	for _, s := range samples {
		if s.Labels["session"] != session {
			continue
		}
		for i, frame := range s.Stack {
			if name, ok := renames[frame]; ok {
				s.Stack[i] = name
			}
		}
	}
}

// cacheRoot is ${XDG_CACHE_HOME:-$HOME/.cache}/agentprof.
func cacheRoot() string {
	root := os.Getenv("XDG_CACHE_HOME")
	if root == "" {
		home, err := os.UserHomeDir()
		if err != nil {
			home = "."
		}
		root = filepath.Join(home, ".cache")
	}
	return filepath.Join(root, "agentprof")
}

// CachePath is the default turn-name cache location (R5).
func CachePath() string { return filepath.Join(cacheRoot(), "turn-names.json") }

// ConfigDir is the scratch CLAUDE_CONFIG_DIR for naming subprocesses (R4),
// keeping naming sessions out of the profiled ~/.claude tree.
func ConfigDir() string { return filepath.Join(cacheRoot(), "claude-config") }
