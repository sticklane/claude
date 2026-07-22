package otel

import (
	"os"
	"path/filepath"
	"testing"

	commonv1 "go.opentelemetry.io/proto/otlp/common/v1"
	metricsv1 "go.opentelemetry.io/proto/otlp/metrics/v1"
	"google.golang.org/protobuf/proto"
)

// metricsExportJSON is one OTLP/JSON metrics export carrying a
// claude_code.token.usage counter (bucketed by the `type` attribute) and a
// claude_code.cost.usage counter in fractional USD.
func metricsExportJSON() string {
	return `{"resourceMetrics":[{"resource":{"attributes":[{"key":"service.name","value":{"stringValue":"claude-code"}}]},` +
		`"scopeMetrics":[{"metrics":[` +
		`{"name":"claude_code.token.usage","sum":{"aggregationTemporality":2,"isMonotonic":true,"dataPoints":[` +
		`{"attributes":[{"key":"type","value":{"stringValue":"input"}}],"asInt":"100"},` +
		`{"attributes":[{"key":"type","value":{"stringValue":"output"}}],"asInt":"50"},` +
		`{"attributes":[{"key":"type","value":{"stringValue":"cacheRead"}}],"asInt":"200"},` +
		`{"attributes":[{"key":"type","value":{"stringValue":"cacheCreation"}}],"asInt":"40"}` +
		`]}},` +
		`{"name":"claude_code.cost.usage","sum":{"aggregationTemporality":2,"isMonotonic":true,"dataPoints":[` +
		`{"attributes":[{"key":"model","value":{"stringValue":"claude-sonnet"}}],"asDouble":0.041230}` +
		`]}}` +
		`]}]}]}`
}

func TestDecodeMetricsJSONSumsCoarseTokenTotals(t *testing.T) {
	tot, err := DecodeMetricsJSON([]byte(metricsExportJSON()))
	if err != nil {
		t.Fatalf("DecodeMetricsJSON() error = %v", err)
	}
	if tot.InputTokens != 100 {
		t.Errorf("InputTokens = %d, want 100", tot.InputTokens)
	}
	if tot.OutputTokens != 50 {
		t.Errorf("OutputTokens = %d, want 50", tot.OutputTokens)
	}
	if tot.CacheReadTokens != 200 {
		t.Errorf("CacheReadTokens = %d, want 200", tot.CacheReadTokens)
	}
	if tot.CacheWriteTokens != 40 {
		t.Errorf("CacheWriteTokens = %d, want 40", tot.CacheWriteTokens)
	}
}

func TestDecodeMetricsJSONConvertsCostToMicroUSD(t *testing.T) {
	tot, err := DecodeMetricsJSON([]byte(metricsExportJSON()))
	if err != nil {
		t.Fatalf("DecodeMetricsJSON() error = %v", err)
	}
	if tot.CostMicroUSD != 41230 {
		t.Errorf("CostMicroUSD = %d, want 41230", tot.CostMicroUSD)
	}
}

func TestDecodeMetricsJSONCountsConsumedPoints(t *testing.T) {
	tot, err := DecodeMetricsJSON([]byte(metricsExportJSON()))
	if err != nil {
		t.Fatalf("DecodeMetricsJSON() error = %v", err)
	}
	if tot.Points != 5 {
		t.Errorf("Points = %d, want 5 (4 token + 1 cost)", tot.Points)
	}
}

func TestDecodeMetricsProtoSumsCoarseTotals(t *testing.T) {
	md := &metricsv1.MetricsData{
		ResourceMetrics: []*metricsv1.ResourceMetrics{{
			ScopeMetrics: []*metricsv1.ScopeMetrics{{
				Metrics: []*metricsv1.Metric{
					{
						Name: "claude_code.token.usage",
						Data: &metricsv1.Metric_Sum{Sum: &metricsv1.Sum{DataPoints: []*metricsv1.NumberDataPoint{
							tokenPoint("input", 100),
							tokenPoint("output", 50),
						}}},
					},
					{
						Name: "claude_code.cost.usage",
						Data: &metricsv1.Metric_Sum{Sum: &metricsv1.Sum{DataPoints: []*metricsv1.NumberDataPoint{
							costPoint(0.041230),
						}}},
					},
				},
			}},
		}},
	}
	raw, err := proto.Marshal(md)
	if err != nil {
		t.Fatalf("proto.Marshal: %v", err)
	}
	tot, err := DecodeMetricsProto(raw)
	if err != nil {
		t.Fatalf("DecodeMetricsProto() error = %v", err)
	}
	if tot.InputTokens != 100 || tot.OutputTokens != 50 {
		t.Errorf("tokens = (%d,%d), want (100,50)", tot.InputTokens, tot.OutputTokens)
	}
	if tot.CostMicroUSD != 41230 {
		t.Errorf("CostMicroUSD = %d, want 41230", tot.CostMicroUSD)
	}
}

// GaugeDataPoints are decoded the same as Sum data points (coarse totals do
// not distinguish instrument kind).
func TestDecodeMetricsGaugeInstrumentDecodes(t *testing.T) {
	md := &metricsv1.MetricsData{
		ResourceMetrics: []*metricsv1.ResourceMetrics{{
			ScopeMetrics: []*metricsv1.ScopeMetrics{{
				Metrics: []*metricsv1.Metric{{
					Name: "claude_code.token.usage",
					Data: &metricsv1.Metric_Gauge{Gauge: &metricsv1.Gauge{DataPoints: []*metricsv1.NumberDataPoint{
						tokenPoint("input", 7),
					}}},
				}},
			}},
		}},
	}
	raw, err := proto.Marshal(md)
	if err != nil {
		t.Fatalf("proto.Marshal: %v", err)
	}
	tot, err := DecodeMetricsProto(raw)
	if err != nil {
		t.Fatalf("DecodeMetricsProto() error = %v", err)
	}
	if tot.InputTokens != 7 {
		t.Errorf("InputTokens = %d, want 7", tot.InputTokens)
	}
}

func TestDecodeMetricsGoldenFixture(t *testing.T) {
	data, err := os.ReadFile(filepath.Join("testdata", "metrics_coarse.json"))
	if err != nil {
		t.Fatalf("reading fixture: %v", err)
	}
	tot, err := DecodeMetricsJSON(data)
	if err != nil {
		t.Fatalf("DecodeMetricsJSON() error = %v", err)
	}
	if tot.InputTokens != 100 || tot.OutputTokens != 50 || tot.CostMicroUSD != 41230 {
		t.Errorf("totals = %+v, want input 100 output 50 cost 41230", tot)
	}
}

func tokenPoint(typ string, v int64) *metricsv1.NumberDataPoint {
	return &metricsv1.NumberDataPoint{
		Attributes: []*commonv1.KeyValue{{
			Key:   "type",
			Value: &commonv1.AnyValue{Value: &commonv1.AnyValue_StringValue{StringValue: typ}},
		}},
		Value: &metricsv1.NumberDataPoint_AsInt{AsInt: v},
	}
}

func costPoint(usd float64) *metricsv1.NumberDataPoint {
	return &metricsv1.NumberDataPoint{
		Value: &metricsv1.NumberDataPoint_AsDouble{AsDouble: usd},
	}
}
