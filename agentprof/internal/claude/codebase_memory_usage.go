package claude

import (
	"encoding/json"
	"regexp"
	"strings"
)

var codebaseMemoryCLI = regexp.MustCompile(
	`(^|[[:space:];&|(])([^[:space:];&|(]*/)?(agentic-)?codebase-memory-mcp[[:space:]]+cli[[:space:]]+` +
		`(index_repository|list_projects|index_status|search_graph|trace_path|` +
		`detect_changes|query_graph|get_graph_schema|get_code_snippet|` +
		`get_architecture|search_code)\b`,
)

var codebaseMemoryQueries = []string{
	"index_repository",
	"list_projects",
	"index_status",
	"search_graph",
	"trace_path",
	"detect_changes",
	"query_graph",
	"get_graph_schema",
	"get_code_snippet",
	"get_architecture",
	"search_code",
}

type codebaseMemoryToolInput struct {
	Command string `json:"command"`
	Skill   string `json:"skill"`
}

func isCodebaseMemorySkill(command string) bool {
	command = strings.TrimSpace(command)
	if _, name, ok := strings.Cut(command, ":"); ok {
		return name == "codebase-memory"
	}
	return command == "codebase-memory"
}

func isCodebaseMemoryQuery(name string) bool {
	normalized := strings.ReplaceAll(strings.ToLower(name), "-", "_")
	for _, query := range codebaseMemoryQueries {
		if strings.Contains(normalized, "codebase_memory") &&
			strings.HasSuffix(normalized, "__"+query) {
			return true
		}
	}
	return false
}

func isCodebaseMemoryToolUse(name string, input json.RawMessage) bool {
	if isCodebaseMemoryQuery(name) {
		return true
	}
	if len(input) == 0 {
		return false
	}
	var parsed codebaseMemoryToolInput
	if json.Unmarshal(input, &parsed) != nil {
		return false
	}
	switch name {
	case "Bash":
		return codebaseMemoryCLI.MatchString(parsed.Command)
	case "Skill":
		skill := parsed.Skill
		if skill == "" {
			skill = parsed.Command
		}
		return isCodebaseMemorySkill(skill)
	}
	return false
}

func codebaseMemoryUsageCount(calls []toolCall) int64 {
	var count int64
	for _, call := range calls {
		if call.codebaseMemoryUsage {
			count++
		}
	}
	return count
}
