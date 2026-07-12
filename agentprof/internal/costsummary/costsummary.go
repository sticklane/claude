// Package costsummary aggregates canonical samples into the pre-aggregated
// "Cost (7d)" summary JSON consumed by the workboard panel
// (workboard-weekly-cost-view R3). agentprof owns the frame-hierarchy
// convention (project/skill/agent/model position in the leaf-last stack), so
// the grouping lives here rather than being parsed out of `go tool pprof -top`.
package costsummary

import (
	"math"
	"sort"
	"strings"

	"github.com/sticklane/agentprof/internal/schema"
)

// Summary is the pre-aggregated cost/token view. Each group maps a dimension
// value (project name, skill frame, agent frame, or model name) to a
// sample_type -> total map; Totals sums each sample_type across all samples.
// Field order fixes the JSON key order.
//
// by_model carries two non-model sentinel rows: `(tools)` holds the duration of
// tool-duration samples (which have no model frame), and `<synthetic>` is the
// explicitly-labeled row for synthetic pseudo-model samples — its bracketed name
// marks it as non-model, and its `calls` are kept as-is rather than excluded
// (SPEC R4). Neither key is ever `main`.
type Summary struct {
	ByProject     map[string]map[string]int64 `json:"by_project"`
	BySkill       map[string]map[string]int64 `json:"by_skill"`
	ByAgentType   map[string]map[string]int64 `json:"by_agent_type"`
	ByModel       map[string]map[string]int64 `json:"by_model"`
	Totals        map[string]int64            `json:"totals"`
	SessionsAdded int                         `json:"sessions_added"`
	Reprime       Reprime                     `json:"reprime"`
	Sessions      map[string]SessionStat      `json:"sessions"`
	UntypedFanout UntypedFanout               `json:"untyped_fanout"`
}

// UntypedFanout is the guard metric for untyped agent dispatch (SPEC R4): the
// calls and cost_microusd flowing through samples whose stack passes through an
// untyped catch-all agent frame, split by model, plus the deepest adjacent
// untyped-frame run observed. The untyped set is the EXACT-match enumeration
// untypedAgents below — any other agent:* frame (e.g. agent:claude-code-guide,
// which merely shares the agent:claude prefix) is typed: excluded from the
// rollup and breaking a depth chain. Additive only, like Reprime.
type UntypedFanout struct {
	Calls        int64                       `json:"calls"`
	CostMicrousd int64                       `json:"cost_microusd"`
	ByModel      map[string]map[string]int64 `json:"by_model"`
	MaxDepth     int64                       `json:"max_depth"`
}

// untypedAgents is the exact-match set of untyped catch-all agent frames — the
// default-when-no-name types whose nested dispatch compounds the caller's model
// (SPEC R4). Membership is exact, never a prefix match.
var untypedAgents = map[string]struct{}{
	"agent:claude":                  {},
	"agent:agentic:claude":          {},
	"agent:general-purpose":         {},
	"agent:agentic:general-purpose": {},
}

// Reprime rolls up the samples labeled reprime=true (cache-reprime SPEC R2):
// how many there are, how much prompt cache they re-wrote, their cost, and a
// per-project breakdown ({count, cache_write_tokens, cost_microusd} per project).
type Reprime struct {
	Count            int64                       `json:"count"`
	CacheWriteTokens int64                       `json:"cache_write_tokens"`
	CostMicrousd     int64                       `json:"cost_microusd"`
	ByProject        map[string]map[string]int64 `json:"by_project"`
}

// SessionStat is one session's context-size profile (cache-reprime SPEC R3),
// computed over that session's MAIN-LOOP model calls only (subagent calls carry
// the parent's session label but are excluded — main-loop context is the cost
// driver; see the spec's Open questions). p50/p90 are over per-call context
// size (cache_read_tokens + input_tokens).
// ReprimeCount and ReprimeCostMicrousd aggregate this session's own samples
// labeled reprime=true — the per-session slice of the top-level Reprime rollup.
type SessionStat struct {
	Project             string `json:"project"`
	Calls               int64  `json:"calls"`
	CostMicrousd        int64  `json:"cost_microusd"`
	P50Ctx              int64  `json:"p50_ctx"`
	P90Ctx              int64  `json:"p90_ctx"`
	ReprimeCount        int64  `json:"reprime_count"`
	ReprimeCostMicrousd int64  `json:"reprime_cost_microusd"`
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
	s.Reprime = reprimeRollup(forGrouping)
	s.Sessions = sessionStats(forGrouping)
	s.UntypedFanout = untypedFanout(forGrouping)
	return s
}

// untypedFanout rolls up the calls and cost of samples that pass through an
// untyped catch-all agent frame, split by model, and records the deepest
// adjacent untyped-frame run observed (SPEC R4). Computed from forGrouping, so
// the --merge rolling-window path is respected exactly like reprimeRollup.
func untypedFanout(forGrouping []schema.Sample) UntypedFanout {
	uf := UntypedFanout{ByModel: map[string]map[string]int64{}}
	for _, smp := range forGrouping {
		depth := untypedRunDepth(smp.Stack)
		if depth == 0 {
			continue
		}
		if int64(depth) > uf.MaxDepth {
			uf.MaxDepth = int64(depth)
		}
		model, _ := modelLeaf(smp.Stack)
		if v, ok := smp.Values["calls"]; ok {
			uf.Calls += v
			add(uf.ByModel, model, "calls", v)
		}
		if v, ok := smp.Values["cost_microusd"]; ok {
			uf.CostMicrousd += v
			add(uf.ByModel, model, "cost_microusd", v)
		}
	}
	return uf
}

