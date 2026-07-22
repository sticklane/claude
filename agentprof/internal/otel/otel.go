// Package otel converts OTLP trace data into agentprof samples. Spans are
// accumulated across batches (parents may arrive separately), then resolved
// into stacks and emitted in a single Flush.
package otel

import (
	"bytes"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"io"
	"math"
	"strings"
	"time"

	commonv1 "go.opentelemetry.io/proto/otlp/common/v1"
	logsv1 "go.opentelemetry.io/proto/otlp/logs/v1"
	resourcev1 "go.opentelemetry.io/proto/otlp/resource/v1"
	tracev1 "go.opentelemetry.io/proto/otlp/trace/v1"
	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"

	"github.com/sticklane/agentprof/internal/schema"
)

const (
	unknownService = "(unknown service)"
	unknownEvent   = "(unknown event)"
)

// costUSDKeys are the log-record attribute keys carrying an explicit fractional
// USD cost, highest precedence first. Claude Code emits bare cost_usd; the
// value converts to integer cost_microusd via round(cost_usd * 1e6).
var costUSDKeys = []string{"cost_usd", "gen_ai.usage.cost"}

// Recognized usage-token attribute keys, highest precedence first. Claude
// Code emits bare keys rather than the GenAI semconv's gen_ai.usage.*
// aliases, so the bare keys lead each list.
var (
	inputTokenKeys  = []string{"input_tokens", "gen_ai.usage.input_tokens", "gen_ai.usage.prompt_tokens"}
	outputTokenKeys = []string{"output_tokens", "gen_ai.usage.output_tokens", "gen_ai.usage.completion_tokens"}

	// cacheReadTokenKeys resolves directly to the canonical cache_read_tokens
	// sample value. cacheCreationTokenKeys resolves to a value that sample()
	// renames to the canonical cache_write_tokens key (SCHEMA.md) — passing
	// the source key through verbatim would silently drop cache-write signal
	// from pprof token profiles.
	cacheReadTokenKeys     = []string{"cache_read_tokens"}
	cacheCreationTokenKeys = []string{"cache_creation_tokens"}
)

// dialect identifies one CLI's OTel export convention by its span-name
// prefix. Task 04 appends gemini_cli.*/qwen-code.*/codex.* entries to
// dialects below without reshaping this type or detectDialect's loop —
// alias lists stay data-driven since the GenAI semconv is pre-stable.
type dialect struct {
	name       string
	spanPrefix string
}

var dialects = []dialect{
	{name: "claude_code", spanPrefix: "claude_code."},
}

// detectDialect returns the matched dialect's name for a span, or "" when
// no span-name prefix matches (the generic gen_ai.* fallback).
func detectDialect(spanName string) string {
	for _, d := range dialects {
		if strings.HasPrefix(spanName, d.spanPrefix) {
			return d.name
		}
	}
	return ""
}

type spanKey struct{ traceID, spanID string }

type spanRec struct {
	name         string
	traceID      string // lowercase hex
	spanID       string
	parentSpanID string
	start, end   uint64
	serviceName  string
	hasTokens    bool // at least one recognized token key present
	invalid      bool // recognized token key with negative or non-int value
	input        tokenMetric
	output       tokenMetric
	cacheRead    tokenMetric
	cacheWrite   tokenMetric // sourced from cache_creation_tokens; canonical name applied in sample()
	model        string
	system       string
	dialect      string // detected export dialect, e.g. "claude_code"; "" = generic
}

type tokenMetric struct {
	value   int64
	present bool
}

// logRec is a decoded OTLP log record carrying an explicit cost. When its
// trace_id/span_id match a span, its cost joins onto that span's sample;
// without trace context it degrades to a flat [service, event-name] sample.
type logRec struct {
	traceID     string // lowercase hex ("" = absent)
	spanID      string // lowercase hex ("" = absent)
	timestamp   uint64
	serviceName string
	eventName   string
	costMicro   int64
	hasCost     bool
}

