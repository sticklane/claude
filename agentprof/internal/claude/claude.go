// Package claude turns a local Claude Code data directory (~/.claude) into
// canonical samples: one per deduped assistant API response, with stack
// [project, turn, skill, "main", agent:*..., model] (agentprof-turns SPEC
// R1-R6). Conversation turns are frames, and subagents nest under the turn
// (and agent) that spawned them via tool_use id linkage. Workflow-spawned
// subagents (under subagents/workflows/<runId>/, meta without a toolUseId)
// link via their path runId joined to the Workflow tool_result line, and
// insert a wf:<workflowName> frame before their agent: frame — once per
// spawn chain (workflow-linkage SPEC R1-R5). Subagents whose spawn chain
// cannot be resolved get [project, "(unlinked)", agent:*, model]. All reads
// are read-only.
package claude

import (
	"bufio"
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
	"time"

	"github.com/sticklane/agentprof/internal/pricing"
	"github.com/sticklane/agentprof/internal/schema"
)

// maxLineSize bounds transcript line length; real transcripts carry pasted
// file contents on a single JSONL line, so allow generously large lines.
const maxLineSize = 16 * 1024 * 1024

// maxSpawnDepth bounds spawn-chain resolution (R4); a chain longer than this
// (or a toolUseId cycle) is treated as unlinked rather than recursed forever.
const maxSpawnDepth = 16

// Turn is per-turn naming context for one prompt-opened main-transcript turn
// (frame-naming SPEC R3): prompt and reply head are scrubbed and truncated to
// 500 runes, and Candidate marks turns whose frame is uninformative (R2).
type Turn struct {
	Session   string
	Ordinal   int
	Frame     string
	Prompt    string
	ReplyHead string
	Candidate bool
}

// Collect walks dir (a ~/.claude-shaped tree) and returns one sample per
// deduped assistant API response, per-turn naming context, plus the count of
// unparseable lines skipped. A session is included iff the max mtime across
// its main transcript and subagent files is not before cutoff; an in-window
// session contributes all its files.
func Collect(dir string, cutoff time.Time) ([]schema.Sample, []Turn, int, error) {
	sessions, err := enumerate(dir)
	if err != nil {
		return nil, nil, 0, err
	}
	var samples []schema.Sample
	var turns []Turn
	skipped := 0
	for _, sess := range sessions {
		in, err := sess.inWindow(cutoff)
		if err != nil {
			return nil, nil, 0, err
		}
		if !in {
			continue
		}
		s, ts, n, err := sess.collect()
		if err != nil {
			return nil, nil, 0, err
		}
		samples = append(samples, s...)
		turns = append(turns, ts...)
		skipped += n
	}
	return samples, turns, skipped, nil
}

// agentFile is one subagent transcript plus its stack frame
// ("agent:{agentType}" from the sibling meta file, else "agent:(unknown)"),
// the toolUseId linking it to the tool_use block that spawned it, and — for
// files under subagents/workflows/<runId>/ — the runId from the path, used as
// a linkage fallback when the meta carries no toolUseId (workflow-linkage
// SPEC R2).
type agentFile struct {
	path      string
	frame     string
	toolUseID string
	runID     string
}

// session is one main transcript with its subagent transcripts.
type session struct {
	mainPath  string
	mungedDir string // directory name under projects/ (cwd fallback)
	id        string // sessionId = main transcript basename sans .jsonl
	agents    []agentFile
}

