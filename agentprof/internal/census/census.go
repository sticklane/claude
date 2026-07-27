// Package census counts skill and tool use across the agent harnesses
// installed on one machine — Claude Code, Codex, and Antigravity — so a skill
// author can see what is actually reached for, from which harness, and how
// often the model chose it rather than being told to.
package census

import (
	"sort"
	"strings"
	"time"
)

// Kind separates a skill activation from an ordinary tool call; the two share
// a namespace (a `ctx` skill and a `ctx` tool both exist) and are never merged.
type Kind string

const (
	KindSkill Kind = "skill"
	KindTool  Kind = "tool"
)

// Invocation records who chose the skill. Only Claude Code's transcript
// distinguishes a slash command from a model decision; Codex and Antigravity
// leave a SKILL.md read either way, so their activations are Unknown.
const (
	InvocationAuto     = "auto"
	InvocationExplicit = "explicit"
	InvocationUnknown  = "unknown"
)

// Activation is one recorded reach for a skill or tool in one session.
// Authoring marks a record that changed the skill's own source rather than
// used it — editing `gate/SKILL.md` is not evidence that `gate` is useful.
type Activation struct {
	Harness    string    `json:"harness"`
	Session    string    `json:"session"`
	Project    string    `json:"project"`
	Kind       Kind      `json:"kind"`
	Name       string    `json:"name"`
	Invocation string    `json:"invocation"`
	Authoring  bool      `json:"authoring,omitempty"`
	At         time.Time `json:"at,omitempty"`
}

// Stat is one name's aggregate across every harness in the window. Total
// counts uses only; Authoring counts source edits, reported alongside so a
// skill that only ever gets edited reads as unused rather than busy.
type Stat struct {
	Name      string         `json:"name"`
	Kind      Kind           `json:"kind"`
	Total     int            `json:"total"`
	ByHarness map[string]int `json:"by_harness"`
	Auto      int            `json:"auto"`
	Explicit  int            `json:"explicit"`
	Sessions  int            `json:"sessions"`
	Authoring int            `json:"authoring,omitempty"`
	LastUsed  time.Time      `json:"last_used,omitempty"`
}

// NormalizeName strips the plugin namespace a harness prepends when it
// resolves a skill from an installed plugin rather than a checkout, so
// `agentic:critique` and `critique` aggregate as one skill.
func NormalizeName(name string) string {
	if i := strings.LastIndex(name, ":"); i >= 0 {
		return name[i+1:]
	}
	return name
}

type statKey struct {
	name string
	kind Kind
}

// Aggregate folds activations into one Stat per (name, kind), ordered by use
// count descending and then by name so equal-count rows stay stable.
func Aggregate(activations []Activation) []Stat {
	stats := map[statKey]*Stat{}
	sessions := map[statKey]map[string]bool{}
	for _, a := range activations {
		key := statKey{name: NormalizeName(a.Name), kind: a.Kind}
		s, ok := stats[key]
		if !ok {
			s = &Stat{Name: key.name, Kind: key.kind, ByHarness: map[string]int{}}
			stats[key] = s
			sessions[key] = map[string]bool{}
		}
		if a.Authoring {
			s.Authoring++
			continue
		}
		s.Total++
		s.ByHarness[a.Harness]++
		switch a.Invocation {
		case InvocationAuto:
			s.Auto++
		case InvocationExplicit:
			s.Explicit++
		}
		sessions[key][a.Session] = true
		if a.At.After(s.LastUsed) {
			s.LastUsed = a.At
		}
	}

	out := make([]Stat, 0, len(stats))
	for key, s := range stats {
		s.Sessions = len(sessions[key])
		out = append(out, *s)
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].Total != out[j].Total {
			return out[i].Total > out[j].Total
		}
		return out[i].Name < out[j].Name
	})
	return out
}

// Unused returns the installed skills with no use in the window, sorted by
// name. A skill whose only records are Authoring counts as unused.
func Unused(installed []string, stats []Stat) []string {
	used := map[string]bool{}
	for _, s := range stats {
		if s.Kind == KindSkill && s.Total > 0 {
			used[s.Name] = true
		}
	}
	var out []string
	for _, name := range installed {
		if !used[NormalizeName(name)] {
			out = append(out, NormalizeName(name))
		}
	}
	sort.Strings(out)
	return out
}
