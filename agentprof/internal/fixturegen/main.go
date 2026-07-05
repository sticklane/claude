// Command fixturegen deterministically regenerates testdata/claude-dir/ (a
// fake ~/.claude tree exercising every parsing rule the Claude adapter must
// handle) plus testdata/claude-dir.expected.json with hand-computed expected
// totals, and testdata/vertex-logs.json (see writeVertexLogs). Run via
// `make fixtures`.
//
// Fixture inventory and hand-computed totals (agentprof-turns SPEC R1-R8).
// One deduped sample per unique message.id (fallback: top-level requestId).
// Stacks are [project, turn, skill, "main", agent:*..., model]; unlinked
// subagents get [project, "(unlinked)", agent:*, model]:
//
//	key             file                     stack                                                                            in   out  cr  cw
//	msg_a1          -x-proj/sess-0001.jsonl  [proj t01·start build main claude-fable-5]                                       100  10   50  20 (5m:15 1h:5)
//	msg_a2 (x3)     -x-proj/sess-0001.jsonl  [proj t02·/parallel… (no skill) main claude-fable-5]                             200  20   0   0
//	msg_sa1         agent-A.jsonl            [proj t01·start build main agent:scout claude-fable-5]                           300  30   0   0
//	msg_sb1         agent-B.jsonl (no meta)  [proj (unlinked) agent:(unknown) claude-haiku-4-5]                               400  40   0   0
//	msg_b1          -y-beta/sess-0002.jsonl  [beta t01·hello (no skill) main mystery-model-9]  priced=false                   500  50   0   0
//	msg_b2          -y-beta/sess-0002.jsonl  [beta t01·hello (no skill) main <synthetic>]      priced=false                   0    0    0   0
//	req-fallback-1  -y-beta/sess-0002.jsonl  [beta t01·hello (no skill) main claude-sonnet-4-5] (x2 lines)                    600  60   0   0
//	msg_b3          -y-beta/sess-0002.jsonl  [beta t02·api token [redacted] leaked in logs (no skill) main claude-fable-5]    100  10   0   0
//	msg_w1          wf_test/agent-W.jsonl    [proj t01·start build main wf:test-flow agent:workflow-subagent claude-fable-5]  700  70   0   0
//	msg_ws1         wf_test/agent-WS.jsonl   [proj t01·start build main wf:test-flow agent:workflow-subagent agent:scout claude-haiku-4-5]  100  10  0  0
//
// Turn structure: sess-0001 has turn 01 ("start", containing msg_a1 whose
// content spawns agent-A via tool_use toolu_A and launches workflow run
// wf_test via tool_use toolu_W) and turn 02 (a slash-command line exercising
// R2 command-tag extraction, containing msg_a2), plus one
// <local-command-stdout> line and one <task-notification> line that must NOT
// open turns (R1 exclusions). A usage-less user tool_result line records
// toolUseResult.runId wf_test (workflowName test-flow): agent-W under
// subagents/workflows/wf_test/ carries no toolUseId in its meta — real
// workflow metas have none — and links via that path runId
// (workflow-linkage SPEC R2/R6), gaining the wf:test-flow frame. agent-W's
// transcript spawns agent-WS via tool_use toolu_WS (depth 2, meta-toolUseId
// linked, inheriting the wf: frame through agent-W's prefix). agent-B has
// no meta -> unlinked. sess-0002 has turn 01 ("hello") and turn 02, whose
// prompt embeds the fake secret cfut_FAKEfake1234FAKEfake1234 that R1
// scrubbing must replace with [redacted] in the frame (frame-naming SPEC R8);
// no subagents.
//
// The summed totals are recorded once, in writeExpected (and thus in
// claude-dir.expected.json) — re-sum this table when editing any usage above.
// sess-0001 is the multi-cwd session: main transcript records /x/proj first
// and /x/proj/sub later, so ALL its samples (subagents included) land under
// root frame "proj". sess-0002.jsonl ends in a truncated line (1 unparseable).
package main

import (
	"encoding/json"
	"log"
	"os"
	"path/filepath"
)

const (
	projXDir = "-x-proj"   // munged dir for /x/proj
	projYDir = "-y-beta"   // munged dir for /y/beta
	s1       = "sess-0001" // multi-cwd session, project /x/proj
	s2       = "sess-0002" // project /y/beta, truncated final line
)

func main() {
	if err := generate("testdata"); err != nil {
		log.Fatal(err)
	}
}

