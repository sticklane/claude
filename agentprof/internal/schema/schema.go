// Package schema implements the canonical agentprof sample schema
// (agentprof/v1): one JSON object per JSONL line describing a costed event.
// See SCHEMA.md at the repo root for the contract.
package schema

import (
	"bufio"
	"encoding/json"
	"io"
	"strconv"
	"strings"
	"time"
)

// Sample is one costed event in the canonical schema.
type Sample struct {
	Time   time.Time         // required, RFC3339 on the wire
	Stack  []string          // required, non-empty, root first
	Values map[string]int64  // metric name -> non-negative integer
	Labels map[string]string // optional pprof string labels
}

// wireSample is the JSON shape of a sample line. Values decode via
// json.Number so non-integers (e.g. 1.5) are rejected during validation
// rather than silently truncated.
type wireSample struct {
	Time   string                 `json:"time"`
	Stack  []string               `json:"stack"`
	Values map[string]json.Number `json:"values,omitempty"`
	Labels map[string]string      `json:"labels,omitempty"`
}

// Read consumes JSONL from r and returns the valid samples plus the count of
// skipped lines. A line is skipped (counted, never fatal) when it is blank,
// malformed JSON, missing/empty/non-string stack, has a negative or
// non-integer value, or has a missing/non-RFC3339 time. The error is non-nil
// only for I/O failures on r.
func Read(r io.Reader) (samples []Sample, skipped int, err error) {
	sc := bufio.NewScanner(r)
	sc.Buffer(make([]byte, 0, 64*1024), 4*1024*1024)
	for sc.Scan() {
		s, ok := parseLine(sc.Bytes())
		if !ok {
			skipped++
			continue
		}
		samples = append(samples, s)
	}
	return samples, skipped, sc.Err()
}

func parseLine(line []byte) (Sample, bool) {
	if len(strings.TrimSpace(string(line))) == 0 {
		return Sample{}, false
	}
	var w wireSample
	if err := json.Unmarshal(line, &w); err != nil {
		return Sample{}, false
	}
	if len(w.Stack) == 0 {
		return Sample{}, false
	}
	t, err := time.Parse(time.RFC3339, w.Time)
	if err != nil {
		return Sample{}, false
	}
	values := make(map[string]int64, len(w.Values))
	for name, num := range w.Values {
		v, err := num.Int64()
		if err != nil || v < 0 {
			return Sample{}, false
		}
		values[name] = v
	}
	return Sample{Time: t, Stack: w.Stack, Values: values, Labels: w.Labels}, true
}

// MarshalLine encodes a sample as a single canonical-schema JSON line
// (no trailing newline) for adapters emitting JSONL.
func MarshalLine(s Sample) ([]byte, error) {
	w := wireSample{
		Time:   s.Time.UTC().Format(time.RFC3339Nano),
		Stack:  s.Stack,
		Labels: s.Labels,
	}
	if len(s.Values) > 0 {
		w.Values = make(map[string]json.Number, len(s.Values))
		for name, v := range s.Values {
			w.Values[name] = json.Number(strconv.FormatInt(v, 10))
		}
	}
	return json.Marshal(w)
}