// enumerate finds main transcripts at {dir}/projects/*/*.jsonl and, for each,
// recursively walks {dir}/projects/*/{sessionId}/ for agent-*.jsonl at any
// depth. Glob and WalkDir order lexically, keeping output deterministic.
func enumerate(dir string) ([]session, error) {
	mains, err := filepath.Glob(filepath.Join(dir, "projects", "*", "*.jsonl"))
	if err != nil {
		return nil, err
	}
	var sessions []session
	for _, mainPath := range mains {
		sess := session{
			mainPath:  mainPath,
			mungedDir: filepath.Base(filepath.Dir(mainPath)),
			id:        strings.TrimSuffix(filepath.Base(mainPath), ".jsonl"),
		}
		sessDir := filepath.Join(filepath.Dir(mainPath), sess.id)
		err := filepath.WalkDir(sessDir, func(path string, d fs.DirEntry, err error) error {
			if err != nil {
				if errors.Is(err, fs.ErrNotExist) {
					return nil // session has no subagent directory
				}
				return err
			}
			name := d.Name()
			if d.IsDir() || !strings.HasPrefix(name, "agent-") || !strings.HasSuffix(name, ".jsonl") {
				return nil
			}
			agentID := strings.TrimSuffix(strings.TrimPrefix(name, "agent-"), ".jsonl")
			meta := filepath.Join(filepath.Dir(path), "agent-"+agentID+".meta.json")
			frame, toolUseID := readAgentMeta(meta)
			sess.agents = append(sess.agents, agentFile{
				path: path, frame: frame, toolUseID: toolUseID,
				runID: workflowRunID(path),
			})
			return nil
		})
		if err != nil {
			return nil, err
		}
		sessions = append(sessions, sess)
	}
	return sessions, nil
}

// workflowRunID extracts <runId> from a path containing a
// .../subagents/workflows/<runId>/... segment, or "" for non-workflow paths.
func workflowRunID(path string) string {
	comps := strings.Split(filepath.ToSlash(path), "/")
	for i := 0; i < len(comps)-3; i++ {
		if comps[i] == "subagents" && comps[i+1] == "workflows" {
			return comps[i+2]
		}
	}
	return ""
}

// readAgentMeta reads agent-{agentId}.meta.json for the agentType and
// toolUseId; a missing or unusable meta file yields "agent:(unknown)" and no
// toolUseId (-> unlinked per R5).
func readAgentMeta(metaPath string) (frame, toolUseID string) {
	data, err := os.ReadFile(metaPath)
	if err != nil {
		return "agent:(unknown)", ""
	}
	var meta struct {
		AgentType string `json:"agentType"`
		ToolUseID string `json:"toolUseId"`
	}
	if json.Unmarshal(data, &meta) != nil {
		return "agent:(unknown)", ""
	}
	frame = "agent:(unknown)"
	if meta.AgentType != "" {
		frame = "agent:" + meta.AgentType
	}
	return frame, meta.ToolUseID
}

// inWindow reports whether the max mtime across the session's files is not
// before cutoff.
func (s session) inWindow(cutoff time.Time) (bool, error) {
	paths := []string{s.mainPath}
	for _, a := range s.agents {
		paths = append(paths, a.path)
	}
	var max time.Time
	for _, p := range paths {
		fi, err := os.Stat(p)
		if err != nil {
			return false, err
		}
		if fi.ModTime().After(max) {
			max = fi.ModTime()
		}
	}
	return !max.Before(cutoff), nil
}

// spawnCtx is where a tool_use id was seen: the transcript containing it, the
// turn open at that line (meaningful for the main transcript only), and that
// line's attributionSkill (R4).
type spawnCtx struct {
	path    string
	turnIdx int
	skill   string
}