// Accumulator collects spans and cost-bearing log records from decoded OTLP
// batches.
type Accumulator struct {
	spans map[spanKey]*spanRec
	order []spanKey // first-seen order
	logs  []*logRec // cost/log records in first-seen order
}

// NewAccumulator returns an empty accumulator.
func NewAccumulator() *Accumulator {
	return &Accumulator{spans: make(map[spanKey]*spanRec)}
}

// AddJSON decodes one OTLP/JSON trace-export object and accumulates its
// spans. Per the OTLP JSON spec, trace/span/parent IDs are hex strings, not
// the base64 protojson expects, so they are rewritten before unmarshaling.
func (a *Accumulator) AddJSON(data []byte) error {
	fixed, err := hexIDsToBase64(data)
	if err != nil {
		return err
	}
	var td tracev1.TracesData
	opts := protojson.UnmarshalOptions{DiscardUnknown: true}
	if err := opts.Unmarshal(fixed, &td); err != nil {
		return err
	}
	a.add(&td)
	return nil
}

// AddProto decodes OTLP protobuf trace data and accumulates its spans.
func (a *Accumulator) AddProto(data []byte) error {
	var td tracev1.TracesData
	if err := proto.Unmarshal(data, &td); err != nil {
		return err
	}
	a.add(&td)
	return nil
}

// AddLogsJSON decodes one OTLP/JSON logs-export object and accumulates its
// records. Like AddJSON, the hex trace_id/span_id fields are rewritten to the
// base64 protojson expects before unmarshaling.
func (a *Accumulator) AddLogsJSON(data []byte) error {
	fixed, err := hexIDsToBase64(data)
	if err != nil {
		return err
	}
	var ld logsv1.LogsData
	opts := protojson.UnmarshalOptions{DiscardUnknown: true}
	if err := opts.Unmarshal(fixed, &ld); err != nil {
		return err
	}
	a.addLogs(&ld)
	return nil
}

// AddLogsProto decodes OTLP protobuf logs data and accumulates its records.
func (a *Accumulator) AddLogsProto(data []byte) error {
	var ld logsv1.LogsData
	if err := proto.Unmarshal(data, &ld); err != nil {
		return err
	}
	a.addLogs(&ld)
	return nil
}

// Len reports the number of distinct spans accumulated so far.
func (a *Accumulator) Len() int {
	return len(a.order)
}

// LogLen reports the number of log records accumulated so far.
func (a *Accumulator) LogLen() int {
	return len(a.logs)
}

// Flush resolves parent chains across everything accumulated and returns the
// samples, plus the count of invalid skipped spans. Cost-bearing log records
// join onto the span whose (trace_id, span_id) they name directly (the
// frames-only-ancestor descendant walk is Task 03); the emit gate is relaxed
// to hasTokens OR attached cost. Span samples come first in first-seen span
// order, then flat samples for records without trace context.
func (a *Accumulator) Flush() ([]schema.Sample, int) {
	// Index each cost record onto the span it names directly. Multiple records
	// targeting one span sum. A record naming no accumulated span attaches
	// nothing here (Task 03's descendant fallback completes that path).
	costBySpan := make(map[spanKey]int64)
	for _, lr := range a.logs {
		if !lr.hasCost || lr.traceID == "" || lr.spanID == "" {
			continue
		}
		key := spanKey{lr.traceID, lr.spanID}
		if _, ok := a.spans[key]; ok {
			costBySpan[key] += lr.costMicro
		}
	}

	var samples []schema.Sample
	skipped := 0
	for _, key := range a.order {
		rec := a.spans[key]
		cost, hasCost := costBySpan[key]
		if !rec.hasTokens && !hasCost {
			continue // frames-only span with no cost: context for descendants
		}
		if rec.invalid || rec.end < rec.start {
			skipped++
			continue
		}
		samples = append(samples, a.sample(rec, cost, hasCost))
	}

	// A record without trace context degrades to a flat [service, event] sample.
	for _, lr := range a.logs {
		if lr.traceID != "" && lr.spanID != "" {
			continue // had trace context (joined above, or unresolved for Task 03)
		}
		if !lr.hasCost {
			continue
		}
		samples = append(samples, flatSample(lr))
	}
	return samples, skipped
}

