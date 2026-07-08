// Package costsummary aggregates canonical samples into the pre-aggregated
// "Cost (7d)" summary JSON consumed by the workboard panel
// (workboard-weekly-cost-view R3). agentprof owns the frame-hierarchy
// convention (project/skill/agent/model position in the leaf-last stack), so
// the grouping lives here rather than being parsed out of `go tool pprof -top`.
package costsummary

import (
	"strings"

	"github.com/sticklane/agentprof/internal/schema"
)

// Summary is the pre-aggregated cost/token view. Each group maps a dimension
// value (project name, skill frame, agent frame, or model name) to a
// sample_type -> total map; Totals sums each sample_type across all samples.
// Field order fixes the JSON key order.
type Summary struct {
	ByProject     map[string]map[string]int64 `json:"by_project"`
	BySkill       map[string]map[string]int64 `json:"by_skill"`
	ByAgentType   map[string]map[string]int64 `json:"by_agent_type"`
	ByModel       map[string]map[string]int64 `json:"by_model"`
	Totals        map[string]int64            `json:"totals"`
	SessionsAdded int                         `json:"sessions_added"`
}

// Build aggregates forGrouping into the by-dimension groups and totals, and
// counts sessions_added from fresh only. In non-merge mode both arguments are
// the fresh Collect() output; in --merge mode forGrouping is the final merged,
// post-eviction rolling window while fresh is this run's Collect() output (R3).
func Build(forGrouping, fresh []schema.Sample) Summary {
	s := Summary{
		ByProject:   map[string]map[string]int64{},
		BySkill:     map[string]map[string]int64{},
		ByAgentType: map[string]map[string]int64{},
		ByModel:     map[string]map[string]int64{},
		Totals:      map[string]int64{},
	}
	for _, smp := range forGrouping {
		if len(smp.Stack) == 0 {
			continue
		}
		proj := smp.Stack[0]
		sk := skill(smp.Stack)
		agent, hasAgent := agentType(smp.Stack)
		model, hasModel := modelLeaf(smp.Stack)
		for st, v := range smp.Values {
			add(s.ByProject, proj, st, v)
			add(s.BySkill, sk, st, v)
			if hasAgent {
				add(s.ByAgentType, agent, st, v)
			}
			if hasModel {
				add(s.ByModel, model, st, v)
			}
			s.Totals[st] += v
		}
	}
	s.SessionsAdded = distinctSessions(fresh)
	return s
}

// add folds value v for sample_type st into group[name], creating the inner map
// on first use.
func add(group map[string]map[string]int64, name, st string, v int64) {
	inner := group[name]
	if inner == nil {
		inner = map[string]int64{}
		group[name] = inner
	}
	inner[st] += v
}

// skill returns the first frame matching ^skill: or exactly "(no skill)";
// samples with no such frame (e.g. an (unlinked) subagent stack) bucket under
// "(no skill)" rather than being dropped.
func skill(stack []string) string {
	for _, f := range stack {
		if strings.HasPrefix(f, "skill:") || f == "(no skill)" {
			return f
		}
	}
	return "(no skill)"
}

// agentType returns the first frame matching ^agent:; the boolean is false when
// the stack carries no agent frame (that sample joins no by_agent_type bucket).
func agentType(stack []string) (string, bool) {
	for _, f := range stack {
		if strings.HasPrefix(f, "agent:") {
			return f, true
		}
	}
	return "", false
}

// modelLeaf returns the last (leaf) frame that isn't a tool:/role:/stage:
// frame — forward-compatible with the instrumentation spec's new frame kinds,
// which are ignored here.
func modelLeaf(stack []string) (string, bool) {
	for i := len(stack) - 1; i >= 0; i-- {
		f := stack[i]
		if strings.HasPrefix(f, "tool:") || strings.HasPrefix(f, "role:") || strings.HasPrefix(f, "stage:") {
			continue
		}
		return f, true
	}
	return "", false
}

// distinctSessions counts distinct non-empty Labels["session"] values across
// the fresh samples (sessions touched since the last refresh).
func distinctSessions(fresh []schema.Sample) int {
	seen := map[string]struct{}{}
	for _, s := range fresh {
		if sess := s.Labels["session"]; sess != "" {
			seen[sess] = struct{}{}
		}
	}
	return len(seen)
}