// collect parses the session's transcripts into samples. The project frame is
// the basename of the first cwd in the MAIN transcript, applied to every
// sample of the session including subagents (falling back to the munged
// directory name under projects/). Main-transcript samples get
// [project, turn, skill, "main", model]; each subagent's samples get its
// resolved spawn prefix + [agent:{type}, model], or the R5 unlinked stack.
func (s session) collect() ([]schema.Sample, []Turn, int, error) {
	mainP, err := parseTranscript(s.mainPath)
	if err != nil {
		return nil, nil, 0, err
	}
	project := s.mungedDir
	if mainP.firstCwd != "" {
		project = filepath.Base(mainP.firstCwd)
	}
	skipped := mainP.skipped

	byPath := map[string]parsed{s.mainPath: mainP}
	agentByPath := map[string]agentFile{}
	for _, a := range s.agents {
		p, err := parseTranscript(a.path)
		if err != nil {
			return nil, nil, 0, err
		}
		skipped += p.skipped
		byPath[a.path] = p
		agentByPath[a.path] = a
	}

	// Spawn and workflow-run maps: first occurrence of a tool_use id / runId
	// wins, in scan order = lexicographic file path, then file order within a
	// file (R4, workflow-linkage SPEC R1).
	paths := make([]string, 0, len(byPath))
	for p := range byPath {
		paths = append(paths, p)
	}
	slices.Sort(paths)
	spawn := map[string]spawnCtx{}
	runs := map[string]runRef{}
	for _, path := range paths {
		for _, tu := range byPath[path].toolUses {
			if _, dup := spawn[tu.id]; !dup {
				spawn[tu.id] = spawnCtx{path: path, turnIdx: tu.turnIdx, skill: tu.skill}
			}
		}
		for _, run := range byPath[path].runs {
			if _, dup := runs[run.runID]; !dup {
				runs[run.runID] = run
			}
		}
	}

	// resolve walks a subagent's spawn chain toward the main transcript,
	// returning the stack prefix above the agent's own frame and the
	// main-session turn ordinal. An agent whose meta carries no toolUseId
	// falls back to its path runId via the run map, and its prefix then ends
	// in a wf:<workflowName> frame (workflow-linkage SPEC R2/R3). Unlinked
	// ancestors, cycles, and chains longer than maxSpawnDepth all report
	// ok=false (R4/R5).
	var resolve func(a agentFile, depth int) (prefix []string, turnIdx int, ok bool)
	resolve = func(a agentFile, depth int) ([]string, int, bool) {
		if depth >= maxSpawnDepth {
			return nil, 0, false
		}
		toolUseID, wfFrame := a.toolUseID, ""
		if toolUseID == "" {
			run, found := runs[a.runID]
			if !found {
				return nil, 0, false
			}
			toolUseID = run.toolUseID
			name := run.workflowName
			if name == "" {
				name = "(unknown)"
			}
			wfFrame = "wf:" + name
		}
		ctx, found := spawn[toolUseID]
		if !found {
			return nil, 0, false
		}
		var prefix []string
		turnIdx := ctx.turnIdx
		if ctx.path == s.mainPath {
			prefix = []string{project, mainP.turns[ctx.turnIdx].frame, ctx.skill, "main"}
		} else {
			parent := agentByPath[ctx.path]
			pp, ti, ok := resolve(parent, depth+1)
			if !ok {
				return nil, 0, false
			}
			prefix, turnIdx = slices.Concat(pp, []string{parent.frame}), ti
		}
		if wfFrame != "" {
			prefix = append(prefix, wfFrame)
		}
		return prefix, turnIdx, true
	}

	var out []schema.Sample
	for _, r := range mainP.responses {
		stack := []string{project, mainP.turns[r.turnIdx].frame, r.skill, "main", r.model}
		out = append(out, r.sample(stack, s.id, fmt.Sprintf("%02d", r.turnIdx)))
	}
	for _, a := range s.agents {
		prefix, turnIdx, linked := resolve(a, 0)
		turn := ""
		if linked {
			turn = fmt.Sprintf("%02d", turnIdx)
		}
		for _, r := range byPath[a.path].responses {
			var stack []string
			if linked {
				stack = slices.Concat(prefix, []string{a.frame, r.model})
			} else {
				stack = []string{project, "(unlinked)", a.frame, r.model}
			}
			out = append(out, r.sample(stack, s.id, turn))
		}
	}

	// Naming context: main-transcript prompt-opened turns only (the synthetic
	// t00 at index 0 is never renamed).
	var turns []Turn
	for i, tr := range mainP.turns[1:] {
		turns = append(turns, Turn{
			Session: s.id, Ordinal: i + 1, Frame: tr.frame,
			Prompt: tr.prompt, ReplyHead: tr.replyHead, Candidate: tr.candidate,
		})
	}
	return out, turns, skipped, nil
}

// response is one deduped assistant API response.
type response struct {
	time    time.Time
	skill   string
	model   string
	usage   pricing.Usage
	turnIdx int // turn open at the response's first line
}