func (a *Accumulator) add(td *tracev1.TracesData) {
	for _, rs := range td.GetResourceSpans() {
		service := serviceName(rs.GetResource())
		for _, ss := range rs.GetScopeSpans() {
			for _, sp := range ss.GetSpans() {
				rec := newSpanRec(sp, service)
				key := spanKey{rec.traceID, rec.spanID}
				if _, dup := a.spans[key]; dup {
					continue // first delivery wins
				}
				a.spans[key] = rec
				a.order = append(a.order, key)
			}
		}
	}
}

func (a *Accumulator) addLogs(ld *logsv1.LogsData) {
	for _, rl := range ld.GetResourceLogs() {
		service := serviceName(rl.GetResource())
		for _, sl := range rl.GetScopeLogs() {
			for _, lr := range sl.GetLogRecords() {
				a.logs = append(a.logs, newLogRec(lr, service))
			}
		}
	}
}

func newLogRec(lr *logsv1.LogRecord, service string) *logRec {
	rec := &logRec{
		traceID:     hex.EncodeToString(lr.GetTraceId()),
		spanID:      hex.EncodeToString(lr.GetSpanId()),
		timestamp:   lr.GetTimeUnixNano(),
		serviceName: service,
		eventName:   lr.GetEventName(),
	}
	attrs := make(map[string]*commonv1.AnyValue, len(lr.GetAttributes()))
	for _, kv := range lr.GetAttributes() {
		if _, ok := attrs[kv.GetKey()]; !ok {
			attrs[kv.GetKey()] = kv.GetValue()
		}
	}
	if rec.eventName == "" {
		rec.eventName = firstString(attrs, "event.name")
	}
	rec.costMicro, rec.hasCost = costMicroUSD(attrs)
	return rec
}

// costMicroUSD resolves a fractional-USD cost attribute (highest-precedence key
// first) and converts it to integer micro-USD via round(cost * 1e6). Both
// double and integer USD values are accepted.
func costMicroUSD(attrs map[string]*commonv1.AnyValue) (int64, bool) {
	for _, k := range costUSDKeys {
		v, ok := attrs[k]
		if !ok {
			continue
		}
		switch val := v.GetValue().(type) {
		case *commonv1.AnyValue_DoubleValue:
			return int64(math.Round(val.DoubleValue * 1e6)), true
		case *commonv1.AnyValue_IntValue:
			return val.IntValue * 1_000_000, true
		}
	}
	return 0, false
}

func newSpanRec(sp *tracev1.Span, service string) *spanRec {
	rec := &spanRec{
		name:         sp.GetName(),
		traceID:      hex.EncodeToString(sp.GetTraceId()),
		spanID:       hex.EncodeToString(sp.GetSpanId()),
		parentSpanID: hex.EncodeToString(sp.GetParentSpanId()),
		start:        sp.GetStartTimeUnixNano(),
		end:          sp.GetEndTimeUnixNano(),
		serviceName:  service,
	}
	attrs := make(map[string]*commonv1.AnyValue, len(sp.GetAttributes()))
	for _, kv := range sp.GetAttributes() {
		if _, ok := attrs[kv.GetKey()]; !ok {
			attrs[kv.GetKey()] = kv.GetValue()
		}
	}
	rec.input = rec.tokenMetric(attrs, inputTokenKeys)
	rec.output = rec.tokenMetric(attrs, outputTokenKeys)
	rec.cacheRead = rec.tokenMetric(attrs, cacheReadTokenKeys)
	rec.cacheWrite = rec.tokenMetric(attrs, cacheCreationTokenKeys)
	rec.model = firstString(attrs, "gen_ai.response.model", "gen_ai.request.model")
	rec.system = firstString(attrs, "gen_ai.system", "gen_ai.provider.name")
	rec.dialect = detectDialect(rec.name)
	return rec
}

