package claude

import (
	"bufio"
	"errors"
	"os"
	"strings"

	"github.com/sticklane/agentprof/internal/schema"
)

// denylistMarker replaces any frame that matched the denylist. It is distinct
// from scrub.go's [redacted] marker so the two mechanisms are separable in
// output: this one hides operator-listed strings, that one hides secrets.
const denylistMarker = "(redacted)"

// LoadDenylist reads path as one denied substring per line, trimming
// surrounding whitespace and skipping blank lines. A missing file is not an
// error — it means no denylist, so redaction is a no-op. The denylist file is
// intentionally never committed (SPEC R6); it lives only on the operator's
// machine.
func LoadDenylist(path string) ([]string, error) {
	f, err := os.Open(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil, nil
		}
		return nil, err
	}
	defer f.Close()

	var denied []string
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		denied = append(denied, line)
	}
	return denied, sc.Err()
}

// ScrubFrames replaces every frame in each sample's Stack that contains any
// denied substring with denylistMarker, applied to EVERY emitted frame string
// (project, turn, skill, agent, role/stage markers, model — all Stack
// elements) at sample-emit time (SPEC R6). An empty denylist leaves samples
// untouched. Skill frames flow here unscrubbed from normalizeSkillFrame, so
// this pass — not the turn-prompt secret scrub — is what closes that leak
// vector.
func ScrubFrames(samples []schema.Sample, denied []string) {
	if len(denied) == 0 {
		return
	}
	for _, s := range samples {
		for i, frame := range s.Stack {
			if containsAny(frame, denied) {
				s.Stack[i] = denylistMarker
			}
		}
	}
}

func containsAny(frame string, denied []string) bool {
	for _, d := range denied {
		if strings.Contains(frame, d) {
			return true
		}
	}
	return false
}