// toolUseRef is one tool_use block id with its spawning line's context.
type toolUseRef struct {
	id      string
	turnIdx int
	skill   string
}

// runRef is one workflow run recorded from a user line whose toolUseResult
// carries a wf_-prefixed runId: the tool_use_id of the line's tool_result
// content block joins the run's agents to the spawning Workflow tool call
// (workflow-linkage SPEC R1).
type runRef struct {
	runID        string
	toolUseID    string
	workflowName string
}

// turnRec is one turn's frame plus its naming context (frame-naming SPEC
// R2-R4): the scrubbed collapsed prompt and first assistant text, each capped
// at 500 runes, and whether the frame is uninformative.
type turnRec struct {
	frame     string
	prompt    string
	replyHead string
	candidate bool
}

// parsed is everything one transcript contributes: deduped responses, turns
// by ordinal (index 0 is the synthetic pre-prompt turn), tool_use spawn
// references, workflow-run references, the first cwd, and the
// unparseable-line count.
type parsed struct {
	responses []response
	turns     []turnRec
	toolUses  []toolUseRef
	runs      []runRef
	firstCwd  string
	skipped   int
}

type contentBlock struct {
	Type      string `json:"type"`
	Text      string `json:"text"`
	ID        string `json:"id"`
	ToolUseID string `json:"tool_use_id"`
}

type transcriptLine struct {
	Type             string          `json:"type"`
	IsMeta           bool            `json:"isMeta"`
	IsSidechain      bool            `json:"isSidechain"`
	Timestamp        string          `json:"timestamp"`
	Cwd              string          `json:"cwd"`
	AttributionSkill string          `json:"attributionSkill"`
	RequestID        string          `json:"requestId"`
	ToolUseResult    json.RawMessage `json:"toolUseResult"`
	Message          *struct {
		ID      string          `json:"id"`
		Model   string          `json:"model"`
		Content json.RawMessage `json:"content"` // string or block array
		Usage   *struct {
			InputTokens              int64 `json:"input_tokens"`
			OutputTokens             int64 `json:"output_tokens"`
			CacheReadInputTokens     int64 `json:"cache_read_input_tokens"`
			CacheCreationInputTokens int64 `json:"cache_creation_input_tokens"`
			CacheCreation            *struct {
				Ephemeral5m *int64 `json:"ephemeral_5m_input_tokens"`
				Ephemeral1h *int64 `json:"ephemeral_1h_input_tokens"`
			} `json:"cache_creation"`
		} `json:"usage"`
	} `json:"message"`
}