// tokenMetric resolves one metric from its alias keys (highest precedence
// first), recording token presence and marking the span invalid on a
// negative or non-int value under any recognized key.
func (r *spanRec) tokenMetric(attrs map[string]*commonv1.AnyValue, keys []string) tokenMetric {
	var m tokenMetric
	for _, k := range keys {
		v, ok := attrs[k]
		if !ok {
			continue
		}
		r.hasTokens = true
		iv, isInt := v.GetValue().(*commonv1.AnyValue_IntValue)
		if !isInt || iv.IntValue < 0 {
			r.invalid = true
			continue
		}
		if !m.present {
			m = tokenMetric{value: iv.IntValue, present: true}
		}
	}
	return m
}

func (a *Accumulator) sample(rec *spanRec, cost int64, hasCost bool) schema.Sample {
	s := schema.Sample{
		Time:  time.Unix(0, int64(rec.start)).UTC(),
		Stack: a.stack(rec),
		Values: map[string]int64{
			"calls":   1,
			"wall_ms": int64((rec.end - rec.start + 500_000) / 1_000_000),
		},
		Labels: map[string]string{"source": "otel", "trace_id": rec.traceID},
	}
	if hasCost {
		s.Values["cost_microusd"] = cost
	}
	if rec.input.present {
		s.Values["input_tokens"] = rec.input.value
	}
	if rec.output.present {
		s.Values["output_tokens"] = rec.output.value
	}
	if rec.cacheRead.present {
		s.Values["cache_read_tokens"] = rec.cacheRead.value
	}
	if rec.cacheWrite.present {
		s.Values["cache_write_tokens"] = rec.cacheWrite.value
	}
	if rec.model != "" {
		s.Labels["model"] = rec.model
	}
	if rec.system != "" {
		s.Labels["system"] = rec.system
	}
	return s
}

// flatSample renders a cost-bearing log record with no trace context as a
// two-frame [service, event-name] sample — token/cost intact, hierarchy absent.
func flatSample(lr *logRec) schema.Sample {
	svc := lr.serviceName
	if svc == "" {
		svc = unknownService
	}
	event := lr.eventName
	if event == "" {
		event = unknownEvent
	}
	s := schema.Sample{
		Time:   time.Unix(0, int64(lr.timestamp)).UTC(),
		Stack:  []string{svc, event},
		Values: map[string]int64{"calls": 1},
		Labels: map[string]string{"source": "otel"},
	}
	if lr.hasCost {
		s.Values["cost_microusd"] = lr.costMicro
	}
	return s
}

// stack builds the root-first frame list [service, root…leaf] by following
// parentSpanId links within the emitting span's trace. Missing parents stop
// the walk (orphan tolerance); a repeated span ID breaks cycles.
func (a *Accumulator) stack(rec *spanRec) []string {
	var names []string // leaf-first
	seen := make(map[string]bool)
	for cur := rec; !seen[cur.spanID]; {
		seen[cur.spanID] = true
		names = append(names, cur.name)
		if cur.parentSpanID == "" {
			break
		}
		parent, ok := a.spans[spanKey{cur.traceID, cur.parentSpanID}]
		if !ok {
			break
		}
		cur = parent
	}
	svc := rec.serviceName
	if svc == "" {
		svc = unknownService
	}
	stack := make([]string, 0, len(names)+1)
	stack = append(stack, svc)
	for i := len(names) - 1; i >= 0; i-- {
		stack = append(stack, names[i])
	}
	return stack
}

func serviceName(res *resourcev1.Resource) string {
	for _, kv := range res.GetAttributes() {
		if kv.GetKey() == "service.name" {
			return kv.GetValue().GetStringValue()
		}
	}
	return ""
}

func firstString(attrs map[string]*commonv1.AnyValue, keys ...string) string {
	for _, k := range keys {
		if v, ok := attrs[k]; ok {
			if s := v.GetStringValue(); s != "" {
				return s
			}
		}
	}
	return ""
}

