package otel

import (
	"encoding/base64"
	"encoding/hex"
	"fmt"
	"strings"
	"testing"
	"time"

	commonv1 "go.opentelemetry.io/proto/otlp/common/v1"
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