// parseTranscript reads one transcript and returns its deduped responses (one
// per unique message.id, falling back to top-level requestId; lines with
// neither key each count), turn frames, and tool_use references. The
// first-seen line of a dedup group supplies the timestamp, attributionSkill,
// and turn.
func parseTranscript(path string) (parsed, error) {
	f, err := os.Open(path)
	if err != nil {
		return parsed{}, err
	}
	defer f.Close()

	p := parsed{turns: []turnRec{{frame: turnFrame(0, "(before first prompt)")}}}
	seen := map[string]bool{}
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 64*1024), maxLineSize)
	for sc.Scan() {
		raw := sc.Bytes()
		if len(bytes.TrimSpace(raw)) == 0 {
			continue
		}
		var l transcriptLine
		if json.Unmarshal(raw, &l) != nil {
			p.skipped++ // malformed or truncated JSON
			continue
		}
		if p.firstCwd == "" {
			p.firstCwd = l.Cwd
		}
		if l.Message == nil {
			continue // non-message line types
		}
		skill := l.AttributionSkill
		if skill == "" {
			skill = "(no skill)"
		}
		switch l.Type {
		case "user":
			if run, ok := workflowRun(l.ToolUseResult, l.Message.Content); ok {
				p.runs = append(p.runs, run)
			}
			if l.IsMeta || l.IsSidechain {
				continue
			}
			if prompt, cmdExtracted, ok := turnPrompt(l.Message.Content); ok {
				sn := snippet(prompt)
				p.turns = append(p.turns, turnRec{
					frame:  turnFrame(len(p.turns), sn),
					prompt: headRunes(prompt, 500),
					candidate: (!cmdExtracted && len(strings.Fields(prompt)) <= 4) ||
						strings.Contains(sn, redactedMarker),
				})
			}
			continue
		case "assistant":
			for _, id := range toolUseIDs(l.Message.Content) {
				p.toolUses = append(p.toolUses, toolUseRef{id: id, turnIdx: len(p.turns) - 1, skill: skill})
			}
			if cur := &p.turns[len(p.turns)-1]; cur.replyHead == "" {
				if text := firstTextBlock(l.Message.Content); text != "" {
					cur.replyHead = headRunes(scrub(text), 500)
				}
			}
		}
		if l.Message.Usage == nil {
			continue
		}
		var key string
		switch {
		case l.Message.ID != "":
			key = "m:" + l.Message.ID
		case l.RequestID != "":
			key = "r:" + l.RequestID
		}
		if key != "" { // no dedup key: every usage line counts
			if seen[key] {
				continue
			}
			seen[key] = true
		}
		ts, err := time.Parse(time.RFC3339Nano, l.Timestamp)
		if err != nil {
			p.skipped++ // a sample needs a valid time
			continue
		}
		u := l.Message.Usage
		usage := pricing.Usage{
			InputTokens:         u.InputTokens,
			OutputTokens:        u.OutputTokens,
			CacheReadTokens:     u.CacheReadInputTokens,
			CacheCreationTokens: u.CacheCreationInputTokens,
		}
		if u.CacheCreation != nil {
			usage.Cache5mTokens = u.CacheCreation.Ephemeral5m
			usage.Cache1hTokens = u.CacheCreation.Ephemeral1h
		}
		p.responses = append(p.responses, response{
			time: ts, skill: skill, model: l.Message.Model, usage: usage,
			turnIdx: len(p.turns) - 1,
		})
	}
	if sc.Err() != nil {
		p.skipped++ // unreadable remainder (e.g. oversized line); keep going
	}
	return p, nil
}

var (
	commandNameRe = regexp.MustCompile(`(?s)<command-name>(.*?)</command-name>`)
	commandArgsRe = regexp.MustCompile(`(?s)<command-args>(.*?)</command-args>`)
)

// excludedPrefixes open no turn (R1): harness-injected notifications, bash
// input/output echo, local command output, and interruption markers.
var excludedPrefixes = []string{
	"<local-command-", "<task-notification", "<bash-stdout", "<bash-input",
	"[Request interrupted",
}

// turnPrompt reports whether a user line's message.content opens a turn (R1)
// and, if so, its scrubbed collapsed prompt text after R2 command-tag
// extraction, plus whether that extraction fired.
func turnPrompt(raw json.RawMessage) (text string, cmdExtracted, ok bool) {
	text, ok = contentText(raw)
	if !ok {
		return "", false, false
	}
	if m := commandNameRe.FindStringSubmatch(text); m != nil {
		extracted := m[1]
		if a := commandArgsRe.FindStringSubmatch(text); a != nil && strings.TrimSpace(a[1]) != "" {
			extracted += " " + a[1]
		}
		text = extracted
		cmdExtracted = true
	}
	text = strings.Join(strings.Fields(text), " ") // collapse whitespace runs
	for _, prefix := range excludedPrefixes {
		if strings.HasPrefix(text, prefix) {
			return "", false, false
		}
	}
	return scrub(text), cmdExtracted, true
}

// contentText extracts prompt text from message.content: the string itself
// (non-empty), or the concatenated text blocks of an array holding at least
// one text block and no tool_result block.
func contentText(raw json.RawMessage) (string, bool) {
	if len(raw) == 0 {
		return "", false
	}
	var s string
	if json.Unmarshal(raw, &s) == nil {
		return s, s != ""
	}
	var blocks []contentBlock
	if json.Unmarshal(raw, &blocks) != nil {
		return "", false
	}
	var b strings.Builder
	hasText := false
	for _, blk := range blocks {
		switch blk.Type {
		case "tool_result":
			return "", false
		case "text":
			hasText = true
			b.WriteString(blk.Text)
		}
	}
	return b.String(), hasText
}

