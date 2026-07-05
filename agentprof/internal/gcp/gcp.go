// Package gcp parses GCP billing standard-export rows (as emitted by
// `bq query --format=json`) into canonical agentprof samples (R9).
package gcp

import (
	"encoding/json"
	"io"
	"math"
	"strconv"

	"github.com/sticklane/agentprof/internal/bqtime"
	"github.com/sticklane/agentprof/internal/schema"
)

// row is one billing-export row. bq emits the selected structs as nested
// objects; aliased flat keys (project_id, ...) are accepted as a fallback.
type row struct {
	Project struct {
		ID string `json:"id"`
	} `json:"project"`
	ProjectID string `json:"project_id"`
	Service   struct {
		Description string `json:"description"`
	} `json:"service"`
	ServiceDescription string `json:"service_description"`
	SKU                struct {
		Description string `json:"description"`
	} `json:"sku"`
	SKUDescription string `json:"sku_description"`
	// bq emits timestamps and numerics as strings or numbers; decode raw
	// and normalize in parseRow.
	UsageStartTime json.RawMessage `json:"usage_start_time"`
	Cost           json.RawMessage `json:"cost"`
	Currency       string          `json:"currency"`
	// Labels is decoded leniently in rowLabels: a malformed labels field
	// means no labels, never a skipped row (frame-naming SPEC R7).
	Labels json.RawMessage `json:"labels"`
}

// Parse reads billing rows (a JSON array or JSONL, as `bq query
// --format=json` emits them) from r and returns the valid samples plus the
// count of skipped rows. A row is skipped (counted, never fatal) when it is
// malformed, missing a required field, or has a negative cost (a credit).
// Each frameLabels key inserts one "key:value" frame after the project frame,
// in the given order, with "(none)" for rows lacking the key (R7). The error
// is non-nil only for I/O failures or an unreadable JSON array.
func Parse(r io.Reader, frameLabels []string) ([]schema.Sample, int, error) {
	raws, err := bqtime.Rows(r)
	if err != nil {
		return nil, 0, err
	}
	var samples []schema.Sample
	skipped := 0
	for _, raw := range raws {
		s, ok := parseRow(raw, frameLabels)
		if !ok {
			skipped++
			continue
		}
		samples = append(samples, s)
	}
	return samples, skipped, nil
}

func parseRow(raw json.RawMessage, frameLabels []string) (schema.Sample, bool) {
	var w row
	if err := json.Unmarshal(raw, &w); err != nil {
		return schema.Sample{}, false
	}
	project := coalesce(w.Project.ID, w.ProjectID)
	service := coalesce(w.Service.Description, w.ServiceDescription)
	sku := coalesce(w.SKU.Description, w.SKUDescription)
	if project == "" || service == "" || sku == "" || w.Currency == "" {
		return schema.Sample{}, false
	}
	t, err := bqtime.Parse(bqtime.RawString(w.UsageStartTime))
	if err != nil {
		return schema.Sample{}, false
	}
	cost, err := strconv.ParseFloat(bqtime.RawString(w.Cost), 64)
	if err != nil || cost < 0 {
		return schema.Sample{}, false
	}
	stack := []string{project}
	if len(frameLabels) > 0 {
		vals := rowLabels(w.Labels)
		for _, key := range frameLabels {
			v, ok := vals[key]
			if !ok {
				v = "(none)"
			}
			stack = append(stack, key+":"+v)
		}
	}
	stack = append(stack, service, sku)
	return schema.Sample{
		Time:  t,
		Stack: stack,
		Values: map[string]int64{
			"cost_microusd": int64(math.Round(cost * 1e6)),
			"calls":         1,
		},
		Labels: map[string]string{
			"source":   "gcp",
			"currency": w.Currency,
		},
	}, true
}

// rowLabels decodes a billing row's labels field (BigQuery export shape: an
// array of {key, value} string pairs) into a map, first occurrence of a key
// winning. Absent or malformed fields yield no labels.
func rowLabels(raw json.RawMessage) map[string]string {
	var pairs []struct {
		Key   string `json:"key"`
		Value string `json:"value"`
	}
	if json.Unmarshal(raw, &pairs) != nil {
		return nil
	}
	vals := map[string]string{}
	for _, p := range pairs {
		if _, dup := vals[p.Key]; !dup {
			vals[p.Key] = p.Value
		}
	}
	return vals
}

func coalesce(a, b string) string {
	if a != "" {
		return a
	}
	return b
}
