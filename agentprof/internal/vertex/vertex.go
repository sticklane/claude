// Package vertex parses Vertex AI request-response logging rows (as emitted
// by `bq query --format=json` over the request_response_logging table) into
// canonical agentprof samples (vertex-logs-adapter SPEC).
package vertex

import (
	"encoding/json"
	"io"
	"strings"

	"github.com/sticklane/agentprof/internal/bqtime"
	"github.com/sticklane/agentprof/internal/pricing"
	"github.com/sticklane/agentprof/internal/schema"
)

// row is one request-response logging row. logging_time may arrive as a
// string or a number; full_response and response_payload entries may each be
// an inline JSON object or a JSON-encoded string (R6), so all decode raw.
type row struct {
	Endpoint        string            `json:"endpoint"`
	LoggingTime     json.RawMessage   `json:"logging_time"`
	APIMethod       string            `json:"api_method"`
	Model           string            `json:"model"`
	ResponsePayload []json.RawMessage `json:"response_payload"`
	FullResponse    json.RawMessage   `json:"full_response"`
}

// responseBody is the slice of a Gemini- or Anthropic-shaped response body
// the adapter reads. Usage token fields decode as pointers so shape
// detection (R7/R8) can distinguish absent from zero.
type responseBody struct {
	ModelVersion  string `json:"modelVersion"` // Gemini
	Model         string `json:"model"`        // Anthropic
	UsageMetadata *struct {
		PromptTokenCount        int64 `json:"promptTokenCount"`
		CandidatesTokenCount    int64 `json:"candidatesTokenCount"`
		ThoughtsTokenCount      int64 `json:"thoughtsTokenCount"`
		CachedContentTokenCount int64 `json:"cachedContentTokenCount"`
	} `json:"usageMetadata"`
	Usage *struct {
		InputTokens              *int64 `json:"input_tokens"`
		OutputTokens             *int64 `json:"output_tokens"`
		CacheReadInputTokens     int64  `json:"cache_read_input_tokens"`
		CacheCreationInputTokens int64  `json:"cache_creation_input_tokens"`
	} `json:"usage"`
}

// hasUsage reports whether the body carries recognizable token usage:
// Gemini-shaped (usageMetadata present) or Anthropic-shaped (usage with
// input_tokens or output_tokens).
func (b *responseBody) hasUsage() bool {
	if b.UsageMetadata != nil {
		return true
	}
	return b.Usage != nil && (b.Usage.InputTokens != nil || b.Usage.OutputTokens != nil)
}

// Parse reads logging rows (a JSON array or JSONL, as `bq query
// --format=json` emits them) from r and returns the valid samples plus the
// count of skipped rows. A row is skipped (counted, never fatal) when it is
// malformed, has no parseable logging_time, or has no response body with
// recognizable usage (R11). The error is non-nil only for I/O failures or an
// unreadable JSON array.
func Parse(r io.Reader) ([]schema.Sample, int, error) {
	raws, err := bqtime.Rows(r)
	if err != nil {
		return nil, 0, err
	}
	var samples []schema.Sample
	skipped := 0
	for _, raw := range raws {
		s, ok := parseRow(raw)
		if !ok {
			skipped++
			continue
		}
		samples = append(samples, s)
	}
	return samples, skipped, nil
}