type cacheCreation struct {
	Ephemeral5m int `json:"ephemeral_5m_input_tokens"`
	Ephemeral1h int `json:"ephemeral_1h_input_tokens"`
}

type usage struct {
	InputTokens              int            `json:"input_tokens"`
	OutputTokens             int            `json:"output_tokens"`
	CacheReadInputTokens     int            `json:"cache_read_input_tokens"`
	CacheCreationInputTokens int            `json:"cache_creation_input_tokens"`
	CacheCreation            *cacheCreation `json:"cache_creation,omitempty"`
}

// Content is a string or a block array, mirroring real transcripts.
type message struct {
	ID      string `json:"id,omitempty"`
	Model   string `json:"model,omitempty"`
	Role    string `json:"role,omitempty"`
	Content any    `json:"content,omitempty"`
	Usage   *usage `json:"usage,omitempty"`
}

type textBlock struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

type toolUseBlock struct {
	Type  string         `json:"type"`
	ID    string         `json:"id"`
	Name  string         `json:"name"`
	Input map[string]any `json:"input"`
}

type toolResultBlock struct {
	Type      string `json:"type"`
	ToolUseID string `json:"tool_use_id"`
	Content   string `json:"content,omitempty"`
}

type line struct {
	Type             string   `json:"type"`
	Timestamp        string   `json:"timestamp,omitempty"`
	Cwd              string   `json:"cwd,omitempty"`
	SessionID        string   `json:"sessionId,omitempty"`
	AttributionSkill string   `json:"attributionSkill,omitempty"`
	RequestID        string   `json:"requestId,omitempty"`
	IsMeta           bool     `json:"isMeta,omitempty"`
	IsSidechain      bool     `json:"isSidechain,omitempty"`
	ToolUseResult    any      `json:"toolUseResult,omitempty"`
	Message          *message `json:"message,omitempty"`
	// Non-message line-type payloads.
	MessageID string `json:"messageId,omitempty"`
	Title     string `json:"title,omitempty"`
	Mode      string `json:"mode,omitempty"`
}

func user(ts, cwd, session string, content any) line {
	return line{
		Type: "user", Timestamp: ts, Cwd: cwd, SessionID: session,
		Message: &message{Role: "user", Content: content},
	}
}

func assistant(ts, cwd, session, skill, msgID, model string, u usage) line {
	return line{
		Type: "assistant", Timestamp: ts, Cwd: cwd, SessionID: session,
		AttributionSkill: skill,
		Message:          &message{ID: msgID, Model: model, Role: "assistant", Usage: &u},
	}
}