// untypedRunDepth returns the length of the longest run of adjacent untyped
// agent frames in stack (SPEC R4 edge rule). Only agent: frames matter: an
// untyped-set frame extends the current run, any other agent: frame (a typed
// agent, e.g. agent:scout or agent:claude-code-guide) breaks it, and every
// non-agent frame (wf:/stage:/role markers, model, main, project) is
// transparent — skipped without breaking adjacency. 0 means the stack passes
// through no untyped frame at all.
func untypedRunDepth(stack []string) int {
	longest, run := 0, 0
	for _, f := range stack {
		if !strings.HasPrefix(f, "agent:") {
			continue
		}
		if _, ok := untypedAgents[f]; ok {
			run++
			if run > longest {
				longest = run
			}
		} else {
			run = 0
		}
	}
	return longest
}

// reprimeRollup sums the samples labeled reprime=true over forGrouping (SPEC R2).
func reprimeRollup(forGrouping []schema.Sample) Reprime {
	r := Reprime{ByProject: map[string]map[string]int64{}}
	for _, smp := range forGrouping {
		if smp.Labels["reprime"] != "true" || len(smp.Stack) == 0 {
			continue
		}
		write := smp.Values["cache_write_tokens"]
		cost := smp.Values["cost_microusd"]
		r.Count++
		r.CacheWriteTokens += write
		r.CostMicrousd += cost
		proj := smp.Stack[0]
		add(r.ByProject, proj, "count", 1)
		add(r.ByProject, proj, "cache_write_tokens", write)
		add(r.ByProject, proj, "cost_microusd", cost)
	}
	return r
}

// sessionStats builds the per-session context-size profile over MAIN-LOOP model
// calls only — samples with no agent: frame that carry a "calls" value (tool and
// subagent samples are excluded) (SPEC R3).
func sessionStats(forGrouping []schema.Sample) map[string]SessionStat {
	type acc struct {
		project     string
		calls       int64
		cost        int64
		ctx         []int64
		reprimeN    int64
		reprimeCost int64
	}
	accs := map[string]*acc{}
	for _, smp := range forGrouping {
		if len(smp.Stack) == 0 {
			continue
		}
		if _, isCall := smp.Values["calls"]; !isCall {
			continue
		}
		if _, hasAgent := agentType(smp.Stack); hasAgent {
			continue
		}
		sess := smp.Labels["session"]
		if sess == "" {
			continue
		}
		a := accs[sess]
		if a == nil {
			a = &acc{project: smp.Stack[0]}
			accs[sess] = a
		}
		a.calls += smp.Values["calls"]
		a.cost += smp.Values["cost_microusd"]
		a.ctx = append(a.ctx, smp.Values["cache_read_tokens"]+smp.Values["input_tokens"])
		if smp.Labels["reprime"] == "true" {
			a.reprimeN++
			a.reprimeCost += smp.Values["cost_microusd"]
		}
	}
	out := map[string]SessionStat{}
	for sess, a := range accs {
		sort.Slice(a.ctx, func(i, j int) bool { return a.ctx[i] < a.ctx[j] })
		out[sess] = SessionStat{
			Project:             a.project,
			Calls:               a.calls,
			CostMicrousd:        a.cost,
			P50Ctx:              percentile(a.ctx, 50),
			P90Ctx:              percentile(a.ctx, 90),
			ReprimeCount:        a.reprimeN,
			ReprimeCostMicrousd: a.reprimeCost,
		}
	}
	return out
}

// percentile returns the nearest-rank percentile p (0-100) of sorted (ascending)
// values; 0 for an empty slice.
func percentile(sorted []int64, p float64) int64 {
	n := len(sorted)
	if n == 0 {
		return 0
	}
	rank := int(math.Ceil(p / 100 * float64(n)))
	if rank < 1 {
		rank = 1
	}
	if rank > n {
		rank = n
	}
	return sorted[rank-1]
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

// toolsSentinel is the by_model key for samples that carry no model frame —
// tool-duration samples, whose model leaf was replaced by a tool:<name> frame.
// Booking their duration here keeps the structural `main`/`agent:` frames out
// of by_model, where they read as bogus "models" (SPEC R4).
const toolsSentinel = "(tools)"

// modelLeaf returns the model frame for a sample: the leaf frame after skipping
// any trailing tool:/role:/stage: marker frames (forward-compatible with the
// instrumentation spec's new frame kinds). A sample carries no model frame when
// that leaf-most non-marker frame is structural — the `main` loop frame or an
// `agent:` frame, which are the model slot's parents; such samples (main-loop
// and subagent tool-duration samples) bucket under the (tools) sentinel so
// `main` never appears as a by_model key (SPEC R4). The `<synthetic>` leaf is a
// non-model pseudo-frame, but is left as-is: it keeps its own explicitly-labeled
// by_model row (its bracketed name marks it as synthetic) rather than being
// folded into (tools). The bool is always true for a non-empty stack — every
// sample maps to some by_model bucket, a real model or (tools).
func modelLeaf(stack []string) (string, bool) {
	for i := len(stack) - 1; i >= 0; i-- {
		f := stack[i]
		if strings.HasPrefix(f, "tool:") || strings.HasPrefix(f, "role:") || strings.HasPrefix(f, "stage:") {
			continue
		}
		if f == "main" || strings.HasPrefix(f, "agent:") {
			return toolsSentinel, true
		}
		return f, true
	}
	return toolsSentinel, true
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