// workflowRun extracts a workflow-run reference from one user line: its
// top-level toolUseResult must be a JSON object carrying a string runId with
// prefix "wf_", and its message.content must hold a tool_result block with a
// tool_use_id (lines without one are skipped, not an error — R1).
func workflowRun(toolUseResult, content json.RawMessage) (runRef, bool) {
	if len(toolUseResult) == 0 {
		return runRef{}, false
	}
	var res struct {
		RunID        string `json:"runId"`
		WorkflowName string `json:"workflowName"`
	}
	if json.Unmarshal(toolUseResult, &res) != nil || !strings.HasPrefix(res.RunID, "wf_") {
		return runRef{}, false
	}
	var blocks []contentBlock
	if json.Unmarshal(content, &blocks) != nil {
		return runRef{}, false
	}
	for _, b := range blocks {
		if b.Type == "tool_result" && b.ToolUseID != "" {
			return runRef{runID: res.RunID, toolUseID: b.ToolUseID, workflowName: res.WorkflowName}, true
		}
	}
	return runRef{}, false
}

// toolUseIDs returns the ids of tool_use blocks in message.content.
func toolUseIDs(raw json.RawMessage) []string {
	var blocks []contentBlock
	if json.Unmarshal(raw, &blocks) != nil {
		return nil // string or malformed content carries no tool_use blocks
	}
	var ids []string
	for _, b := range blocks {
		if b.Type == "tool_use" && b.ID != "" {
			ids = append(ids, b.ID)
		}
	}
	return ids
}

// turnFrame formats "tNN · <snippet>" (R2): 1-based ordinal zero-padded to at
// least 2 digits; ordinal 0 is the synthetic pre-prompt turn.
func turnFrame(ordinal int, snippet string) string {
	return fmt.Sprintf("t%02d · %s", ordinal, snippet)
}

// snippet truncates collapsed prompt text to 40 runes (R2). A [redacted]
// marker straddling the cut would be shown mangled, so the cut moves to just
// before it instead (frame-naming SPEC R2).
func snippet(collapsed string) string {
	if collapsed == "" {
		return "(no text)"
	}
	r := []rune(collapsed)
	if len(r) <= 40 {
		return collapsed
	}
	cut := 40
	marker := []rune(redactedMarker)
	for start := cut - len(marker) + 1; start < cut; start++ {
		if start >= 0 && start+len(marker) <= len(r) && string(r[start:start+len(marker)]) == redactedMarker {
			cut = start
			break
		}
	}
	return string(r[:cut]) + "…"
}

// headRunes returns the first n runes of s.
func headRunes(s string, n int) string {
	if r := []rune(s); len(r) > n {
		return string(r[:n])
	}
	return s
}

// firstTextBlock returns the first non-empty text block of an assistant
// message's content array, or "".
func firstTextBlock(raw json.RawMessage) string {
	var blocks []contentBlock
	if json.Unmarshal(raw, &blocks) != nil {
		return ""
	}
	for _, b := range blocks {
		if b.Type == "text" && b.Text != "" {
			return b.Text
		}
	}
	return ""
}

// sample builds the canonical sample for one deduped response. turn is the
// zero-padded turn-ordinal label, or "" for unlinked subagent samples (R6).
func (r response) sample(stack []string, sessionID, turn string) schema.Sample {
	cost, priced := pricing.Price(r.model, r.usage)
	labels := map[string]string{"source": "claude-code", "session": sessionID}
	if turn != "" {
		labels["turn"] = turn
	}
	if !priced {
		labels["priced"] = "false"
	}
	return schema.Sample{
		Time:  r.time,
		Stack: stack,
		Values: map[string]int64{
			"input_tokens":       r.usage.InputTokens,
			"output_tokens":      r.usage.OutputTokens,
			"cache_read_tokens":  r.usage.CacheReadTokens,
			"cache_write_tokens": r.usage.CacheCreationTokens,
			"cost_microusd":      cost,
			"calls":              1,
		},
		Labels: labels,
	}
}
