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
	"time"

	commonv1 "go.opentelemetry.io/proto/otlp/common/v1"
	resourcev1 "go.opentelemetry.io/proto/otlp/resource/v1"
	tracev1 "go.opentelemetry.io/proto/otlp/trace/v1"
	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"

	"github.com/sticklane/agentprof/internal/schema"
)

const unknownService = "(unknown service)"

// Recognized usage-token attribute keys, highest precedence first.
var (
	inputTokenKeys  = []string{"gen_ai.usage.input_tokens", "gen_ai.usage.prompt_tokens"}
	outputTokenKeys = []string{"gen_ai.usage.output_tokens", "gen_ai.usage.completion_tokens"}
)

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
	model        string
	system       string
}

type tokenMetric struct {
	value   int64
	present bool
}

// Accumulator collects spans from decoded OTLP trace batches.
type Accumulator struct {
	spans map[spanKey]*spanRec
	order []spanKey // first-seen order
}

// NewAccumulator returns an empty span accumulator.
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

// Len reports the number of distinct spans accumulated so far.
func (a *Accumulator) Len() int {
	return len(a.order)
}

// Flush resolves parent chains across everything accumulated and returns the
// samples in first-seen span order, plus the count of invalid skipped spans.
func (a *Accumulator) Flush() ([]schema.Sample, int) {
	var samples []schema.Sample
	skipped := 0
	for _, key := range a.order {
		rec := a.spans[key]
		if !rec.hasTokens {
			continue // frames-only span: context for descendants
		}
		if rec.invalid || rec.end < rec.start {
			skipped++
			continue
		}
		samples = append(samples, a.sample(rec))
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
	rec.model = firstString(attrs, "gen_ai.response.model", "gen_ai.request.model")
	rec.system = firstString(attrs, "gen_ai.system", "gen_ai.provider.name")
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

func (a *Accumulator) sample(rec *spanRec) schema.Sample {
	values := map[string]int64{
		"calls":   1,
		"wall_ms": int64((rec.end - rec.start + 500_000) / 1_000_000),
	}
	if rec.input.present {
		values["input_tokens"] = rec.input.value
	}
	if rec.output.present {
		values["output_tokens"] = rec.output.value
	}
	labels := map[string]string{"source": "otel", "trace_id": rec.traceID}
	if rec.model != "" {
		labels["model"] = rec.model
	}
	if rec.system != "" {
		labels["system"] = rec.system
	}
	return schema.Sample{
		Time:   time.Unix(0, int64(rec.start)).UTC(),
		Stack:  a.stack(rec),
		Values: values,
		Labels: labels,
	}
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