// idJSONKeys are the bytes fields whose OTLP/JSON encoding is hex rather
// than the base64 protojson expects (32/16 hex chars are coincidentally
// valid base64, so a naive decode is silently wrong).
var idJSONKeys = map[string]bool{
	"traceId": true, "trace_id": true,
	"spanId": true, "span_id": true,
	"parentSpanId": true, "parent_span_id": true,
}

// hexIDsToBase64 rewrites the six OTLP/JSON ID fields (hex) into the base64
// protojson expects, touching nothing else. It runs one json.Decoder pass to
// locate the byte span of each ID *value* (only object-key position counts),
// then splices hex→base64 into the original bytes in place. Every non-ID byte
// — whitespace, key order, number formatting — is preserved verbatim: there is
// no any-tree and no re-marshal.
func hexIDsToBase64(data []byte) ([]byte, error) {
	spans, err := findIDValueSpans(data)
	if err != nil {
		return nil, err
	}
	if len(spans) == 0 {
		return data, nil
	}
	// base64 is longer than the hex it replaces, so len(data) is a safe lower
	// bound; pre-sizing avoids append-growth reallocations.
	out := make([]byte, 0, len(data)+len(spans)*8)
	prev := 0
	for _, s := range spans {
		raw := data[s.start:s.end]
		b, decErr := hex.DecodeString(string(raw))
		if decErr != nil {
			continue // not hex: leave the value untouched (matches skip behavior)
		}
		out = append(out, data[prev:s.start]...)
		out = append(out, base64.StdEncoding.EncodeToString(b)...)
		prev = s.end
	}
	if out == nil {
		return data, nil // no span was valid hex
	}
	out = append(out, data[prev:]...)
	return out, nil
}

// idSpan is the byte range of an ID string value's content, exclusive of the
// surrounding quotes.
type idSpan struct{ start, end int }

// findIDValueSpans scans data once and returns, in order, the content byte
// span of every string value whose object key is one of idJSONKeys.
func findIDValueSpans(data []byte) ([]idSpan, error) {
	dec := json.NewDecoder(bytes.NewReader(data))
	// stack tracks container nesting; for objects, wantKey toggles between
	// expecting a key and expecting its value.
	type frame struct {
		isObject bool
		wantKey  bool
	}
	var stack []frame
	completeValue := func() {
		if n := len(stack); n > 0 && stack[n-1].isObject {
			stack[n-1].wantKey = true
		}
	}
	var spans []idSpan
	var pendingIDKey bool // the last-read key is an ID key awaiting its value
	var keyEnd int64      // input offset just past that key's closing quote
	for {
		tok, err := dec.Token()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}
		switch t := tok.(type) {
		case json.Delim:
			switch t {
			case '{':
				stack = append(stack, frame{isObject: true, wantKey: true})
			case '[':
				stack = append(stack, frame{})
			case '}', ']':
				stack = stack[:len(stack)-1]
				completeValue()
			}
			pendingIDKey = false
		default: // string, float64, bool, or nil
			n := len(stack)
			if n > 0 && stack[n-1].isObject && stack[n-1].wantKey {
				stack[n-1].wantKey = false
				key, _ := t.(string)
				if idJSONKeys[key] {
					pendingIDKey = true
					keyEnd = dec.InputOffset()
				} else {
					pendingIDKey = false
				}
				continue
			}
			if pendingIDKey {
				if _, ok := t.(string); ok {
					// The value's opening quote is the first '"' at or after
					// keyEnd (only ':' and whitespace precede it); InputOffset
					// is just past the closing quote.
					open := int(keyEnd) + bytes.IndexByte(data[keyEnd:], '"')
					spans = append(spans, idSpan{start: open + 1, end: int(dec.InputOffset()) - 1})
				}
				pendingIDKey = false
			}
			completeValue()
		}
	}
	return spans, nil
}