// generate writes root/claude-dir and root/claude-dir.expected.json,
// deleting any existing root/claude-dir first.
func generate(root string) error {
	dir := filepath.Join(root, "claude-dir")
	if err := os.RemoveAll(dir); err != nil {
		return err
	}

	projX := filepath.Join(dir, "projects", projXDir)
	projY := filepath.Join(dir, "projects", projYDir)

	// Project 1 main transcript: multi-cwd (/x/proj first, /x/proj/sub later),
	// two turns, a 3-line assistant response repeating msg_a2 with identical
	// usage, R1 exclusion lines, and non-message line types. msg_a1's content
	// carries the tool_use blocks that spawn agent-A and launch workflow run
	// wf_test (turn 01, skill "build"); the usage-less wfResult line records
	// the run's toolUseResult linkage (workflow-linkage SPEC R1).
	msgA1 := assistant("2026-07-01T10:01:00.000Z", "/x/proj", s1, "build", "msg_a1",
		"claude-fable-5", usage{
			InputTokens: 100, OutputTokens: 10,
			CacheReadInputTokens: 50, CacheCreationInputTokens: 20,
			CacheCreation: &cacheCreation{Ephemeral5m: 15, Ephemeral1h: 5},
		})
	msgA1.Message.Content = []any{
		textBlock{Type: "text", Text: "Spawning a scout."},
		toolUseBlock{Type: "tool_use", ID: "toolu_A", Name: "Agent",
			Input: map[string]any{"subagent_type": "scout"}},
		toolUseBlock{Type: "tool_use", ID: "toolu_W", Name: "Workflow",
			Input: map[string]any{"name": "test-flow"}},
	}
	wfResult := user("2026-07-01T10:01:15.000Z", "/x/proj", s1,
		[]any{toolResultBlock{Type: "tool_result", ToolUseID: "toolu_W",
			Content: "Workflow launched in the background"}})
	wfResult.ToolUseResult = map[string]any{
		"status": "async_launched", "runId": "wf_test", "workflowName": "test-flow",
	}
	msgA2 := assistant("2026-07-01T10:02:00.000Z", "/x/proj/sub", s1, "", "msg_a2",
		"claude-fable-5", usage{InputTokens: 200, OutputTokens: 20})
	if err := writeJSONL(filepath.Join(projX, s1+".jsonl"),
		line{Type: "file-history-snapshot", MessageID: "fh-1"},
		user("2026-07-01T10:00:00.000Z", "/x/proj", s1, "start"),
		msgA1,
		wfResult,
		user("2026-07-01T10:01:30.000Z", "/x/proj", s1,
			"<command-name>/parallel</command-name>\n"+
				"<command-message>parallel</command-message>\n"+
				"<command-args>specs/agentprof</command-args>"),
		msgA2, msgA2, msgA2,
		user("2026-07-01T10:06:00.000Z", "/x/proj/sub", s1,
			"<local-command-stdout>ok</local-command-stdout>"),
		user("2026-07-01T10:07:00.000Z", "/x/proj/sub", s1,
			[]any{textBlock{Type: "text", Text: "<task-notification>agent-A finished</task-notification>"}}),
		line{Type: "ai-title", Title: "Fixture session one"},
		line{Type: "mode", Mode: "default"},
	); err != nil {
		return err
	}

	// Two flat subagents: agent-A with meta (linked via toolu_A), agent-B
	// without meta (unlinked).
	subX := filepath.Join(projX, s1, "subagents")
	msgSA1 := assistant("2026-07-01T10:04:00.000Z", "/x/proj/sub", s1, "scan", "msg_sa1",
		"claude-fable-5", usage{InputTokens: 300, OutputTokens: 30})
	msgSA1.Message.Content = []any{
		textBlock{Type: "text", Text: "Scanning the tree."},
	}
	if err := writeJSONL(filepath.Join(subX, "agent-A.jsonl"),
		user("2026-07-01T10:03:00.000Z", "/x/proj/sub", s1, "subtask"),
		msgSA1,
	); err != nil {
		return err
	}
	if err := writeMeta(filepath.Join(subX, "agent-A.meta.json"), meta{
		AgentID: "agent-A", AgentType: "scout", ToolUseID: "toolu_A", SpawnDepth: 1,
	}); err != nil {
		return err
	}
	if err := writeJSONL(filepath.Join(subX, "agent-B.jsonl"),
		assistant("2026-07-01T10:05:00.000Z", "/x/proj", s1, "", "msg_sb1",
			"claude-haiku-4-5", usage{InputTokens: 400, OutputTokens: 40}),
	); err != nil {
		return err
	}

	// Workflow subagent agent-W: its meta carries NO toolUseId (matching real
	// workflow-subagent metas), so it links only via its path runId (wf_test)
	// through the wfResult line. Its transcript spawns the depth-2 scout
	// agent-WS via tool_use toolu_WS.
	wfDir := filepath.Join(projX, s1, "subagents", "workflows", "wf_test")
	msgW1 := assistant("2026-07-01T10:08:00.000Z", "/x/proj", s1, "wf-skill", "msg_w1",
		"claude-fable-5", usage{InputTokens: 700, OutputTokens: 70})
	msgW1.Message.Content = []any{
		textBlock{Type: "text", Text: "Spawning a scout from the workflow."},
		toolUseBlock{Type: "tool_use", ID: "toolu_WS", Name: "Agent",
			Input: map[string]any{"subagent_type": "scout"}},
	}
	if err := writeJSONL(filepath.Join(wfDir, "agent-W.jsonl"), msgW1); err != nil {
		return err
	}
	if err := writeMeta(filepath.Join(wfDir, "agent-W.meta.json"), meta{
		AgentType: "workflow-subagent", SpawnDepth: 1,
	}); err != nil {
		return err
	}
	if err := writeJSONL(filepath.Join(wfDir, "agent-WS.jsonl"),
		assistant("2026-07-01T10:09:00.000Z", "/x/proj", s1, "", "msg_ws1",
			"claude-haiku-4-5", usage{InputTokens: 100, OutputTokens: 10}),
	); err != nil {
		return err
	}
	if err := writeMeta(filepath.Join(wfDir, "agent-WS.meta.json"), meta{
		AgentID: "agent-WS", AgentType: "scout", ToolUseID: "toolu_WS", SpawnDepth: 2,
	}); err != nil {
		return err
	}

	// Project 2 main transcript: turn 01 ("hello") with an unknown model,
	// "<synthetic>" zero usage, and a requestId-only dedup fallback (two
	// identical lines, no message.id); turn 02 opens with a prompt embedding a
	// fake class-(a) secret within the first 25 runes (frame-naming SPEC R8 —
	// its [redacted] marker must survive snippet truncation) and carries
	// msg_b3; then a final line cut mid-JSON. No subagents.
	reqFallback := line{
		Type: "assistant", Timestamp: "2026-07-01T11:03:00.000Z", Cwd: "/y/beta",
		SessionID: s2, RequestID: "req-fallback-1",
		Message: &message{Model: "claude-sonnet-4-5", Role: "assistant",
			Usage: &usage{InputTokens: 600, OutputTokens: 60}},
	}
	truncatedPath := filepath.Join(projY, s2+".jsonl")
	if err := writeJSONL(truncatedPath,
		user("2026-07-01T11:00:00.000Z", "/y/beta", s2, "hello"),
		assistant("2026-07-01T11:01:00.000Z", "/y/beta", s2, "", "msg_b1",
			"mystery-model-9", usage{InputTokens: 500, OutputTokens: 50}),
		assistant("2026-07-01T11:02:00.000Z", "/y/beta", s2, "", "msg_b2",
			"<synthetic>", usage{}),
		reqFallback, reqFallback,
		user("2026-07-01T11:05:00.000Z", "/y/beta", s2,
			"api token cfut_FAKEfake1234FAKEfake1234 leaked in logs"),
		assistant("2026-07-01T11:06:00.000Z", "/y/beta", s2, "", "msg_b3",
			"claude-fable-5", usage{InputTokens: 100, OutputTokens: 10}),
	); err != nil {
		return err
	}
	truncated := `{"type":"assistant","timestamp":"2026-07-01T11:04:00.000Z","cwd":"/y/beta","sessionId":"sess-0002","message":{"id":"msg_trunc","model":"claude-fa`
	if err := appendRaw(truncatedPath, truncated); err != nil {
		return err
	}

	if err := writeExpected(filepath.Join(root, "claude-dir.expected.json")); err != nil {
		return err
	}
	return writeVertexLogs(filepath.Join(root, "vertex-logs.json"))
}

