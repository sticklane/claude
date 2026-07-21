package claude

import (
	"bufio"
	"bytes"
	"encoding/json"
	"os"
	"strings"
)

// SkillInvocation is one Skill tool_use paired with its tool_result, plus the
// context a skill audit needs: the <command-name> tag of the turn it fired in
// (if any) and whether a user turn opened before it. PrecededByUserTurn is
// false for a self-chain — a skill invoked inside an ongoing assistant turn
// with no new user message since the previous invocation.
type SkillInvocation struct {
	// Name is the invoked skill's name, from the Skill tool_use input's
	// "command" field.
	Name string
	// Args is the args string the Skill tool_use carried (its input "args"
	// field), "" when none.
	Args string
	// Result is the paired tool_result's text content, "" when unpaired.
	Result string
	// CommandTag is the <command-name> value of the turn this invocation fired
	// in, "" when the turn opened with no command tag.
	CommandTag string
	// PrecededByUserTurn reports whether a user turn opened after the previous
	// Skill invocation and before this one; false marks a self-chain.
	PrecededByUserTurn bool
}

// skillBlock parses the tool_use / tool_result fields SkillInvocations needs —
// input (for a Skill invocation's name and args) and content (a tool_result's
// text) — which the package's shared contentBlock does not carry.
type skillBlock struct {
	Type      string          `json:"type"`
	ID        string          `json:"id"`
	Name      string          `json:"name"`
	Text      string          `json:"text"`
	Input     json.RawMessage `json:"input"`
	ToolUseID string          `json:"tool_use_id"`
	Content   json.RawMessage `json:"content"`
}

// skillInput is a Skill tool_use's input payload: the invoked skill's name and
// any args passed to it.
type skillInput struct {
	Command string `json:"command"`
	Args    string `json:"args"`
}

// SkillInvocations walks one transcript in order and returns every Skill
// tool_use, paired with its tool_result content. It reuses the package's shared
// JSONL line type and <command-name> extraction (turnPrompt) rather than
// re-deriving them, and pairs each invocation with the tool_result carrying its
// tool_use id.
func SkillInvocations(path string) ([]SkillInvocation, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	type pending struct {
		inv SkillInvocation
		id  string
	}
	var invs []pending
	results := map[string]string{}
	curCommandTag := ""
	userTurnSinceLastSkill := false

	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 64*1024), maxLineSize)
	for sc.Scan() {
		raw := sc.Bytes()
		if len(bytes.TrimSpace(raw)) == 0 {
			continue
		}
		var l transcriptLine
		if json.Unmarshal(raw, &l) != nil {
			continue
		}
		if l.Message == nil {
			continue
		}
		switch l.Type {
		case "user":
			// A tool_result-carrying user line records results but never opens a
			// turn (turnPrompt rejects content holding a tool_result block).
			var blocks []skillBlock
			if json.Unmarshal(l.Message.Content, &blocks) == nil {
				for _, b := range blocks {
					if b.Type == "tool_result" && b.ToolUseID != "" {
						if _, dup := results[b.ToolUseID]; !dup {
							results[b.ToolUseID] = toolResultText(b.Content)
						}
					}
				}
			}
			if l.IsMeta || l.IsSidechain {
				continue
			}
			if _, cmdName, ok := turnPrompt(l.Message.Content); ok {
				curCommandTag = strings.TrimSpace(cmdName)
				userTurnSinceLastSkill = true
			}
		case "assistant":
			var blocks []skillBlock
			if json.Unmarshal(l.Message.Content, &blocks) != nil {
				continue
			}
			for _, b := range blocks {
				if b.Type != "tool_use" || b.Name != "Skill" {
					continue
				}
				var in skillInput
				_ = json.Unmarshal(b.Input, &in)
				invs = append(invs, pending{
					inv: SkillInvocation{
						Name:               in.Command,
						Args:               in.Args,
						CommandTag:         curCommandTag,
						PrecededByUserTurn: userTurnSinceLastSkill,
					},
					id: b.ID,
				})
				userTurnSinceLastSkill = false
			}
		}
	}

	out := make([]SkillInvocation, len(invs))
	for i, p := range invs {
		p.inv.Result = results[p.id]
		out[i] = p.inv
	}
	return out, nil
}

// toolResultText renders a tool_result block's content, which the transcript
// encodes as either a bare JSON string or an array of {type,text} blocks.
func toolResultText(raw json.RawMessage) string {
	if len(raw) == 0 {
		return ""
	}
	var s string
	if json.Unmarshal(raw, &s) == nil {
		return s
	}
	var blocks []skillBlock
	if json.Unmarshal(raw, &blocks) == nil {
		var b strings.Builder
		for _, blk := range blocks {
			if blk.Type == "text" {
				b.WriteString(blk.Text)
			}
		}
		return b.String()
	}
	return ""
}
