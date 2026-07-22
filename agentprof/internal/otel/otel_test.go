package otel

import (
	"encoding/base64"
	"encoding/hex"
	"fmt"
	"os"
	"strings"
	"testing"
	"time"

	commonv1 "go.opentelemetry.io/proto/otlp/common/v1"
	logsv1 "go.opentelemetry.io/proto/otlp/logs/v1"
	tracev1 "go.opentelemetry.io/proto/otlp/trace/v1"
	"google.golang.org/protobuf/proto"
)

// b64hex is the base64 that protojson expects for a hex-encoded ID.
func b64hex(t *testing.T, h string) string {
	t.Helper()
	raw, err := hex.DecodeString(h)
	if err != nil {
		t.Fatalf("hex.DecodeString(%q) error = %v", h, err)
	}
	return base64.StdEncoding.EncodeToString(raw)
}

const (
	testTraceID = "0102030405060708090a0b0c0d0e0f10"
	testSpanID  = "0102030405060708"
	testStart   = "1700000000000000000"
	testEnd     = "1700000000001500000" // start + 1.5ms
)

// export wraps span JSON objects in a single OTLP/JSON trace-export object.
// An empty service omits the service.name resource attribute entirely.
func export(service string, spans ...string) string {
	resource := ""
	if service != "" {
		resource = `"resource":{"attributes":[{"key":"service.name","value":{"stringValue":"` + service + `"}}]},`
	}
	return `{"resourceSpans":[{` + resource + `"scopeSpans":[{"spans":[` + strings.Join(spans, ",") + `]}]}]}`
}

// span builds one span JSON object with the shared trace ID and test times.
func span(spanID, parentSpanID, name string, attrs ...string) string {
	parent := ""
	if parentSpanID != "" {
		parent = `"parentSpanId":"` + parentSpanID + `",`
	}
	return `{"traceId":"` + testTraceID + `","spanId":"` + spanID + `",` + parent +
		`"name":"` + name + `","startTimeUnixNano":"` + testStart + `","endTimeUnixNano":"` + testEnd + `",` +
		`"attributes":[` + strings.Join(attrs, ",") + `]}`
}

func intAttr(key, v string) string {
	return `{"key":"` + key + `","value":{"intValue":"` + v + `"}}`
}

func strAttr(key, v string) string {
	return `{"key":"` + key + `","value":{"stringValue":"` + v + `"}}`
}

func tokenSpan(spanID, parentSpanID, name string, extraAttrs ...string) string {
	attrs := append([]string{intAttr("gen_ai.usage.input_tokens", "100"), intAttr("gen_ai.usage.output_tokens", "50")}, extraAttrs...)
	return span(spanID, parentSpanID, name, attrs...)
}

// claudeCodeTokenSpan builds a span carrying Claude Code's bare token keys
// (not the gen_ai.usage.* aliases).
func claudeCodeTokenSpan(spanID, parentSpanID, name string, extraAttrs ...string) string {
	attrs := append([]string{intAttr("input_tokens", "100"), intAttr("output_tokens", "50")}, extraAttrs...)
	return span(spanID, parentSpanID, name, attrs...)
}