// vertexRow mirrors the Vertex AI request-response logging table columns the
// vertex adapter reads, in the `bq query --format=json` shape (a JSON array
// of row objects; the full_response JSON column arrives either as an inline
// object or as a JSON-encoded string depending on the export path).
type vertexRow struct {
	Endpoint        string          `json:"endpoint,omitempty"`
	LoggingTime     string          `json:"logging_time,omitempty"`
	RequestID       string          `json:"request_id,omitempty"`
	APIMethod       string          `json:"api_method,omitempty"`
	Model           string          `json:"model,omitempty"`
	ResponsePayload []string        `json:"response_payload,omitempty"`
	FullResponse    json.RawMessage `json:"full_response,omitempty"`
}

// writeVertexLogs writes the vertex adapter fixture (vertex-logs-adapter
// SPEC R12). Row inventory and hand-computed expected samples — literal
// expected stacks/metrics live in internal/vertex/vertex_test.go and
// cmd_vertex_test.go; costs computed against internal/pricing/table.go
// (claude-sonnet-4@20250514 -> claude-sonnet-: 500 in ×3 + 60 out ×15 +
// 30 cr ×0.30 + 40 cw ×3.75 = 2559):
//
//	row  kind                    stack                                                          in    out  cr   cw   cost   notes
//	1    gemini unary            [proj-vertex us-central1 gemini-2.0-flash GenerateContent]     1000  150  200  -    -      full_response inline object; out = 100 candidates + 50 thoughts
//	2    gemini streaming        [proj-vertex us-central1 gemini-2.0-flash StreamGenerateContent] 300 40   -    -    -      no full_response; usage only in last response_payload chunk
//	3    claude-on-vertex        [123456789 us-east5 claude-sonnet-4@20250514 rawPredict]       500   60   30   40   2559   full_response JSON-encoded string; priced=true; project number verbatim
//	4    missing endpoint        [(unknown) (unknown) gemini-2.0-flash generateContent]         10    2    -    -    -      bare model id and api_method used as-is
//	5    skipped (no usage)      -                                                              -     -    -    -    -      full_response present but usage-less
//
// Totals: 4 samples, 1 skipped, exactly 1 row priced=true.
func writeVertexLogs(path string) error {
	const gemEndpoint = "projects/proj-vertex/locations/us-central1/publishers/google/models/gemini-2.0-flash"
	rows := []vertexRow{
		{
			Endpoint:     gemEndpoint,
			LoggingTime:  "2026-07-01 12:00:00.123456 UTC",
			RequestID:    "vreq-1",
			APIMethod:    "google.cloud.aiplatform.v1.PredictionService.GenerateContent",
			Model:        "publishers/google/models/gemini-2.0-flash",
			FullResponse: json.RawMessage(`{"modelVersion":"gemini-2.0-flash","usageMetadata":{"promptTokenCount":1000,"candidatesTokenCount":100,"thoughtsTokenCount":50,"cachedContentTokenCount":200}}`),
		},
		{
			Endpoint:    gemEndpoint,
			LoggingTime: "2026-07-01T12:05:00Z",
			RequestID:   "vreq-2",
			APIMethod:   "google.cloud.aiplatform.v1.PredictionService.StreamGenerateContent",
			Model:       "publishers/google/models/gemini-2.0-flash",
			ResponsePayload: []string{
				`{"candidates":[{"content":{"parts":[{"text":"hel"}]}}]}`,
				`{"candidates":[{"content":{"parts":[{"text":"lo"}]},"finishReason":"STOP"}],"usageMetadata":{"promptTokenCount":300,"candidatesTokenCount":40}}`,
			},
		},
		{
			Endpoint:     "projects/123456789/locations/us-east5/publishers/anthropic/models/claude-sonnet-4@20250514",
			LoggingTime:  "2026-07-01 13:00:00",
			RequestID:    "vreq-3",
			APIMethod:    "rawPredict",
			Model:        "publishers/anthropic/models/claude-sonnet-4@20250514",
			FullResponse: json.RawMessage(`"{\"id\":\"msg_v1\",\"model\":\"claude-sonnet-4-20250514\",\"usage\":{\"input_tokens\":500,\"output_tokens\":60,\"cache_read_input_tokens\":30,\"cache_creation_input_tokens\":40}}"`),
		},
		{
			LoggingTime:  "2026-07-01 14:00:00",
			RequestID:    "vreq-4",
			APIMethod:    "generateContent",
			Model:        "gemini-2.0-flash",
			FullResponse: json.RawMessage(`{"usageMetadata":{"promptTokenCount":10,"candidatesTokenCount":2}}`),
		},
		{
			Endpoint:     gemEndpoint,
			LoggingTime:  "2026-07-01 15:00:00",
			RequestID:    "vreq-5",
			APIMethod:    "google.cloud.aiplatform.v1.PredictionService.GenerateContent",
			Model:        "publishers/google/models/gemini-2.0-flash",
			FullResponse: json.RawMessage(`{"candidates":[{"content":{"parts":[{"text":"no usage recorded"}]}}]}`),
		},
	}
	data, err := json.MarshalIndent(rows, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(data, '\n'), 0o644)
}

