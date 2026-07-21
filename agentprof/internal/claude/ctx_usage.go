package claude

import (
	"encoding/json"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// ctxBashRe matches a shell command that invokes the `ctx` code-structure CLI
// with one of its verbs as a standalone token (ctx-dispatch-adoption R5). The
// leading class keeps a bare `ctx tree` or a chained `cd x && ctx refs Foo`
// while rejecting an identifier substring like `getExecutionCtx` (ctx preceded
// by a word char never matches), and `\b` after the verb rejects `treex`.
var ctxBashRe = regexp.MustCompile(`(^|[\s;&|(])ctx[ \t]+(tree|sig|refs|deps|at|map|notes|show)\b`)

// isCtxBashCommand reports whether a Bash tool_use command invokes `ctx <verb>`.
func isCtxBashCommand(cmd string) bool {
	return ctxBashRe.MatchString(cmd)
}

// isCtxSkillCommand reports whether a Skill tool_use command targets the ctx
// skill, matching both the namespaced `agentic:ctx` and a bare `ctx` — the same
// plugin-namespace stripping normalizeSkillFrame applies to skill attribution.
func isCtxSkillCommand(cmd string) bool {
	cmd = strings.TrimSpace(cmd)
	if _, name, ok := strings.Cut(cmd, ":"); ok {
		return name == "ctx"
	}
	return cmd == "ctx"
}

// ctxToolInput is the tool_use input ctx detection reads. A Bash call carries
// its shell command under "command"; a Skill call carries the invoked skill
// name under "skill" (the real Claude Code shape — NOT "command"; "command" is
// kept only as a defensive fallback for legacy/synthetic input shapes).
type ctxToolInput struct {
	Command string `json:"command"`
	Skill   string `json:"skill"`
}

// isCtxToolUse reports whether a tool_use block is a ctx-usage event: a Bash
// call running `ctx <verb>` or a Skill call invoking the ctx skill.
func isCtxToolUse(name string, input json.RawMessage) bool {
	if len(input) == 0 {
		return false
	}
	var in ctxToolInput
	if json.Unmarshal(input, &in) != nil {
		return false
	}
	switch name {
	case "Bash":
		return isCtxBashCommand(in.Command)
	case "Skill":
		skill := in.Skill
		if skill == "" {
			skill = in.Command
		}
		return isCtxSkillCommand(skill)
	}
	return false
}

// ctxUsageCount returns how many of a response's tool calls were ctx-usage
// events (SPEC R5): the per-response contribution to a session's ctx metric.
func ctxUsageCount(calls []toolCall) int64 {
	var n int64
	for _, c := range calls {
		if c.ctxUsage {
			n++
		}
	}
	return n
}

// isIndexedRepo reports whether cwd is the root of a ctx-indexed repo — a
// `.context/` directory present at cwd, resolved against the live filesystem at
// analysis time (SPEC R5). A session in a non-indexed repo contributes zero ctx
// usage even when its transcript carries ctx-shaped commands.
func isIndexedRepo(cwd string) bool {
	if cwd == "" {
		return false
	}
	info, err := os.Stat(filepath.Join(cwd, ".context"))
	return err == nil && info.IsDir()
}
