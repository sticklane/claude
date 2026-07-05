// Package bqtime parses the output shapes of `bq query --format=json` —
// timestamp strings, string-or-number scalars, and the array-or-JSONL row
// stream — shared by the BigQuery-fed adapters (gcp, vertex).
package bqtime

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"strconv"
	"strings"
	"time"
)

// Rows reads a bq export from r — either a JSON array of row objects or
// JSONL (one object per line) — and returns the raw rows. Blank lines are
// dropped; an empty input yields no rows. The error is non-nil only for I/O
// failures or an unreadable JSON array (malformed JSONL lines pass through
// for the caller to count as skipped).
func Rows(r io.Reader) ([]json.RawMessage, error) {
	br := bufio.NewReader(r)
	first, err := firstNonSpace(br)
	if err == io.EOF {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var raws []json.RawMessage
	if first == '[' {
		if err := json.NewDecoder(br).Decode(&raws); err != nil {
			return nil, fmt.Errorf("decoding JSON array: %w", err)
		}
		return raws, nil
	}
	sc := bufio.NewScanner(br)
	sc.Buffer(make([]byte, 0, 64*1024), 4*1024*1024)
	for sc.Scan() {
		line := bytes.TrimSpace(sc.Bytes())
		if len(line) == 0 {
			continue
		}
		raws = append(raws, append(json.RawMessage(nil), line...))
	}
	return raws, sc.Err()
}

// firstNonSpace peeks past leading whitespace without consuming input.
func firstNonSpace(br *bufio.Reader) (byte, error) {
	for {
		b, err := br.ReadByte()
		if err != nil {
			return 0, err
		}
		if b == ' ' || b == '\t' || b == '\n' || b == '\r' {
			continue
		}
		return b, br.UnreadByte()
	}
}

// RawString returns the contents of a JSON value that may be a string or a
// number ("1.5" and 1.5 both yield "1.5"); anything else yields "".
func RawString(raw json.RawMessage) string {
	var s string
	if json.Unmarshal(raw, &s) == nil {
		return s
	}
	var n json.Number
	if json.Unmarshal(raw, &n) == nil {
		return n.String()
	}
	return ""
}

// Parse accepts the three verified bq timestamp forms and returns UTC:
// `YYYY-MM-DD HH:MM:SS[.ffffff][ UTC]`, RFC3339, and epoch seconds
// (possibly in scientific notation).
func Parse(s string) (time.Time, error) {
	if t, err := time.Parse(time.RFC3339Nano, s); err == nil {
		return t.UTC(), nil
	}
	trimmed := strings.TrimSuffix(s, " UTC")
	// time.Parse accepts a fractional second after the seconds field even
	// when the layout omits it, so this covers the [.ffffff] variants.
	if t, err := time.ParseInLocation("2006-01-02 15:04:05", trimmed, time.UTC); err == nil {
		return t, nil
	}
	if f, err := strconv.ParseFloat(s, 64); err == nil {
		sec, frac := math.Modf(f)
		return time.Unix(int64(sec), int64(math.Round(frac*1e9))).UTC(), nil
	}
	return time.Time{}, fmt.Errorf("unrecognized timestamp %q", s)
}