// expected mirrors the hand-computed totals in the package comment. Stacks
// are recorded root-first, [project, turn, skill, "main", agent:*..., model]
// per the agentprof-turns SPEC (R3/R4), "(unlinked)" per R5. Costs are
// hand-computed against the task 03 rate table (internal/pricing/table.go):
// msg_a1 1838 (100 in ×10 + 10 out ×50 + 50 cr ×1 + 15 cw5m ×12.50 +
// 5 cw1h ×20 = 1837.5, rounded away from zero), msg_a2 3000, msg_sa1 4500,
// msg_sb1 600 (haiku), msg_b1 and msg_b2 0 (unpriced), req-fallback-1 2700
// (sonnet), msg_b3 1500, msg_w1 10500, msg_ws1 150 (haiku).
type expected struct {
	Note                 string               `json:"note"`
	SampleCount          int                  `json:"sample_count"`
	TotalInputTokens     int                  `json:"total_input_tokens"`
	TotalOutputTokens    int                  `json:"total_output_tokens"`
	TotalCacheReadTokens int                  `json:"total_cache_read_tokens"`
	TotalCacheWrite      int                  `json:"total_cache_write_tokens"`
	TotalCostMicroUSD    int                  `json:"total_cost_microusd"`
	UnparseableLines     int                  `json:"unparseable_lines"`
	UnpricedSampleCount  int                  `json:"unpriced_sample_count"`
	TruncatedFile        string               `json:"truncated_file"`
	StackOrder           string               `json:"stack_order"`
	PerRootFrame         map[string]rootFrame `json:"per_root_frame"`
	Stacks               map[string][]string  `json:"stacks"`
}

