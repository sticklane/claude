package otel

import (
	"math"

	commonv1 "go.opentelemetry.io/proto/otlp/common/v1"
	metricsv1 "go.opentelemetry.io/proto/otlp/metrics/v1"
	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"
)

// MetricTotals holds the coarse token/cost sums decoded from an OTLP metrics
// export. Metrics are the lowest-fidelity ingestion tier (SPEC design pt 1,
// "coarse cross-check") — they carry no trace context, so they never produce
// or override a trace-derived sample; they are a summed cross-check signal
// only. Points counts the numeric data points consumed from recognized
// token/cost metrics.
type MetricTotals struct {
	InputTokens      int64
	OutputTokens     int64
	CacheReadTokens  int64
	CacheWriteTokens int64
	CostMicroUSD     int64
	Points           int
}

// tokenUsageMetricNames name the counter/gauge carrying per-request token
// counts, bucketed by a `type` attribute. Claude Code emits
// claude_code.token.usage; the list stays data-driven like the span dialect
// table since the GenAI metrics semconv is pre-stable.
var tokenUsageMetricNames = map[string]bool{
	"claude_code.token.usage": true,
}

// costUsageMetricNames name the counter carrying cumulative fractional-USD
// cost.
var costUsageMetricNames = map[string]bool{
	"claude_code.cost.usage": true,
}

// tokenTypeAttrKeys name the data-point attribute distinguishing which token
// bucket a claude_code.token.usage point belongs to, highest precedence first.
var tokenTypeAttrKeys = []string{"type", "gen_ai.token.type"}

// Add accumulates another batch's totals into t (receiver-side accumulation
// across POSTed metric batches).
func (t *MetricTotals) Add(o *MetricTotals) {
	if o == nil {
		return
	}
	t.InputTokens += o.InputTokens
	t.OutputTokens += o.OutputTokens
	t.CacheReadTokens += o.CacheReadTokens
	t.CacheWriteTokens += o.CacheWriteTokens
	t.CostMicroUSD += o.CostMicroUSD
	t.Points += o.Points
}

// DecodeMetricsJSON decodes one OTLP/JSON metrics-export object into coarse
// totals. Unlike traces and logs, metric data points carry no hex ID fields,
// so no base64 rewrite is needed before unmarshaling.
func DecodeMetricsJSON(data []byte) (*MetricTotals, error) {
	var md metricsv1.MetricsData
	opts := protojson.UnmarshalOptions{DiscardUnknown: true}
	if err := opts.Unmarshal(data, &md); err != nil {
		return nil, err
	}
	return sumMetrics(&md), nil
}

// DecodeMetricsProto decodes OTLP protobuf metrics data into coarse totals.
func DecodeMetricsProto(data []byte) (*MetricTotals, error) {
	var md metricsv1.MetricsData
	if err := proto.Unmarshal(data, &md); err != nil {
		return nil, err
	}
	return sumMetrics(&md), nil
}

// sumMetrics walks every resource/scope/metric and sums the token and cost
// data points of the recognized metrics into coarse totals.
func sumMetrics(md *metricsv1.MetricsData) *MetricTotals {
	tot := &MetricTotals{}
	for _, rm := range md.GetResourceMetrics() {
		for _, sm := range rm.GetScopeMetrics() {
			for _, m := range sm.GetMetrics() {
				switch {
				case tokenUsageMetricNames[m.GetName()]:
					for _, dp := range numberDataPoints(m) {
						tot.addTokenPoint(dp)
					}
				case costUsageMetricNames[m.GetName()]:
					for _, dp := range numberDataPoints(m) {
						tot.addCostPoint(dp)
					}
				}
			}
		}
	}
	return tot
}

// numberDataPoints returns a metric's numeric data points from whichever of
// its Sum/Gauge instrument kinds is set (coarse totals do not distinguish
// monotonic counters from gauges).
func numberDataPoints(m *metricsv1.Metric) []*metricsv1.NumberDataPoint {
	switch {
	case m.GetSum() != nil:
		return m.GetSum().GetDataPoints()
	case m.GetGauge() != nil:
		return m.GetGauge().GetDataPoints()
	}
	return nil
}

// addTokenPoint buckets one token.usage data point by its `type` attribute.
// A negative value or an unrecognized bucket is skipped without counting.
func (t *MetricTotals) addTokenPoint(dp *metricsv1.NumberDataPoint) {
	v, ok := numberValue(dp)
	if !ok {
		return
	}
	n := int64(math.Round(v))
	if n < 0 {
		return
	}
	switch tokenType(dp.GetAttributes()) {
	case "input":
		t.InputTokens += n
	case "output":
		t.OutputTokens += n
	case "cacheRead", "cache_read":
		t.CacheReadTokens += n
	case "cacheCreation", "cache_creation":
		t.CacheWriteTokens += n
	default:
		return // unrecognized token bucket: not a consumed point
	}
	t.Points++
}

// addCostPoint sums one cost.usage data point, converting fractional USD to
// integer micro-USD via round(cost * 1e6).
func (t *MetricTotals) addCostPoint(dp *metricsv1.NumberDataPoint) {
	v, ok := numberValue(dp)
	if !ok || v < 0 {
		return
	}
	t.CostMicroUSD += int64(math.Round(v * 1e6))
	t.Points++
}

// numberValue reads a NumberDataPoint's value as a float64, from whichever of
// its AsInt/AsDouble oneof arms is set.
func numberValue(dp *metricsv1.NumberDataPoint) (float64, bool) {
	switch v := dp.GetValue().(type) {
	case *metricsv1.NumberDataPoint_AsInt:
		return float64(v.AsInt), true
	case *metricsv1.NumberDataPoint_AsDouble:
		return v.AsDouble, true
	}
	return 0, false
}

// tokenType returns the token bucket named by a data point's `type`
// attribute (highest-precedence key first), or "" when absent.
func tokenType(attrs []*commonv1.KeyValue) string {
	for _, want := range tokenTypeAttrKeys {
		for _, kv := range attrs {
			if kv.GetKey() == want {
				if s := kv.GetValue().GetStringValue(); s != "" {
					return s
				}
			}
		}
	}
	return ""
}