func flushOne(t *testing.T, bodies ...string) (stack []string, values map[string]int64, labels map[string]string, tm time.Time) {
	t.Helper()
	acc := NewAccumulator()
	for _, body := range bodies {
		if err := acc.AddJSON([]byte(body)); err != nil {
			t.Fatalf("AddJSON() error = %v", err)
		}
	}
	samples, skipped := acc.Flush()
	if skipped != 0 {
		t.Fatalf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 1 {
		t.Fatalf("len(samples) = %d, want 1", len(samples))
	}
	s := samples[0]
	return s.Stack, s.Values, s.Labels, s.Time
}

// --- Decode (R2) ---

func TestDecodeHexTraceAndSpanIDsRoundTrip(t *testing.T) {
	// A base64 mis-decode of the hex ID would produce different bytes, so
	// asserting the label equals the input hex catches silent mis-decoding.
	_, _, labels, _ := flushOne(t, export("svc", tokenSpan(testSpanID, "", "llm-call")))
	if labels["trace_id"] != testTraceID {
		t.Errorf("labels[trace_id] = %q, want %q", labels["trace_id"], testTraceID)
	}
}

func TestDecodeIgnoresUnknownJSONFields(t *testing.T) {
	sp := tokenSpan(testSpanID, "", "llm-call")
	sp = strings.Replace(sp, `"name":`, `"futureField":{"nested":[1,2]},"name":`, 1)
	stack, _, _, _ := flushOne(t, export("svc", sp))
	if len(stack) == 0 {
		t.Errorf("stack is empty, want frames")
	}
}

// --- Token recognition (R3) ---

func TestCanonicalTokenKeysEmitSample(t *testing.T) {
	_, values, _, _ := flushOne(t, export("svc", tokenSpan(testSpanID, "", "llm-call")))
	if values["input_tokens"] != 100 {
		t.Errorf("input_tokens = %d, want 100", values["input_tokens"])
	}
	if values["output_tokens"] != 50 {
		t.Errorf("output_tokens = %d, want 50", values["output_tokens"])
	}
}

func TestLegacyTokenKeysEmitSample(t *testing.T) {
	sp := span(testSpanID, "", "llm-call",
		intAttr("gen_ai.usage.prompt_tokens", "7"), intAttr("gen_ai.usage.completion_tokens", "3"))
	_, values, _, _ := flushOne(t, export("svc", sp))
	if values["input_tokens"] != 7 {
		t.Errorf("input_tokens = %d, want 7", values["input_tokens"])
	}
	if values["output_tokens"] != 3 {
		t.Errorf("output_tokens = %d, want 3", values["output_tokens"])
	}
}

func TestCanonicalTokenKeyWinsOverLegacyAlias(t *testing.T) {
	sp := span(testSpanID, "", "llm-call",
		intAttr("gen_ai.usage.prompt_tokens", "999"), intAttr("gen_ai.usage.input_tokens", "100"))
	_, values, _, _ := flushOne(t, export("svc", sp))
	if values["input_tokens"] != 100 {
		t.Errorf("input_tokens = %d, want 100 (canonical key should win)", values["input_tokens"])
	}
}

func TestNegativeTokenValueSkipsSpan(t *testing.T) {
	sp := span(testSpanID, "", "llm-call", intAttr("gen_ai.usage.input_tokens", "-1"))
	acc := NewAccumulator()
	if err := acc.AddJSON([]byte(export("svc", sp))); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	samples, skipped := acc.Flush()
	if len(samples) != 0 {
		t.Errorf("len(samples) = %d, want 0", len(samples))
	}
	if skipped != 1 {
		t.Errorf("skipped = %d, want 1", skipped)
	}
}

func TestNonIntTokenValueSkipsSpan(t *testing.T) {
	sp := span(testSpanID, "", "llm-call", strAttr("gen_ai.usage.input_tokens", "100"))
	acc := NewAccumulator()
	if err := acc.AddJSON([]byte(export("svc", sp))); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	samples, skipped := acc.Flush()
	if len(samples) != 0 {
		t.Errorf("len(samples) = %d, want 0", len(samples))
	}
	if skipped != 1 {
		t.Errorf("skipped = %d, want 1", skipped)
	}
}

// --- Claude Code aliases (bare keys + cache tokens) ---

func TestClaudeCodeBareTokenKeysEmitSample(t *testing.T) {
	sp := claudeCodeTokenSpan(testSpanID, "", "claude_code.llm_request")
	_, values, _, _ := flushOne(t, export("claude-code", sp))
	if values["input_tokens"] != 100 {
		t.Errorf("input_tokens = %d, want 100", values["input_tokens"])
	}
	if values["output_tokens"] != 50 {
		t.Errorf("output_tokens = %d, want 50", values["output_tokens"])
	}
}

func TestClaudeCodeCacheCreationTokensMapToCacheWriteTokens(t *testing.T) {
	sp := claudeCodeTokenSpan(testSpanID, "", "claude_code.llm_request", intAttr("cache_creation_tokens", "40"))
	_, values, _, _ := flushOne(t, export("claude-code", sp))
	if values["cache_write_tokens"] != 40 {
		t.Errorf("cache_write_tokens = %d, want 40", values["cache_write_tokens"])
	}
	for k := range values {
		if strings.HasPrefix(k, "cache_creation") {
			t.Errorf("Values contains raw source key %q, want only canonical cache_write_tokens", k)
		}
	}
}

func TestClaudeCodeCacheReadTokensSurface(t *testing.T) {
	sp := claudeCodeTokenSpan(testSpanID, "", "claude_code.llm_request", intAttr("cache_read_tokens", "18"))
	_, values, _, _ := flushOne(t, export("claude-code", sp))
	if values["cache_read_tokens"] != 18 {
		t.Errorf("cache_read_tokens = %d, want 18", values["cache_read_tokens"])
	}
}

func TestCacheTokenValuesOmittedWhenAbsent(t *testing.T) {
	_, values, _, _ := flushOne(t, export("claude-code", claudeCodeTokenSpan(testSpanID, "", "claude_code.llm_request")))
	if _, ok := values["cache_read_tokens"]; ok {
		t.Errorf("cache_read_tokens present = %d, want absent", values["cache_read_tokens"])
	}
	if _, ok := values["cache_write_tokens"]; ok {
		t.Errorf("cache_write_tokens present = %d, want absent", values["cache_write_tokens"])
	}
}

// TestGenAiUsageKeysUnaffectedByClaudeCodeAliases is the regression check:
// adding Claude Code's bare-key aliases must not change resolution of the
// existing gen_ai.usage.* keys (canonical still wins over legacy).
func TestGenAiUsageKeysUnaffectedByClaudeCodeAliases(t *testing.T) {
	sp := span(testSpanID, "", "llm-call",
		intAttr("gen_ai.usage.prompt_tokens", "999"), intAttr("gen_ai.usage.input_tokens", "100"))
	_, values, _, _ := flushOne(t, export("svc", sp))
	if values["input_tokens"] != 100 {
		t.Errorf("input_tokens = %d, want 100 (canonical gen_ai key should still win)", values["input_tokens"])
	}
}

func TestSpanWithoutTokensEmitsNothingButProvidesFrame(t *testing.T) {
	parent := span("00000000000000aa", "", "agent-root")
	child := tokenSpan(testSpanID, "00000000000000aa", "llm-call")
	stack, _, _, _ := flushOne(t, export("svc", parent, child))
	want := []string{"svc", "agent-root", "llm-call"}
	if len(stack) != 3 || stack[0] != want[0] || stack[1] != want[1] || stack[2] != want[2] {
		t.Errorf("stack = %v, want %v", stack, want)
	}
}

// --- Values / Time (R4) ---

func TestWallMsRoundsDurationAndCallsIsOne(t *testing.T) {
	_, values, _, _ := flushOne(t, export("svc", tokenSpan(testSpanID, "", "llm-call")))
	if values["wall_ms"] != 2 { // 1.5ms rounds to 2
		t.Errorf("wall_ms = %d, want 2", values["wall_ms"])
	}
	if values["calls"] != 1 {
		t.Errorf("calls = %d, want 1", values["calls"])
	}
}

func TestWallMsRoundsDown(t *testing.T) {
	sp := strings.Replace(tokenSpan(testSpanID, "", "llm-call"), testEnd, "1700000000001400000", 1) // 1.4ms
	_, values, _, _ := flushOne(t, export("svc", sp))
	if values["wall_ms"] != 1 {
		t.Errorf("wall_ms = %d, want 1", values["wall_ms"])
	}
}

func TestValuesOmitAbsentTokenMetric(t *testing.T) {
	sp := span(testSpanID, "", "llm-call", intAttr("gen_ai.usage.input_tokens", "100"))
	_, values, _, _ := flushOne(t, export("svc", sp))
	if _, ok := values["output_tokens"]; ok {
		t.Errorf("output_tokens present = %d, want absent", values["output_tokens"])
	}
}

func TestTimeIsStartNanosUTC(t *testing.T) {
	_, _, _, tm := flushOne(t, export("svc", tokenSpan(testSpanID, "", "llm-call")))
	want := time.Unix(0, 1700000000000000000).UTC()
	if !tm.Equal(want) {
		t.Errorf("Time = %v, want %v", tm, want)
	}
	if tm.Location() != time.UTC {
		t.Errorf("Time location = %v, want UTC", tm.Location())
	}
}

func TestEndBeforeStartSkipsSpan(t *testing.T) {
	sp := strings.Replace(tokenSpan(testSpanID, "", "llm-call"), testEnd, "1600000000000000000", 1)
	acc := NewAccumulator()
	if err := acc.AddJSON([]byte(export("svc", sp))); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	samples, skipped := acc.Flush()
	if len(samples) != 0 {
		t.Errorf("len(samples) = %d, want 0", len(samples))
	}
	if skipped != 1 {
		t.Errorf("skipped = %d, want 1", skipped)
	}
}

// --- Stack (R5) ---

func TestStackIsRootFirstWithServiceName(t *testing.T) {
	root := span("00000000000000aa", "", "agent-root")
	mid := span("00000000000000bb", "00000000000000aa", "tool-step")
	leaf := tokenSpan(testSpanID, "00000000000000bb", "llm-call")
	stack, _, _, _ := flushOne(t, export("svc", root, mid, leaf))
	want := []string{"svc", "agent-root", "tool-step", "llm-call"}
	if strings.Join(stack, "|") != strings.Join(want, "|") {
		t.Errorf("stack = %v, want %v", stack, want)
	}
}

func TestMissingServiceNameUsesUnknownPlaceholder(t *testing.T) {
	stack, _, _, _ := flushOne(t, export("", tokenSpan(testSpanID, "", "llm-call")))
	if stack[0] != "(unknown service)" {
		t.Errorf("stack[0] = %q, want %q", stack[0], "(unknown service)")
	}
}

func TestOrphanSpanStartsChainAtItself(t *testing.T) {
	sp := tokenSpan(testSpanID, "00000000000000ff", "llm-call") // parent never delivered
	stack, _, _, _ := flushOne(t, export("svc", sp))
	want := []string{"svc", "llm-call"}
	if strings.Join(stack, "|") != strings.Join(want, "|") {
		t.Errorf("stack = %v, want %v", stack, want)
	}
}

func TestParentCycleBrokenAtFirstRepeatedSpanID(t *testing.T) {
	a := tokenSpan("00000000000000aa", "00000000000000bb", "span-a")
	b := span("00000000000000bb", "00000000000000aa", "span-b")
	stack, _, _, _ := flushOne(t, export("svc", a, b))
	want := []string{"svc", "span-b", "span-a"}
	if strings.Join(stack, "|") != strings.Join(want, "|") {
		t.Errorf("stack = %v, want %v", stack, want)
	}
}

func TestDuplicateSpanDedupedFirstWins(t *testing.T) {
	first := tokenSpan(testSpanID, "", "first-delivery")
	second := tokenSpan(testSpanID, "", "second-delivery")
	stack, _, _, _ := flushOne(t, export("svc", first), export("svc", second))
	if stack[len(stack)-1] != "first-delivery" {
		t.Errorf("leaf frame = %q, want %q (first delivery wins)", stack[len(stack)-1], "first-delivery")
	}
}

// --- Labels (R6) ---

func TestLabelsSourceAndLowercaseHexTraceID(t *testing.T) {
	_, _, labels, _ := flushOne(t, export("svc", tokenSpan(testSpanID, "", "llm-call")))
	if labels["source"] != "otel" {
		t.Errorf("labels[source] = %q, want %q", labels["source"], "otel")
	}
	if labels["trace_id"] != strings.ToLower(labels["trace_id"]) {
		t.Errorf("labels[trace_id] = %q, want lowercase hex", labels["trace_id"])
	}
}

func TestModelPrefersResponseOverRequest(t *testing.T) {
	sp := tokenSpan(testSpanID, "", "llm-call",
		strAttr("gen_ai.request.model", "requested-model"), strAttr("gen_ai.response.model", "actual-model"))
	_, _, labels, _ := flushOne(t, export("svc", sp))
	if labels["model"] != "actual-model" {
		t.Errorf("labels[model] = %q, want %q", labels["model"], "actual-model")
	}
}

func TestModelFallsBackToRequestModel(t *testing.T) {
	sp := tokenSpan(testSpanID, "", "llm-call", strAttr("gen_ai.request.model", "requested-model"))
	_, _, labels, _ := flushOne(t, export("svc", sp))
	if labels["model"] != "requested-model" {
		t.Errorf("labels[model] = %q, want %q", labels["model"], "requested-model")
	}
}

func TestModelOmittedWhenAbsent(t *testing.T) {
	_, _, labels, _ := flushOne(t, export("svc", tokenSpan(testSpanID, "", "llm-call")))
	if v, ok := labels["model"]; ok {
		t.Errorf("labels[model] = %q, want absent", v)
	}
}

func TestSystemPrefersGenAISystem(t *testing.T) {
	sp := tokenSpan(testSpanID, "", "llm-call",
		strAttr("gen_ai.system", "anthropic"), strAttr("gen_ai.provider.name", "other"))
	_, _, labels, _ := flushOne(t, export("svc", sp))
	if labels["system"] != "anthropic" {
		t.Errorf("labels[system] = %q, want %q", labels["system"], "anthropic")
	}
}

func TestSystemFallsBackToProviderName(t *testing.T) {
	sp := tokenSpan(testSpanID, "", "llm-call", strAttr("gen_ai.provider.name", "anthropic"))
	_, _, labels, _ := flushOne(t, export("svc", sp))
	if labels["system"] != "anthropic" {
		t.Errorf("labels[system] = %q, want %q", labels["system"], "anthropic")
	}
}

func TestSystemOmittedWhenAbsent(t *testing.T) {
	_, _, labels, _ := flushOne(t, export("svc", tokenSpan(testSpanID, "", "llm-call")))
	if v, ok := labels["system"]; ok {
		t.Errorf("labels[system] = %q, want absent", v)
	}
}

// --- Determinism ---

func TestSamplesEmittedInFirstSeenOrderAcrossBatches(t *testing.T) {
	acc := NewAccumulator()
	batches := []string{
		export("svc", tokenSpan("00000000000000aa", "", "seen-first")),
		export("svc", tokenSpan("00000000000000bb", "", "seen-second")),
	}
	for _, b := range batches {
		if err := acc.AddJSON([]byte(b)); err != nil {
			t.Fatalf("AddJSON() error = %v", err)
		}
	}
	samples, _ := acc.Flush()
	if len(samples) != 2 {
		t.Fatalf("len(samples) = %d, want 2", len(samples))
	}
	if leaf := samples[0].Stack[len(samples[0].Stack)-1]; leaf != "seen-first" {
		t.Errorf("samples[0] leaf = %q, want %q", leaf, "seen-first")
	}
	if leaf := samples[1].Stack[len(samples[1].Stack)-1]; leaf != "seen-second" {
		t.Errorf("samples[1] leaf = %q, want %q", leaf, "seen-second")
	}
}

// --- Protobuf decode path ---

func TestAddProtoDecodesTracesData(t *testing.T) {
	td := &tracev1.TracesData{
		ResourceSpans: []*tracev1.ResourceSpans{{
			ScopeSpans: []*tracev1.ScopeSpans{{
				Spans: []*tracev1.Span{{
					TraceId:           []byte{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16},
					SpanId:            []byte{1, 2, 3, 4, 5, 6, 7, 8},
					Name:              "llm-call",
					StartTimeUnixNano: 1700000000000000000,
					EndTimeUnixNano:   1700000001500000000,
					Attributes: []*commonv1.KeyValue{{
						Key:   "gen_ai.usage.input_tokens",
						Value: &commonv1.AnyValue{Value: &commonv1.AnyValue_IntValue{IntValue: 100}},
					}},
				}},
			}},
		}},
	}
	raw, err := proto.Marshal(td)
	if err != nil {
		t.Fatalf("proto.Marshal() error = %v", err)
	}
	acc := NewAccumulator()
	if err := acc.AddProto(raw); err != nil {
		t.Fatalf("AddProto() error = %v", err)
	}
	samples, skipped := acc.Flush()
	if skipped != 0 {
		t.Fatalf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 1 {
		t.Fatalf("len(samples) = %d, want 1", len(samples))
	}
	if samples[0].Values["input_tokens"] != 100 {
		t.Errorf("input_tokens = %d, want 100", samples[0].Values["input_tokens"])
	}
	if samples[0].Labels["trace_id"] != testTraceID {
		t.Errorf("labels[trace_id] = %q, want %q", samples[0].Labels["trace_id"], testTraceID)
	}
}

// --- ID rewrite splice (decoder-offset) ---

// TestIDKeyNameInValuePositionNotRewritten verifies that a valid-hex string
// appearing as an attribute *value* (not as an object key) is left byte-for-
// byte untouched, while the real ID *key* value is rewritten to base64. Only
// object-key position counts.
func TestIDKeyNameInValuePositionNotRewritten(t *testing.T) {
	valueHex := "aabbccddeeff00112233445566778899" // 32 hex chars, valid, but a value
	in := `{"traceId":"` + testTraceID + `","attributes":[` +
		strAttr("custom.id", valueHex) + `,` + strAttr("note", "trace_id") + `]}`
	out, err := hexIDsToBase64([]byte(in))
	if err != nil {
		t.Fatalf("hexIDsToBase64() error = %v", err)
	}
	got := string(out)
	if !strings.Contains(got, `"`+valueHex+`"`) {
		t.Errorf("value-position hex %q was rewritten; want preserved verbatim in %q", valueHex, got)
	}
	if !strings.Contains(got, `"`+"trace_id"+`"`) {
		t.Errorf("value-position string \"trace_id\" was altered; want preserved in %q", got)
	}
	if !strings.Contains(got, `"traceId":"`+b64hex(t, testTraceID)+`"`) {
		t.Errorf("key-position traceId not rewritten to base64 in %q", got)
	}
}

// TestMixedAndLowerCaseHexDecodeToSameID verifies hex decoding is case
// insensitive: an uppercase/mixed-case trace ID yields the same decoded bytes
// (and thus the same lowercase-hex label) as its lowercase equivalent.
func TestMixedAndLowerCaseHexDecodeToSameID(t *testing.T) {
	lower := "0102030405060708090a0b0c0d0e0f10"
	mixed := "0102030405060708090A0b0C0d0E0f10"
	spanLower := span(testSpanID, "", "llm-call", intAttr("gen_ai.usage.input_tokens", "1"))
	spanLower = strings.Replace(spanLower, testTraceID, lower, 1)
	spanMixed := strings.Replace(spanLower, lower, mixed, 1)
	_, _, labLower, _ := flushOne(t, export("svc", spanLower))
	_, _, labMixed, _ := flushOne(t, export("svc", spanMixed))
	if labMixed["trace_id"] != labLower["trace_id"] {
		t.Errorf("mixed-case trace_id = %q, want same as lowercase %q", labMixed["trace_id"], labLower["trace_id"])
	}
	if labLower["trace_id"] != lower {
		t.Errorf("lowercase trace_id label = %q, want %q", labLower["trace_id"], lower)
	}
}

// TestNonHexIDValuePassedThroughUntouched verifies that an ID key whose value
// is not valid hex is left verbatim (matching hex.DecodeString error → skip).
func TestNonHexIDValuePassedThroughUntouched(t *testing.T) {
	in := `{"traceId":"not-valid-hex!!","spanId":"` + testSpanID + `"}`
	out, err := hexIDsToBase64([]byte(in))
	if err != nil {
		t.Fatalf("hexIDsToBase64() error = %v", err)
	}
	got := string(out)
	if !strings.Contains(got, `"traceId":"not-valid-hex!!"`) {
		t.Errorf("non-hex traceId was altered; want preserved verbatim in %q", got)
	}
	if !strings.Contains(got, `"spanId":"`+b64hex(t, testSpanID)+`"`) {
		t.Errorf("valid-hex spanId not rewritten in %q", got)
	}
}

// TestEveryNonIDBytePreservedVerbatim is the core new constraint: the splice
// changes only the ID value spans and reformats nothing. The output must equal
// the input byte-for-byte except that each ID hex value is replaced by its
// base64 — no whitespace collapse, key reordering, or number reformatting (all
// of which a json.Marshal round-trip would introduce).
func TestEveryNonIDBytePreservedVerbatim(t *testing.T) {
	tHex := testTraceID
	sHex := testSpanID
	pHex := "00000000000000aa"
	// Deliberately irregular whitespace, a large integer string, and a raw
	// number literal — none of which must change.
	in := "{\n  \"resourceSpans\" : [ {\n" +
		"    \"scopeSpans\": [ { \"spans\": [ {\n" +
		"      \"traceId\":\"" + tHex + "\" ,\n" +
		"      \"spanId\" : \"" + sHex + "\",\n" +
		"      \"parentSpanId\":\"" + pHex + "\",\n" +
		"      \"name\":\"x\", \"droppedAttributesCount\": 3,\n" +
		"      \"startTimeUnixNano\":\"1700000000000000000\"\n" +
		"    } ] } ]\n  } ]\n}"
	want := strings.Replace(in, `"`+tHex+`"`, `"`+b64hex(t, tHex)+`"`, 1)
	want = strings.Replace(want, `"`+sHex+`"`, `"`+b64hex(t, sHex)+`"`, 1)
	want = strings.Replace(want, `"`+pHex+`"`, `"`+b64hex(t, pHex)+`"`, 1)
	out, err := hexIDsToBase64([]byte(in))
	if err != nil {
		t.Fatalf("hexIDsToBase64() error = %v", err)
	}
	if string(out) != want {
		t.Errorf("splice output not byte-preserving.\n got: %q\nwant: %q", string(out), want)
	}
}

// --- Golden fixtures (Claude Code dialect) ---

func TestClaudeCodeGoldenFixtureDecodesBareAndCacheKeys(t *testing.T) {
	data, err := os.ReadFile("testdata/claude_code_cache_tokens.json")
	if err != nil {
		t.Fatalf("ReadFile() error = %v", err)
	}
	acc := NewAccumulator()
	if err := acc.AddJSON(data); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	samples, skipped := acc.Flush()
	if skipped != 0 {
		t.Fatalf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 1 {
		t.Fatalf("len(samples) = %d, want 1", len(samples))
	}
	want := map[string]int64{"input_tokens": 200, "output_tokens": 80, "cache_read_tokens": 30, "cache_write_tokens": 500}
	got := samples[0].Values
	for k, v := range want {
		if got[k] != v {
			t.Errorf("Values[%q] = %d, want %d", k, got[k], v)
		}
	}
}

// --- Log ingestion + trace-context cost join ---

// logsExport wraps log-record JSON objects in a single OTLP/JSON logs-export
// object. An empty service omits the service.name resource attribute.
func logsExport(service string, records ...string) string {
	resource := ""
	if service != "" {
		resource = `"resource":{"attributes":[{"key":"service.name","value":{"stringValue":"` + service + `"}}]},`
	}
	return `{"resourceLogs":[{` + resource + `"scopeLogs":[{"logRecords":[` + strings.Join(records, ",") + `]}]}]}`
}

// costLogRecord builds one OTLP/JSON log record. Empty traceID/spanID omit the
// trace-context fields (a record without trace context degrades to a flat
// sample). Empty eventName omits the event_name field.
func costLogRecord(traceID, spanID, eventName, ts string, attrs ...string) string {
	ctx := ""
	if traceID != "" {
		ctx += `"traceId":"` + traceID + `",`
	}
	if spanID != "" {
		ctx += `"spanId":"` + spanID + `",`
	}
	ev := ""
	if eventName != "" {
		ev = `"eventName":"` + eventName + `",`
	}
	return `{` + ctx + ev + `"timeUnixNano":"` + ts + `","attributes":[` + strings.Join(attrs, ",") + `]}`
}

func doubleAttr(key, v string) string {
	return `{"key":"` + key + `","value":{"doubleValue":` + v + `}}`
}

func TestLogRecordCostAttachesToMatchingTokenSpan(t *testing.T) {
	acc := NewAccumulator()
	sp := claudeCodeTokenSpan(testSpanID, "", "claude_code.llm_request")
	if err := acc.AddJSON([]byte(export("claude-code", sp))); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	rec := costLogRecord(testTraceID, testSpanID, "claude_code.api_request", testStart, doubleAttr("cost_usd", "0.041230"))
	if err := acc.AddLogsJSON([]byte(logsExport("claude-code", rec))); err != nil {
		t.Fatalf("AddLogsJSON() error = %v", err)
	}
	samples, skipped := acc.Flush()
	if skipped != 0 {
		t.Fatalf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 1 {
		t.Fatalf("len(samples) = %d, want 1", len(samples))
	}
	if got := samples[0].Values["cost_microusd"]; got != 41230 {
		t.Errorf("cost_microusd = %d, want 41230", got)
	}
	if got := samples[0].Values["input_tokens"]; got != 100 {
		t.Errorf("input_tokens = %d, want 100 (span tokens retained)", got)
	}
}

func TestLogCostUSDRoundsToNearestMicroUSD(t *testing.T) {
	// 0.0000015 USD * 1e6 = 1.5 micro-USD, which rounds to 2.
	acc := NewAccumulator()
	sp := claudeCodeTokenSpan(testSpanID, "", "claude_code.llm_request")
	if err := acc.AddJSON([]byte(export("claude-code", sp))); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	rec := costLogRecord(testTraceID, testSpanID, "claude_code.api_request", testStart, doubleAttr("cost_usd", "0.0000015"))
	if err := acc.AddLogsJSON([]byte(logsExport("claude-code", rec))); err != nil {
		t.Fatalf("AddLogsJSON() error = %v", err)
	}
	samples, _ := acc.Flush()
	if len(samples) != 1 {
		t.Fatalf("len(samples) = %d, want 1", len(samples))
	}
	if got := samples[0].Values["cost_microusd"]; got != 2 {
		t.Errorf("cost_microusd = %d, want 2 (1.5 rounds to 2)", got)
	}
}

func TestCostOnlySpanEmittedUnderRelaxedFlushGate(t *testing.T) {
	// A span with no token attributes emits nothing under the old gate; with a
	// cost record joined, the relaxed hasTokens||hasCost gate emits it.
	acc := NewAccumulator()
	sp := span(testSpanID, "", "claude_code.tool") // no token attributes
	if err := acc.AddJSON([]byte(export("claude-code", sp))); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	rec := costLogRecord(testTraceID, testSpanID, "claude_code.api_request", testStart, doubleAttr("cost_usd", "0.001000"))
	if err := acc.AddLogsJSON([]byte(logsExport("claude-code", rec))); err != nil {
		t.Fatalf("AddLogsJSON() error = %v", err)
	}
	samples, skipped := acc.Flush()
	if skipped != 0 {
		t.Fatalf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 1 {
		t.Fatalf("len(samples) = %d, want 1 (relaxed gate emits cost-only span)", len(samples))
	}
	if got := samples[0].Values["cost_microusd"]; got != 1000 {
		t.Errorf("cost_microusd = %d, want 1000", got)
	}
	if _, ok := samples[0].Values["input_tokens"]; ok {
		t.Errorf("input_tokens present on a token-less span, want absent")
	}
}

func TestLogRecordWithoutTraceContextYieldsFlatSample(t *testing.T) {
	acc := NewAccumulator()
	rec := costLogRecord("", "", "claude_code.api_request", testStart, doubleAttr("cost_usd", "0.002500"))
	if err := acc.AddLogsJSON([]byte(logsExport("claude-code", rec))); err != nil {
		t.Fatalf("AddLogsJSON() error = %v", err)
	}
	samples, skipped := acc.Flush()
	if skipped != 0 {
		t.Fatalf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 1 {
		t.Fatalf("len(samples) = %d, want 1", len(samples))
	}
	if got := strings.Join(samples[0].Stack, "|"); got != "claude-code|claude_code.api_request" {
		t.Errorf("flat stack = %q, want %q", got, "claude-code|claude_code.api_request")
	}
	if got := samples[0].Values["cost_microusd"]; got != 2500 {
		t.Errorf("cost_microusd = %d, want 2500", got)
	}
}

func TestLogRecordEventNameFromAttributeWhenFieldAbsent(t *testing.T) {
	// Older emitters carry the event name in an event.name attribute rather
	// than the dedicated event_name field; a flat sample still names it.
	acc := NewAccumulator()
	rec := costLogRecord("", "", "", testStart,
		strAttr("event.name", "claude_code.api_request"), doubleAttr("cost_usd", "0.000100"))
	if err := acc.AddLogsJSON([]byte(logsExport("claude-code", rec))); err != nil {
		t.Fatalf("AddLogsJSON() error = %v", err)
	}
	samples, _ := acc.Flush()
	if len(samples) != 1 {
		t.Fatalf("len(samples) = %d, want 1", len(samples))
	}
	if got := samples[0].Stack[len(samples[0].Stack)-1]; got != "claude_code.api_request" {
		t.Errorf("flat leaf frame = %q, want %q", got, "claude_code.api_request")
	}
}

func TestAddLogsProtoJoinsCostOntoSpan(t *testing.T) {
	acc := NewAccumulator()
	sp := claudeCodeTokenSpan(testSpanID, "", "claude_code.llm_request")
	if err := acc.AddJSON([]byte(export("claude-code", sp))); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	ld := &logsv1.LogsData{
		ResourceLogs: []*logsv1.ResourceLogs{{
			ScopeLogs: []*logsv1.ScopeLogs{{
				LogRecords: []*logsv1.LogRecord{{
					TraceId:      []byte{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16},
					SpanId:       []byte{1, 2, 3, 4, 5, 6, 7, 8},
					EventName:    "claude_code.api_request",
					TimeUnixNano: 1700000000000000000,
					Attributes: []*commonv1.KeyValue{{
						Key:   "cost_usd",
						Value: &commonv1.AnyValue{Value: &commonv1.AnyValue_DoubleValue{DoubleValue: 0.5}},
					}},
				}},
			}},
		}},
	}
	raw, err := proto.Marshal(ld)
	if err != nil {
		t.Fatalf("proto.Marshal() error = %v", err)
	}
	if err := acc.AddLogsProto(raw); err != nil {
		t.Fatalf("AddLogsProto() error = %v", err)
	}
	samples, _ := acc.Flush()
	if len(samples) != 1 {
		t.Fatalf("len(samples) = %d, want 1", len(samples))
	}
	if got := samples[0].Values["cost_microusd"]; got != 500000 {
		t.Errorf("cost_microusd = %d, want 500000", got)
	}
}

func TestGoldenCostLogFixturesJoinAndDegrade(t *testing.T) {
	acc := NewAccumulator()
	for _, f := range []struct {
		name string
		logs bool
	}{
		{"testdata/cost_correlated_trace.json", false},
		{"testdata/cost_correlated_log.json", true},
		{"testdata/logs_uncorrelated_cost.json", true},
	} {
		data, err := os.ReadFile(f.name)
		if err != nil {
			t.Fatalf("ReadFile(%s) error = %v", f.name, err)
		}
		if f.logs {
			err = acc.AddLogsJSON(data)
		} else {
			err = acc.AddJSON(data)
		}
		if err != nil {
			t.Fatalf("adding %s: %v", f.name, err)
		}
	}
	samples, skipped := acc.Flush()
	if skipped != 0 {
		t.Fatalf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 2 {
		t.Fatalf("len(samples) = %d, want 2 (one joined span + one flat log)", len(samples))
	}
	// Sample 0: the token span with the correlated cost joined onto it.
	joined := samples[0]
	if joined.Values["input_tokens"] != 200 || joined.Values["cost_microusd"] != 41230 {
		t.Errorf("joined sample = %v, want input_tokens 200 + cost_microusd 41230", joined.Values)
	}
	if got := joined.Stack[len(joined.Stack)-1]; got != "claude_code.llm_request" {
		t.Errorf("joined leaf frame = %q, want claude_code.llm_request", got)
	}
	// Sample 1: the uncorrelated cost log degraded to a flat sample.
	flat := samples[1]
	if got := strings.Join(flat.Stack, "|"); got != "claude-code|claude_code.api_request" {
		t.Errorf("flat stack = %q, want claude-code|claude_code.api_request", got)
	}
	if flat.Values["cost_microusd"] != 7500 {
		t.Errorf("flat cost_microusd = %d, want 7500", flat.Values["cost_microusd"])
	}
}

// --- Dialect detection ---

func TestDetectDialectMatchesClaudeCodeSpanPrefix(t *testing.T) {
	if d := detectDialect("claude_code.llm_request"); d != "claude_code" {
		t.Errorf("detectDialect() = %q, want %q", d, "claude_code")
	}
}

func TestDetectDialectFallsBackToGenericForUnknownPrefix(t *testing.T) {
	if d := detectDialect("llm.chat"); d != "" {
		t.Errorf("detectDialect() = %q, want empty (generic fallback)", d)
	}
}

// --- Additional dialects (Task 04): codex / gemini_cli / qwen-code ---

func TestDetectDialectMatchesCodexSpanPrefix(t *testing.T) {
	if d := detectDialect("codex.session_loop"); d != "codex" {
		t.Errorf("detectDialect() = %q, want %q", d, "codex")
	}
}

func TestDetectDialectMatchesGeminiSpanPrefix(t *testing.T) {
	if d := detectDialect("gemini_cli.generate_content"); d != "gemini_cli" {
		t.Errorf("detectDialect() = %q, want %q", d, "gemini_cli")
	}
}

func TestDetectDialectMatchesQwenSpanPrefix(t *testing.T) {
	if d := detectDialect("qwen-code.generate_content"); d != "qwen-code" {
		t.Errorf("detectDialect() = %q, want %q", d, "qwen-code")
	}
}

// Codex maps its own session identifier — conversation.id — into
// labels["session"], while its gen_ai.usage.* tokens resolve via the shared
// base alias set.
func TestCodexDialectMapsConversationIDToSession(t *testing.T) {
	sp := tokenSpan(testSpanID, "", "codex.session_loop", strAttr("conversation.id", "conv-abc"))
	_, values, labels, _ := flushOne(t, export("codex", sp))
	if labels["session"] != "conv-abc" {
		t.Errorf("labels[session] = %q, want %q", labels["session"], "conv-abc")
	}
	if values["input_tokens"] != 100 || values["output_tokens"] != 50 {
		t.Errorf("tokens = %d/%d, want 100/50", values["input_tokens"], values["output_tokens"])
	}
}

func TestGeminiDialectMapsSessionIDToSession(t *testing.T) {
	sp := tokenSpan(testSpanID, "", "gemini_cli.generate_content", strAttr("session.id", "gem-123"))
	_, values, labels, _ := flushOne(t, export("gemini-cli", sp))
	if labels["session"] != "gem-123" {
		t.Errorf("labels[session] = %q, want %q", labels["session"], "gem-123")
	}
	if values["input_tokens"] != 100 {
		t.Errorf("input_tokens = %d, want 100", values["input_tokens"])
	}
}

func TestQwenDialectMapsSessionIDToSession(t *testing.T) {
	sp := tokenSpan(testSpanID, "", "qwen-code.generate_content", strAttr("session.id", "qwen-9"))
	_, _, labels, _ := flushOne(t, export("qwen-code", sp))
	if labels["session"] != "qwen-9" {
		t.Errorf("labels[session] = %q, want %q", labels["session"], "qwen-9")
	}
}

// An unrecognized gen_ai.* service carries no dialect prefix: the base alias
// set still resolves gen_ai.usage.* tokens, and the generic session key
// populates labels["session"].
func TestGenericGenAiDialectFallsBackToBaseAliasSet(t *testing.T) {
	sp := tokenSpan(testSpanID, "", "gen_ai.chat", strAttr("gen_ai.conversation.id", "gen-77"))
	_, values, labels, _ := flushOne(t, export("some-service", sp))
	if values["input_tokens"] != 100 {
		t.Errorf("input_tokens = %d, want 100 (base alias set)", values["input_tokens"])
	}
	if labels["session"] != "gen-77" {
		t.Errorf("labels[session] = %q, want %q", labels["session"], "gen-77")
	}
}

// A span with no session attribute omits the session label entirely.
func TestDialectSessionLabelOmittedWhenSessionKeyAbsent(t *testing.T) {
	sp := tokenSpan(testSpanID, "", "codex.session_loop")
	_, _, labels, _ := flushOne(t, export("codex", sp))
	if _, ok := labels["session"]; ok {
		t.Errorf("labels[session] present = %q, want absent", labels["session"])
	}
}

// flushDialectFixture reads a golden OTLP/JSON trace fixture, flushes it, and
// returns the single emitted sample's values and labels.
func flushDialectFixture(t *testing.T, path string) (map[string]int64, map[string]string) {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("ReadFile() error = %v", err)
	}
	acc := NewAccumulator()
	if err := acc.AddJSON(data); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	samples, skipped := acc.Flush()
	if skipped != 0 {
		t.Fatalf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 1 {
		t.Fatalf("len(samples) = %d, want 1", len(samples))
	}
	return samples[0].Values, samples[0].Labels
}

func TestCodexGoldenFixtureMapsSessionAndTokens(t *testing.T) {
	values, labels := flushDialectFixture(t, "testdata/codex_session.json")
	if labels["session"] != "codex-conv-01" {
		t.Errorf("labels[session] = %q, want codex-conv-01", labels["session"])
	}
	if values["input_tokens"] != 300 || values["output_tokens"] != 120 {
		t.Errorf("tokens = %d/%d, want 300/120", values["input_tokens"], values["output_tokens"])
	}
}

func TestGeminiGoldenFixtureMapsSessionAndTokens(t *testing.T) {
	values, labels := flushDialectFixture(t, "testdata/gemini_session.json")
	if labels["session"] != "gemini-sess-01" {
		t.Errorf("labels[session] = %q, want gemini-sess-01", labels["session"])
	}
	if values["input_tokens"] != 250 || values["output_tokens"] != 90 {
		t.Errorf("tokens = %d/%d, want 250/90", values["input_tokens"], values["output_tokens"])
	}
}

func TestQwenGoldenFixtureMapsSessionAndTokens(t *testing.T) {
	values, labels := flushDialectFixture(t, "testdata/qwen_session.json")
	if labels["session"] != "qwen-sess-01" {
		t.Errorf("labels[session] = %q, want qwen-sess-01", labels["session"])
	}
	if values["input_tokens"] != 150 || values["output_tokens"] != 60 {
		t.Errorf("tokens = %d/%d, want 150/60", values["input_tokens"], values["output_tokens"])
	}
}

// --- Frames-only-ancestor cost fallback (Task 03) ---

// spanAt builds one span JSON object with explicit start/end nanos and the
// shared trace ID. attrs are the span's attribute JSON objects (empty = a
// frames-only span carrying no token metrics).
func spanAt(spanID, parentSpanID, name, start, end string, attrs ...string) string {
	parent := ""
	if parentSpanID != "" {
		parent = `"parentSpanId":"` + parentSpanID + `",`
	}
	return `{"traceId":"` + testTraceID + `","spanId":"` + spanID + `",` + parent +
		`"name":"` + name + `","startTimeUnixNano":"` + start + `","endTimeUnixNano":"` + end + `",` +
		`"attributes":[` + strings.Join(attrs, ",") + `]}`
}

// tokenSpanAt is spanAt carrying Claude Code's bare token keys.
func tokenSpanAt(spanID, parentSpanID, name, start, end string) string {
	return spanAt(spanID, parentSpanID, name, start, end,
		intAttr("input_tokens", "100"), intAttr("output_tokens", "50"))
}

// costByLeaf flushes acc and maps each emitted sample's leaf frame name to its
// cost_microusd (0 when the sample carries no cost). It fails on any skipped
// span. A leaf name absent from the map means that span emitted no sample.
func costByLeaf(t *testing.T, acc *Accumulator) map[string]int64 {
	t.Helper()
	samples, skipped := acc.Flush()
	if skipped != 0 {
		t.Fatalf("skipped = %d, want 0", skipped)
	}
	out := make(map[string]int64)
	for _, s := range samples {
		out[s.Stack[len(s.Stack)-1]] = s.Values["cost_microusd"]
	}
	return out
}

func TestAncestorCostAttachesToSingleContainingDescendant(t *testing.T) {
	// Cost targets a frames-only ancestor; the one token-bearing descendant
	// whose time range contains the event timestamp receives it.
	acc := NewAccumulator()
	trace := export("claude-code",
		spanAt("aa00000000000001", "", "claude_code.interaction", "1700000000000000000", "1700000000005000000"),
		tokenSpanAt("bb00000000000001", "aa00000000000001", "claude_code.llm_request", "1700000000001000000", "1700000000002000000"),
	)
	if err := acc.AddJSON([]byte(trace)); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	rec := costLogRecord(testTraceID, "aa00000000000001", "claude_code.api_request", "1700000000001500000", doubleAttr("cost_usd", "0.041230"))
	if err := acc.AddLogsJSON([]byte(logsExport("claude-code", rec))); err != nil {
		t.Fatalf("AddLogsJSON() error = %v", err)
	}
	byLeaf := costByLeaf(t, acc)
	if got := byLeaf["claude_code.llm_request"]; got != 41230 {
		t.Errorf("descendant cost_microusd = %d, want 41230 (redistributed from ancestor)", got)
	}
	if _, ok := byLeaf["claude_code.interaction"]; ok {
		t.Errorf("frames-only ancestor emitted a sample; cost should have moved to the descendant")
	}
}

func TestAncestorCostPrefersEarliestStartAmongContainingDescendants(t *testing.T) {
	// Two token-bearing descendants both contain the event timestamp; the one
	// with the earlier span start wins.
	acc := NewAccumulator()
	trace := export("claude-code",
		spanAt("aa00000000000001", "", "claude_code.interaction", "1700000000000000000", "1700000000005000000"),
		tokenSpanAt("bb00000000000001", "aa00000000000001", "claude_code.earlier", "1700000000001000000", "1700000000004000000"),
		tokenSpanAt("cc00000000000001", "aa00000000000001", "claude_code.later", "1700000000001500000", "1700000000004000000"),
	)
	if err := acc.AddJSON([]byte(trace)); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	rec := costLogRecord(testTraceID, "aa00000000000001", "claude_code.api_request", "1700000000002000000", doubleAttr("cost_usd", "0.041230"))
	if err := acc.AddLogsJSON([]byte(logsExport("claude-code", rec))); err != nil {
		t.Fatalf("AddLogsJSON() error = %v", err)
	}
	byLeaf := costByLeaf(t, acc)
	if got := byLeaf["claude_code.earlier"]; got != 41230 {
		t.Errorf("earliest-start descendant cost = %d, want 41230", got)
	}
	if got := byLeaf["claude_code.later"]; got != 0 {
		t.Errorf("later-start descendant cost = %d, want 0 (earliest wins the tie-break)", got)
	}
}

func TestAncestorCostFallsBackToLatestDescendantStartedBeforeEvent(t *testing.T) {
	// No descendant's time range contains the event timestamp (the event lands
	// after both ended); the latest-started descendant receives the cost.
	acc := NewAccumulator()
	trace := export("claude-code",
		spanAt("aa00000000000001", "", "claude_code.interaction", "1700000000000000000", "1700000000005000000"),
		tokenSpanAt("bb00000000000001", "aa00000000000001", "claude_code.first", "1700000000001000000", "1700000000001200000"),
		tokenSpanAt("cc00000000000001", "aa00000000000001", "claude_code.second", "1700000000001500000", "1700000000001700000"),
	)
	if err := acc.AddJSON([]byte(trace)); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	rec := costLogRecord(testTraceID, "aa00000000000001", "claude_code.api_request", "1700000000003000000", doubleAttr("cost_usd", "0.041230"))
	if err := acc.AddLogsJSON([]byte(logsExport("claude-code", rec))); err != nil {
		t.Fatalf("AddLogsJSON() error = %v", err)
	}
	byLeaf := costByLeaf(t, acc)
	if got := byLeaf["claude_code.second"]; got != 41230 {
		t.Errorf("latest-started descendant cost = %d, want 41230 (started-before fallback)", got)
	}
	if got := byLeaf["claude_code.first"]; got != 0 {
		t.Errorf("earlier descendant cost = %d, want 0", got)
	}
}

func TestAncestorFallbackLeavesDirectTokenMatchUnchanged(t *testing.T) {
	// Regression: a cost record naming a token-bearing span directly still
	// attaches to that span (Task 02's fast path), never a descendant walk.
	acc := NewAccumulator()
	sp := claudeCodeTokenSpan(testSpanID, "", "claude_code.llm_request")
	if err := acc.AddJSON([]byte(export("claude-code", sp))); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	rec := costLogRecord(testTraceID, testSpanID, "claude_code.api_request", testStart, doubleAttr("cost_usd", "0.041230"))
	if err := acc.AddLogsJSON([]byte(logsExport("claude-code", rec))); err != nil {
		t.Fatalf("AddLogsJSON() error = %v", err)
	}
	byLeaf := costByLeaf(t, acc)
	if got := byLeaf["claude_code.llm_request"]; got != 41230 {
		t.Errorf("direct-match token span cost = %d, want 41230 (unchanged)", got)
	}
	if len(byLeaf) != 1 {
		t.Errorf("emitted %d samples, want 1 (direct match, no extra descendant)", len(byLeaf))
	}
}

func TestGoldenAncestorSingleDescendantFixture(t *testing.T) {
	acc := NewAccumulator()
	for _, f := range []struct {
		name string
		logs bool
	}{
		{"testdata/ancestor_single_trace.json", false},
		{"testdata/ancestor_single_cost.json", true},
	} {
		data, err := os.ReadFile(f.name)
		if err != nil {
			t.Fatalf("ReadFile(%s) error = %v", f.name, err)
		}
		if f.logs {
			err = acc.AddLogsJSON(data)
		} else {
			err = acc.AddJSON(data)
		}
		if err != nil {
			t.Fatalf("adding %s: %v", f.name, err)
		}
	}
	samples, skipped := acc.Flush()
	if skipped != 0 {
		t.Fatalf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 1 {
		t.Fatalf("len(samples) = %d, want 1 (cost redistributed onto the sole descendant)", len(samples))
	}
	s := samples[0]
	if got := s.Stack[len(s.Stack)-1]; got != "claude_code.llm_request" {
		t.Errorf("leaf frame = %q, want claude_code.llm_request", got)
	}
	if s.Values["cost_microusd"] != 41230 || s.Values["input_tokens"] != 200 {
		t.Errorf("sample values = %v, want cost_microusd 41230 + input_tokens 200", s.Values)
	}
}

func TestGoldenAncestorMultiDescendantFixture(t *testing.T) {
	acc := NewAccumulator()
	for _, f := range []struct {
		name string
		logs bool
	}{
		{"testdata/ancestor_multi_trace.json", false},
		{"testdata/ancestor_multi_cost.json", true},
	} {
		data, err := os.ReadFile(f.name)
		if err != nil {
			t.Fatalf("ReadFile(%s) error = %v", f.name, err)
		}
		if f.logs {
			err = acc.AddLogsJSON(data)
		} else {
			err = acc.AddJSON(data)
		}
		if err != nil {
			t.Fatalf("adding %s: %v", f.name, err)
		}
	}
	samples, skipped := acc.Flush()
	if skipped != 0 {
		t.Fatalf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 2 {
		t.Fatalf("len(samples) = %d, want 2 (both token descendants emit; only the earliest carries cost)", len(samples))
	}
	byLeaf := make(map[string]int64)
	for _, s := range samples {
		byLeaf[s.Stack[len(s.Stack)-1]] = s.Values["cost_microusd"]
	}
	if got := byLeaf["claude_code.llm_request_first"]; got != 41230 {
		t.Errorf("earliest-start descendant cost = %d, want 41230", got)
	}
	if got := byLeaf["claude_code.llm_request_second"]; got != 0 {
		t.Errorf("later-start descendant cost = %d, want 0", got)
	}
}

// --- Cost from tokens (Claude table) + user pricing config ---

// TestCostFromTokensComputesClaudeModelCost: a token-only span whose model
// prefix-matches the built-in Claude pricing table gets a cost_microusd
// computed from its tokens (no emitted cost attribute present).
func TestCostFromTokensComputesClaudeModelCost(t *testing.T) {
	sp := tokenSpan(testSpanID, "", "llm-call",
		strAttr("gen_ai.response.model", "claude-sonnet-4-5"))
	_, values, _, _ := flushOne(t, export("svc", sp))
	// claude-sonnet- rates: input $3/MTok, output $15/MTok. 100 input + 50
	// output = 100*3 + 50*15 = 1050 micro-USD (USD/MTok == micro-USD/token).
	if got := values["cost_microusd"]; got != 1050 {
		t.Errorf("cost_microusd = %d, want 1050 (computed from Claude table)", got)
	}
	if values["input_tokens"] != 100 {
		t.Errorf("input_tokens = %d, want 100 (tokens still emitted)", values["input_tokens"])
	}
}

// TestEmittedCostWinsOverComputedFromTokens: when a span carries both tokens
// (a priceable Claude model) and an emitted cost attribute, the emitted value
// is kept — computation never overrides it.
func TestEmittedCostWinsOverComputedFromTokens(t *testing.T) {
	sp := tokenSpan(testSpanID, "", "llm-call",
		strAttr("gen_ai.response.model", "claude-sonnet-4-5"))
	rec := costLogRecord(testTraceID, testSpanID, "claude_code.api_request", testStart,
		doubleAttr("cost_usd", "0.000009"))
	acc := NewAccumulator()
	if err := acc.AddJSON([]byte(export("svc", sp))); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	if err := acc.AddLogsJSON([]byte(logsExport("svc", rec))); err != nil {
		t.Fatalf("AddLogsJSON() error = %v", err)
	}
	samples, skipped := acc.Flush()
	if skipped != 0 || len(samples) != 1 {
		t.Fatalf("Flush() = %d samples, %d skipped, want 1, 0", len(samples), skipped)
	}
	// Emitted 0.000009 USD = 9 micro-USD; computed-from-tokens would be 1050.
	if got := samples[0].Values["cost_microusd"]; got != 9 {
		t.Errorf("cost_microusd = %d, want 9 (emitted wins over computed 1050)", got)
	}
}

// TestCostFromTokensGeminiModelStaysTokensOnly: a Gemini-model token-only span
// gets no cost_microusd — the Gemini table is exact-map on Antigravity display
// strings that OTel API model IDs never hit (Decision 6), and no user config is
// supplied.
func TestCostFromTokensGeminiModelStaysTokensOnly(t *testing.T) {
	sp := tokenSpan(testSpanID, "", "gemini_cli.generate",
		strAttr("gen_ai.response.model", "gemini-2.5-pro"))
	_, values, _, _ := flushOne(t, export("gemini", sp))
	if _, ok := values["cost_microusd"]; ok {
		t.Errorf("cost_microusd present = %d, want absent (Gemini stays tokens-only)", values["cost_microusd"])
	}
	if values["input_tokens"] != 100 {
		t.Errorf("input_tokens = %d, want 100 (tokens still emitted)", values["input_tokens"])
	}
}

// TestUserPricingConfigAppliesToNonClaudeModel: a --pricing-supplied rate table
// prices a non-Claude model the built-in Claude table does not match.
func TestUserPricingConfigAppliesToNonClaudeModel(t *testing.T) {
	sp := tokenSpan(testSpanID, "", "gemini_cli.generate",
		strAttr("gen_ai.response.model", "gemini-2.5-pro"))
	acc := NewAccumulator()
	acc.SetUserPricing([]UserRate{{Prefix: "gemini-2.5", Input: 1.25, Output: 10}})
	if err := acc.AddJSON([]byte(export("gemini", sp))); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	samples, skipped := acc.Flush()
	if skipped != 0 || len(samples) != 1 {
		t.Fatalf("Flush() = %d samples, %d skipped, want 1, 0", len(samples), skipped)
	}
	// 100 input * 1.25 + 50 output * 10 = 125 + 500 = 625 micro-USD.
	if got := samples[0].Values["cost_microusd"]; got != 625 {
		t.Errorf("cost_microusd = %d, want 625 (user rate table)", got)
	}
}

// TestParseUserPricingDecodesModelsArray: the --pricing config decoder reads a
// {"models":[…]} object into ordered prefix-matched rate entries.
func TestParseUserPricingDecodesModelsArray(t *testing.T) {
	cfg := `{"models":[{"prefix":"gemini-2.5","input":1.25,"output":10,"cache_read":0.31,"cache_write":1.625}]}`
	rates, err := ParseUserPricing([]byte(cfg))
	if err != nil {
		t.Fatalf("ParseUserPricing() error = %v", err)
	}
	if len(rates) != 1 {
		t.Fatalf("len(rates) = %d, want 1", len(rates))
	}
	r := rates[0]
	if r.Prefix != "gemini-2.5" || r.Input != 1.25 || r.Output != 10 || r.CacheRead != 0.31 || r.CacheWrite != 1.625 {
		t.Errorf("parsed rate = %+v, want prefix gemini-2.5 with input 1.25 output 10 cache_read 0.31 cache_write 1.625", r)
	}
}

// TestPricingGoldenFixturesComputeCost exercises both compute paths through
// golden OTLP/JSON fixtures: the Claude-table path and the user-config path.
func TestPricingGoldenFixturesComputeCost(t *testing.T) {
	// Claude-table compute path.
	claudeData, err := os.ReadFile("testdata/pricing_claude_compute.json")
	if err != nil {
		t.Fatalf("ReadFile() error = %v", err)
	}
	acc := NewAccumulator()
	if err := acc.AddJSON(claudeData); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	samples, skipped := acc.Flush()
	if skipped != 0 || len(samples) != 1 {
		t.Fatalf("Flush() = %d samples, %d skipped, want 1, 0", len(samples), skipped)
	}
	// claude-sonnet- rates on 200 input + 80 output = 200*3 + 80*15 = 1800.
	if got := samples[0].Values["cost_microusd"]; got != 1800 {
		t.Errorf("Claude-table cost_microusd = %d, want 1800", got)
	}

	// User-config compute path.
	cfgData, err := os.ReadFile("testdata/pricing_user_config.json")
	if err != nil {
		t.Fatalf("ReadFile() error = %v", err)
	}
	rates, err := ParseUserPricing(cfgData)
	if err != nil {
		t.Fatalf("ParseUserPricing() error = %v", err)
	}
	modelData, err := os.ReadFile("testdata/pricing_user_model.json")
	if err != nil {
		t.Fatalf("ReadFile() error = %v", err)
	}
	acc2 := NewAccumulator()
	acc2.SetUserPricing(rates)
	if err := acc2.AddJSON(modelData); err != nil {
		t.Fatalf("AddJSON() error = %v", err)
	}
	samples2, skipped2 := acc2.Flush()
	if skipped2 != 0 || len(samples2) != 1 {
		t.Fatalf("Flush() = %d samples, %d skipped, want 1, 0", len(samples2), skipped2)
	}
	// gemini-2.5 user rates on 100 input + 50 output = 100*1.25 + 50*10 = 625.
	if got := samples2[0].Values["cost_microusd"]; got != 625 {
		t.Errorf("user-config cost_microusd = %d, want 625", got)
	}
}

// --- Benchmark ---

// benchBatch builds one OTLP/JSON export object with n token-bearing gen_ai
// spans. Each carries a distinct ID + chain parent and representative
// attributes, including multi-KB prompt/completion text bodies — the payload
// shape the three-pass round-trip re-encodes wholesale and the splice copies
// verbatim.
func benchBatch(n int) []byte {
	prompt := strings.Repeat("Summarize the following document in three bullet points. ", 40)
	completion := strings.Repeat("The system processes OTLP trace batches into profiling samples. ", 40)
	spans := make([]string, n)
	for i := 0; i < n; i++ {
		sid := fmt.Sprintf("%016x", i+1)
		parent := ""
		if i > 0 {
			parent = fmt.Sprintf("%016x", i)
		}
		spans[i] = tokenSpan(sid, parent, fmt.Sprintf("span-%d", i),
			strAttr("gen_ai.request.model", "claude-3"),
			strAttr("gen_ai.response.model", "claude-3-actual"),
			strAttr("gen_ai.system", "anthropic"),
			strAttr("gen_ai.prompt", prompt),
			strAttr("gen_ai.completion", completion),
			strAttr("http.url", "https://example.com/v1/messages?trace_id=not-a-key"))
	}
	return []byte(export("bench-svc", spans...))
}

func BenchmarkAddJSON(b *testing.B) {
	data := benchBatch(200)
	b.ReportAllocs()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		acc := NewAccumulator()
		if err := acc.AddJSON(data); err != nil {
			b.Fatalf("AddJSON() error = %v", err)
		}
	}
}