func parseRow(raw json.RawMessage) (schema.Sample, bool) {
	var w row
	if err := json.Unmarshal(raw, &w); err != nil {
		return schema.Sample{}, false
	}
	t, err := bqtime.Parse(bqtime.RawString(w.LoggingTime))
	if err != nil {
		return schema.Sample{}, false
	}
	body := findUsageBody(w)
	if body == nil {
		return schema.Sample{}, false
	}

	project, location := endpointFrames(w.Endpoint)
	model := modelFrame(w.Model, body)

	values := map[string]int64{"calls": 1}
	var u pricing.Usage
	if m := body.UsageMetadata; m != nil {
		values["input_tokens"] = m.PromptTokenCount
		values["output_tokens"] = m.CandidatesTokenCount + m.ThoughtsTokenCount
		if m.CachedContentTokenCount > 0 {
			values["cache_read_tokens"] = m.CachedContentTokenCount
		}
		u = pricing.Usage{
			InputTokens:     m.PromptTokenCount,
			OutputTokens:    m.CandidatesTokenCount + m.ThoughtsTokenCount,
			CacheReadTokens: m.CachedContentTokenCount,
		}
	} else {
		us := body.Usage
		values["input_tokens"] = deref(us.InputTokens)
		values["output_tokens"] = deref(us.OutputTokens)
		if us.CacheReadInputTokens > 0 {
			values["cache_read_tokens"] = us.CacheReadInputTokens
		}
		if us.CacheCreationInputTokens > 0 {
			values["cache_write_tokens"] = us.CacheCreationInputTokens
		}
		u = pricing.Usage{
			InputTokens:         deref(us.InputTokens),
			OutputTokens:        deref(us.OutputTokens),
			CacheReadTokens:     us.CacheReadInputTokens,
			CacheCreationTokens: us.CacheCreationInputTokens,
		}
	}

	labels := map[string]string{"source": "vertex", "priced": "false"}
	// Vertex Claude ids use @-dated suffixes (claude-sonnet-4@20250514);
	// replacing @ with - matches the dated entries in the pricing table (R9).
	if cost, ok := pricing.Price(strings.ReplaceAll(model, "@", "-"), u); ok {
		values["cost_microusd"] = cost
		labels["priced"] = "true"
		labels["currency"] = "USD"
	}

	return schema.Sample{
		Time:   t,
		Stack:  []string{project, location, model, methodFrame(w.APIMethod)},
		Values: values,
		Labels: labels,
	}, true
}

// findUsageBody locates the response body carrying usage (R6): the
// full_response column if it has usage, else the response_payload entries
// scanned last to first (streaming puts usage on the final chunk).
func findUsageBody(w row) *responseBody {
	if b := decodeBody(w.FullResponse); b != nil && b.hasUsage() {
		return b
	}
	for i := len(w.ResponsePayload) - 1; i >= 0; i-- {
		if b := decodeBody(w.ResponsePayload[i]); b != nil && b.hasUsage() {
			return b
		}
	}
	return nil
}

// decodeBody unmarshals a response value that is either an inline JSON
// object or a JSON-encoded string of one (`bq query --format=json`
// serializes JSON-type columns as strings; other export paths inline them).
func decodeBody(raw json.RawMessage) *responseBody {
	if len(raw) == 0 {
		return nil
	}
	// A RawMessage starts at its value's first byte, so only string-encoded
	// bodies need the second unmarshal — skipping it for inline objects
	// avoids a guaranteed-fail validation pass over the largest bytes per row.
	if raw[0] == '"' {
		var s string
		if json.Unmarshal(raw, &s) != nil {
			return nil
		}
		raw = json.RawMessage(s)
	}
	var b responseBody
	if json.Unmarshal(raw, &b) != nil {
		return nil
	}
	return &b
}

// endpointFrames extracts the project and location segments from an endpoint
// resource name (projects/{project}/locations/{location}/...); anything else
// yields "(unknown)" for both (R4).
func endpointFrames(endpoint string) (project, location string) {
	parts := strings.Split(endpoint, "/")
	if len(parts) >= 4 && parts[0] == "projects" && parts[2] == "locations" &&
		parts[1] != "" && parts[3] != "" {
		return parts[1], parts[3]
	}
	return "(unknown)", "(unknown)"
}

// modelFrame picks the model frame (R5): the model column's final path
// segment, else the response body's model field per shape, else "(unknown)".
func modelFrame(col string, body *responseBody) string {
	if seg := col[strings.LastIndex(col, "/")+1:]; seg != "" {
		return seg
	}
	if body.UsageMetadata != nil && body.ModelVersion != "" {
		return body.ModelVersion
	}
	if body.Usage != nil && body.Model != "" {
		return body.Model
	}
	return "(unknown)"
}

// methodFrame returns the api_method column's final dot-segment; a bare
// value passes through and a missing one yields "(unknown)" (R5).
func methodFrame(method string) string {
	if method == "" {
		return "(unknown)"
	}
	return method[strings.LastIndex(method, ".")+1:]
}

func deref(p *int64) int64 {
	if p == nil {
		return 0
	}
	return *p
}