type rootFrame struct {
	SampleCount  int `json:"sample_count"`
	InputTokens  int `json:"input_tokens"`
	OutputTokens int `json:"output_tokens"`
	CostMicroUSD int `json:"cost_microusd"`
}

func writeExpected(path string) error {
	turn1 := "t01 · start"
	e := expected{
		Note: "hand-computed from the fixture inventory; cost fields computed " +
			"against the task 03 rate table (internal/pricing/table.go)",
		SampleCount:          10,
		TotalInputTokens:     3000,
		TotalOutputTokens:    300,
		TotalCacheReadTokens: 50,
		TotalCacheWrite:      20,
		TotalCostMicroUSD:    24788,
		UnparseableLines:     1,
		UnpricedSampleCount:  2,
		// Repo-relative by contract (task 05 and the acceptance commands
		// resolve it from the repo root), independent of generate's root arg.
		TruncatedFile: "testdata/claude-dir/projects/" + projYDir + "/" + s2 + ".jsonl",
		StackOrder:    "[project, turn, skill, main, agent:*..., model] per agentprof-turns SPEC (leaf-last); workflow-run-linked agents insert wf:<workflowName> before their agent: frame (workflow-linkage SPEC R3); unlinked subagents [project, (unlinked), agent:*, model]",
		PerRootFrame: map[string]rootFrame{
			"proj": {SampleCount: 6, InputTokens: 1800, OutputTokens: 180, CostMicroUSD: 20588},
			"beta": {SampleCount: 4, InputTokens: 1200, OutputTokens: 120, CostMicroUSD: 4200},
		},
		Stacks: map[string][]string{
			"main_turn01_msg_a1":        {"proj", turn1, "build", "main", "claude-fable-5"},
			"main_turn02_dedup_msg_a2":  {"proj", "t02 · /parallel specs/agentprof", "(no skill)", "main", "claude-fable-5"},
			"depth1_subagent_msg_sa1":   {"proj", turn1, "build", "main", "agent:scout", "claude-fable-5"},
			"unlinked_subagent_msg_sb1": {"proj", "(unlinked)", "agent:(unknown)", "claude-haiku-4-5"},
			"unknown_model_msg_b1":      {"beta", "t01 · hello", "(no skill)", "main", "mystery-model-9"},
			"synthetic_msg_b2":          {"beta", "t01 · hello", "(no skill)", "main", "<synthetic>"},
			"request_id_fallback":       {"beta", "t01 · hello", "(no skill)", "main", "claude-sonnet-4-5"},
			"scrubbed_turn02_msg_b3":    {"beta", "t02 · api token [redacted] leaked in logs", "(no skill)", "main", "claude-fable-5"},
			"workflow_agent_msg_w1":     {"proj", turn1, "build", "main", "wf:test-flow", "agent:workflow-subagent", "claude-fable-5"},
			"workflow_scout_msg_ws1":    {"proj", turn1, "build", "main", "wf:test-flow", "agent:workflow-subagent", "agent:scout", "claude-haiku-4-5"},
		},
	}
	data, err := json.MarshalIndent(e, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(data, '\n'), 0o644)
}

func writeJSONL(path string, lines ...line) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	var out []byte
	for _, l := range lines {
		data, err := json.Marshal(l)
		if err != nil {
			return err
		}
		out = append(append(out, data...), '\n')
	}
	return os.WriteFile(path, out, 0o644)
}

// appendRaw appends s to path without a trailing newline (used for the
// truncated final line).
func appendRaw(path, s string) error {
	b, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(b, s...), 0o644)
}

type meta struct {
	AgentID    string `json:"agentId,omitempty"`
	AgentType  string `json:"agentType"`
	ToolUseID  string `json:"toolUseId,omitempty"`
	SpawnDepth int    `json:"spawnDepth,omitempty"`
}

func writeMeta(path string, m meta) error {
	data, err := json.Marshal(m)
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(data, '\n'), 0o644)
}
