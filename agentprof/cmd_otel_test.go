package main

import (
	"bytes"
	"compress/gzip"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"sync"
	"testing"

	commonv1 "go.opentelemetry.io/proto/otlp/common/v1"
	logsv1 "go.opentelemetry.io/proto/otlp/logs/v1"
	tracev1 "go.opentelemetry.io/proto/otlp/trace/v1"
	"google.golang.org/protobuf/proto"
)

const otelFixture = "testdata/otel-trace.json"

func runOtel(t *testing.T, args ...string) (code int, stdout, stderr string) {
	t.Helper()
	var out, errBuf bytes.Buffer
	code = run(append([]string{"otel"}, args...), &out, &errBuf)
	return code, out.String(), errBuf.String()
}

func fixtureFirstLine(t *testing.T) string {
	t.Helper()
	data, err := os.ReadFile(otelFixture)
	if err != nil {
		t.Fatalf("reading fixture: %v", err)
	}
	line, _, _ := strings.Cut(string(data), "\n")
	return line
}

func TestCmdOtelFixtureWritesCanonicalJSONLToStdout(t *testing.T) {
	code, stdout, stderr := runOtel(t, otelFixture)
	if code != 0 {
		t.Fatalf("exit code = %d, want 0 (stderr: %q)", code, stderr)
	}
	lines := strings.Split(strings.TrimSpace(stdout), "\n")
	if len(lines) != 3 {
		t.Fatalf("got %d samples, want 3 (stdout: %q)", len(lines), stdout)
	}
	var first struct {
		Stack  []string          `json:"stack"`
		Labels map[string]string `json:"labels"`
	}
	if err := json.Unmarshal([]byte(lines[0]), &first); err != nil {
		t.Fatalf("first line is not JSON: %v", err)
	}
	if first.Labels["source"] != "otel" {
		t.Errorf("labels.source = %q, want %q", first.Labels["source"], "otel")
	}
	if want := "0102030405060708090a0b0c0d0e0f10"; first.Labels["trace_id"] != want {
		t.Errorf("labels.trace_id = %q, want %q", first.Labels["trace_id"], want)
	}
	if want := []string{"demo-agent", "agent.run", "llm.chat"}; !reflect.DeepEqual(first.Stack, want) {
		t.Errorf("stack = %v, want %v", first.Stack, want)
	}
}

func TestCmdOtelFixtureReportsSkippedLinesAndSpans(t *testing.T) {
	code, _, stderr := runOtel(t, otelFixture)
	if code != 0 {
		t.Fatalf("exit code = %d, want 0 (stderr: %q)", code, stderr)
	}
	if want := "skipped 1 invalid line(s), 1 invalid span(s)"; !strings.Contains(stderr, want) {
		t.Errorf("stderr = %q, want it to contain %q", stderr, want)
	}
}

func TestCmdOtelWholeObjectFileOmitsSkipReport(t *testing.T) {
	path := filepath.Join(t.TempDir(), "single.json")
	if err := os.WriteFile(path, []byte(fixtureFirstLine(t)), 0o644); err != nil {
		t.Fatal(err)
	}
	code, stdout, stderr := runOtel(t, path)
	if code != 0 {
		t.Fatalf("exit code = %d, want 0 (stderr: %q)", code, stderr)
	}
	if strings.Contains(stderr, "skipped") {
		t.Errorf("stderr = %q, want no skipped report when nothing was skipped", stderr)
	}
	if lines := strings.Split(strings.TrimSpace(stdout), "\n"); len(lines) != 1 {
		t.Errorf("got %d samples, want 1", len(lines))
	}
}

func TestCmdOtelWritesPprofFileWithFlagAfterPositional(t *testing.T) {
	path := filepath.Join(t.TempDir(), "out.pb.gz")
	code, _, stderr := runOtel(t, otelFixture, "-o", path)
	if code != 0 {
		t.Fatalf("exit code = %d, want 0 (stderr: %q)", code, stderr)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("output file not written: %v", err)
	}
	if len(data) < 2 || data[0] != 0x1f || data[1] != 0x8b {
		t.Errorf("output is not gzip (first bytes % x)", data[:min(2, len(data))])
	}
}

func TestCmdOtelZeroValidSamplesExitsOne(t *testing.T) {
	path := filepath.Join(t.TempDir(), "frames-only.json")
	framesOnly := `{"resourceSpans":[{"resource":{},"scopeSpans":[{"spans":[{"traceId":"5152535455565758595a5b5c5d5e5f60","spanId":"0707070707070707","name":"no.tokens","startTimeUnixNano":"1","endTimeUnixNano":"2"}]}]}]}`
	if err := os.WriteFile(path, []byte(framesOnly), 0o644); err != nil {
		t.Fatal(err)
	}
	code, _, stderr := runOtel(t, path)
	if code != 1 {
		t.Fatalf("exit code = %d, want 1 (stderr: %q)", code, stderr)
	}
	if !strings.Contains(stderr, "no valid samples") {
		t.Errorf("stderr = %q, want a no-valid-samples diagnostic", stderr)
	}
}

func TestCmdOtelWrongArgCountExitsTwo(t *testing.T) {
	code, _, stderr := runOtel(t)
	if code != 2 {
		t.Fatalf("exit code = %d, want 2 (stderr: %q)", code, stderr)
	}
	if !strings.Contains(stderr, "usage") {
		t.Errorf("stderr = %q, want usage text", stderr)
	}
}

// --- Serve mode (R8, R9, R10) ---

// syncBuffer is an io.Writer safe for concurrent handler logging and
// post-hoc reads from the test goroutine.
type syncBuffer struct {
	mu sync.Mutex
	b  bytes.Buffer
}

func (s *syncBuffer) Write(p []byte) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.b.Write(p)
}

func (s *syncBuffer) String() string {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.b.String()
}

func startOtelServer(t *testing.T) (*httptest.Server, *otelReceiver, *syncBuffer) {
	t.Helper()
	logs := &syncBuffer{}
	rcv := newOtelReceiver(logs)
	srv := httptest.NewServer(rcv)
	t.Cleanup(srv.Close)
	return srv, rcv, logs
}

func postTraces(t *testing.T, baseURL, contentType string, body []byte) *http.Response {
	t.Helper()
	resp, err := http.Post(baseURL+"/v1/traces", contentType, bytes.NewReader(body))
	if err != nil {
		t.Fatalf("POST /v1/traces: %v", err)
	}
	t.Cleanup(func() { resp.Body.Close() })
	return resp
}

func protoTraceBody(t *testing.T) []byte {
	t.Helper()
	td := &tracev1.TracesData{
		ResourceSpans: []*tracev1.ResourceSpans{{
			ScopeSpans: []*tracev1.ScopeSpans{{
				Spans: []*tracev1.Span{{
					TraceId:           []byte{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16},
					SpanId:            []byte{9, 9, 9, 9, 9, 9, 9, 9},
					Name:              "proto.llm",
					StartTimeUnixNano: 1700000000000000000,
					EndTimeUnixNano:   1700000001000000000,
					Attributes: []*commonv1.KeyValue{{
						Key:   "gen_ai.usage.input_tokens",
						Value: &commonv1.AnyValue{Value: &commonv1.AnyValue_IntValue{IntValue: 33}},
					}},
				}},
			}},
		}},
	}
	raw, err := proto.Marshal(td)
	if err != nil {
		t.Fatalf("proto.Marshal: %v", err)
	}
	return raw
}

func TestOtelServeJSONPostReturnsJSONSuccessBody(t *testing.T) {
	srv, _, _ := startOtelServer(t)
	resp := postTraces(t, srv.URL, "application/json", []byte(fixtureFirstLine(t)))
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status = %d, want 200", resp.StatusCode)
	}
	if ct := resp.Header.Get("Content-Type"); ct != "application/json" {
		t.Errorf("Content-Type = %q, want application/json", ct)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		t.Fatalf("reading body: %v", err)
	}
	if string(body) != "{}" {
		t.Errorf("body = %q, want {}", body)
	}
}

func TestOtelServeProtobufPostReturnsEmptyBody(t *testing.T) {
	srv, _, _ := startOtelServer(t)
	resp := postTraces(t, srv.URL, "application/x-protobuf", protoTraceBody(t))
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status = %d, want 200", resp.StatusCode)
	}
	if ct := resp.Header.Get("Content-Type"); ct != "application/x-protobuf" {
		t.Errorf("Content-Type = %q, want application/x-protobuf", ct)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		t.Fatalf("reading body: %v", err)
	}
	if len(body) != 0 {
		t.Errorf("body = %q, want zero-length", body)
	}
}

func TestOtelServeLogsAcceptedSpanCountPerBatch(t *testing.T) {
	srv, _, logs := startOtelServer(t)
	postTraces(t, srv.URL, "application/json", []byte(fixtureFirstLine(t)))
	if want := "accepted 2 spans"; !strings.Contains(logs.String(), want) {
		t.Errorf("logs = %q, want them to contain %q", logs.String(), want)
	}
}

func TestOtelServeUndecodableJSONBodyReturns400(t *testing.T) {
	srv, _, _ := startOtelServer(t)
	resp := postTraces(t, srv.URL, "application/json", []byte("{not json"))
	if resp.StatusCode != http.StatusBadRequest {
		t.Errorf("status = %d, want 400", resp.StatusCode)
	}
}

func TestOtelServeUndecodableProtobufBodyReturns400(t *testing.T) {
	srv, _, _ := startOtelServer(t)
	resp := postTraces(t, srv.URL, "application/x-protobuf", []byte{0xff, 0xff, 0xff, 0xff})
	if resp.StatusCode != http.StatusBadRequest {
		t.Errorf("status = %d, want 400", resp.StatusCode)
	}
}

func TestOtelServeUnsupportedContentTypeReturns415(t *testing.T) {
	srv, _, _ := startOtelServer(t)
	resp := postTraces(t, srv.URL, "text/plain", []byte(fixtureFirstLine(t)))
	if resp.StatusCode != http.StatusUnsupportedMediaType {
		t.Errorf("status = %d, want 415", resp.StatusCode)
	}
}

func TestOtelServeGetOnTracesReturns405(t *testing.T) {
	srv, _, _ := startOtelServer(t)
	resp, err := http.Get(srv.URL + "/v1/traces")
	if err != nil {
		t.Fatalf("GET /v1/traces: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusMethodNotAllowed {
		t.Errorf("status = %d, want 405", resp.StatusCode)
	}
}

func TestOtelServeUnregisteredPathsReturn404(t *testing.T) {
	srv, _, _ := startOtelServer(t)
	for _, path := range []string{"/v1/metrics", "/"} {
		resp, err := http.Post(srv.URL+path, "application/json", strings.NewReader("{}"))
		if err != nil {
			t.Fatalf("POST %s: %v", path, err)
		}
		resp.Body.Close()
		if resp.StatusCode != http.StatusNotFound {
			t.Errorf("POST %s status = %d, want 404", path, resp.StatusCode)
		}
	}
}

func TestOtelServeConcurrentPostsAccumulateAllSpans(t *testing.T) {
	srv, rcv, _ := startOtelServer(t)
	const batches = 8
	var wg sync.WaitGroup
	errs := make(chan error, batches)
	for i := 0; i < batches; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			batch := fmt.Sprintf(`{"resourceSpans":[{"resource":{"attributes":[{"key":"service.name","value":{"stringValue":"svc"}}]},"scopeSpans":[{"spans":[{"traceId":"%032x","spanId":"%016x","name":"llm.call","startTimeUnixNano":"1","endTimeUnixNano":"2","attributes":[{"key":"gen_ai.usage.input_tokens","value":{"intValue":"7"}}]}]}]}]}`, i+1, i+1)
			resp, err := http.Post(srv.URL+"/v1/traces", "application/json", strings.NewReader(batch))
			if err != nil {
				errs <- err
				return
			}
			resp.Body.Close()
			if resp.StatusCode != http.StatusOK {
				errs <- fmt.Errorf("batch %d: status %d", i, resp.StatusCode)
			}
		}(i)
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		t.Fatal(err)
	}

	path := filepath.Join(t.TempDir(), "out.jsonl")
	var stdout, stderr bytes.Buffer
	if code := rcv.flush(path, &stdout, &stderr); code != 0 {
		t.Fatalf("flush exit code = %d, want 0 (stderr: %q)", code, stderr.String())
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("output not written: %v", err)
	}
	if lines := strings.Split(strings.TrimSpace(string(data)), "\n"); len(lines) != batches {
		t.Errorf("got %d samples, want %d", len(lines), batches)
	}
	if want := fmt.Sprintf("wrote %d sample(s)", batches); !strings.Contains(stderr.String(), want) {
		t.Errorf("stderr = %q, want it to contain %q", stderr.String(), want)
	}
}

func TestOtelServeFlushWithZeroSamplesExitsOneWithoutWriting(t *testing.T) {
	_, rcv, _ := startOtelServer(t)
	path := filepath.Join(t.TempDir(), "out.jsonl")
	var stdout, stderr bytes.Buffer
	if code := rcv.flush(path, &stdout, &stderr); code != 1 {
		t.Fatalf("flush exit code = %d, want 1", code)
	}
	if !strings.Contains(stderr.String(), "no valid samples") {
		t.Errorf("stderr = %q, want a no-valid-samples diagnostic", stderr.String())
	}
	if _, err := os.Stat(path); !os.IsNotExist(err) {
		t.Errorf("output file exists, want no write on zero samples")
	}
}

func TestOtelServeFlushWriteFailureExitsOne(t *testing.T) {
	srv, rcv, _ := startOtelServer(t)
	postTraces(t, srv.URL, "application/json", []byte(fixtureFirstLine(t)))
	path := filepath.Join(t.TempDir(), "missing-dir", "out.jsonl")
	var stdout, stderr bytes.Buffer
	if code := rcv.flush(path, &stdout, &stderr); code != 1 {
		t.Fatalf("flush exit code = %d, want 1 (stderr: %q)", code, stderr.String())
	}
	if stderr.Len() == 0 {
		t.Error("stderr is empty, want a write-failure error")
	}
}

func TestOtelServeRequiresOutputFlag(t *testing.T) {
	code, _, stderr := runOtel(t, "serve")
	if code != 1 {
		t.Fatalf("exit code = %d, want 1 (stderr: %q)", code, stderr)
	}
	if !strings.Contains(stderr, "-o") || !strings.Contains(stderr, "usage") {
		t.Errorf("stderr = %q, want -o requirement and usage text", stderr)
	}
}

func TestOtelServeUnlistenableAddrExitsOne(t *testing.T) {
	path := filepath.Join(t.TempDir(), "out.jsonl")
	code, _, stderr := runOtel(t, "serve", "--addr", "localhost:notaport", "-o", path)
	if code != 1 {
		t.Fatalf("exit code = %d, want 1 (stderr: %q)", code, stderr)
	}
	if stderr == "" {
		t.Error("stderr is empty, want a listen error")
	}
}

// --- /v1/logs ingestion + gzip (R10, cost join) ---

const (
	logJoinTraceID = "0102030405060708090a0b0c0d0e0f10"
	logJoinSpanID  = "0102030405060708"
)

// tokenSpanTraceBody is one OTLP/JSON trace export with a single token-bearing
// span keyed on logJoinTraceID/logJoinSpanID.
func tokenSpanTraceBody() string {
	return `{"resourceSpans":[{"resource":{"attributes":[{"key":"service.name","value":{"stringValue":"claude-code"}}]},` +
		`"scopeSpans":[{"spans":[{"traceId":"` + logJoinTraceID + `","spanId":"` + logJoinSpanID + `",` +
		`"name":"claude_code.llm_request","startTimeUnixNano":"1700000000000000000","endTimeUnixNano":"1700000001000000000",` +
		`"attributes":[{"key":"input_tokens","value":{"intValue":"100"}}]}]}]}]}`
}

// costLogBody is one OTLP/JSON logs export whose record's trace context matches
// tokenSpanTraceBody and carries cost_usd 0.041230 (→ 41230 micro-USD).
func costLogBody() string {
	return `{"resourceLogs":[{"resource":{"attributes":[{"key":"service.name","value":{"stringValue":"claude-code"}}]},` +
		`"scopeLogs":[{"logRecords":[{"traceId":"` + logJoinTraceID + `","spanId":"` + logJoinSpanID + `",` +
		`"eventName":"claude_code.api_request","timeUnixNano":"1700000000500000000",` +
		`"attributes":[{"key":"cost_usd","value":{"doubleValue":0.041230}}]}]}]}]}`
}

func postTo(t *testing.T, baseURL, path, contentType string, body []byte) *http.Response {
	t.Helper()
	resp, err := http.Post(baseURL+path, contentType, bytes.NewReader(body))
	if err != nil {
		t.Fatalf("POST %s: %v", path, err)
	}
	t.Cleanup(func() { resp.Body.Close() })
	return resp
}

// flushToSamples flushes the receiver to a temp JSONL file and returns the
// decoded sample values, one map per line.
func flushToSamples(t *testing.T, rcv *otelReceiver) []map[string]int64 {
	t.Helper()
	path := filepath.Join(t.TempDir(), "out.jsonl")
	var stdout, stderr bytes.Buffer
	if code := rcv.flush(path, &stdout, &stderr); code != 0 {
		t.Fatalf("flush exit code = %d, want 0 (stderr: %q)", code, stderr.String())
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("output not written: %v", err)
	}
	var out []map[string]int64
	for _, line := range strings.Split(strings.TrimSpace(string(data)), "\n") {
		var s struct {
			Values map[string]int64 `json:"values"`
		}
		if err := json.Unmarshal([]byte(line), &s); err != nil {
			t.Fatalf("sample line is not JSON: %v (%q)", err, line)
		}
		out = append(out, s.Values)
	}
	return out
}

func TestOtelServePostV1LogsJSONJoinsCostAtFlush(t *testing.T) {
	srv, rcv, _ := startOtelServer(t)
	postTraces(t, srv.URL, "application/json", []byte(tokenSpanTraceBody()))
	resp := postTo(t, srv.URL, "/v1/logs", "application/json", []byte(costLogBody()))
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("POST /v1/logs status = %d, want 200", resp.StatusCode)
	}
	samples := flushToSamples(t, rcv)
	if len(samples) != 1 {
		t.Fatalf("got %d samples, want 1", len(samples))
	}
	if samples[0]["cost_microusd"] != 41230 {
		t.Errorf("cost_microusd = %d, want 41230", samples[0]["cost_microusd"])
	}
	if samples[0]["input_tokens"] != 100 {
		t.Errorf("input_tokens = %d, want 100 (span tokens retained)", samples[0]["input_tokens"])
	}
}

func TestOtelServePostV1LogsProtobufDecodes(t *testing.T) {
	srv, rcv, _ := startOtelServer(t)
	postTraces(t, srv.URL, "application/json", []byte(tokenSpanTraceBody()))
	ld := &logsv1.LogsData{
		ResourceLogs: []*logsv1.ResourceLogs{{
			ScopeLogs: []*logsv1.ScopeLogs{{
				LogRecords: []*logsv1.LogRecord{{
					TraceId:      []byte{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16},
					SpanId:       []byte{1, 2, 3, 4, 5, 6, 7, 8},
					EventName:    "claude_code.api_request",
					TimeUnixNano: 1700000000500000000,
					Attributes: []*commonv1.KeyValue{{
						Key:   "cost_usd",
						Value: &commonv1.AnyValue{Value: &commonv1.AnyValue_DoubleValue{DoubleValue: 0.041230}},
					}},
				}},
			}},
		}},
	}
	raw, err := proto.Marshal(ld)
	if err != nil {
		t.Fatalf("proto.Marshal: %v", err)
	}
	resp := postTo(t, srv.URL, "/v1/logs", "application/x-protobuf", raw)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("POST /v1/logs status = %d, want 200", resp.StatusCode)
	}
	samples := flushToSamples(t, rcv)
	if len(samples) != 1 || samples[0]["cost_microusd"] != 41230 {
		t.Errorf("samples = %v, want one with cost_microusd 41230", samples)
	}
}

func TestOtelServeLogsLogsAcceptedRecordCount(t *testing.T) {
	srv, _, logs := startOtelServer(t)
	postTo(t, srv.URL, "/v1/logs", "application/json", []byte(costLogBody()))
	if want := "accepted 1 log record"; !strings.Contains(logs.String(), want) {
		t.Errorf("logs = %q, want them to contain %q", logs.String(), want)
	}
}

func gzipBytes(t *testing.T, data []byte) []byte {
	t.Helper()
	var buf bytes.Buffer
	gz := gzip.NewWriter(&buf)
	if _, err := gz.Write(data); err != nil {
		t.Fatalf("gzip write: %v", err)
	}
	if err := gz.Close(); err != nil {
		t.Fatalf("gzip close: %v", err)
	}
	return buf.Bytes()
}

func postGzip(t *testing.T, baseURL, path, contentType string, data []byte) *http.Response {
	t.Helper()
	req, err := http.NewRequest(http.MethodPost, baseURL+path, bytes.NewReader(gzipBytes(t, data)))
	if err != nil {
		t.Fatalf("NewRequest: %v", err)
	}
	req.Header.Set("Content-Type", contentType)
	req.Header.Set("Content-Encoding", "gzip")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("POST %s (gzip): %v", path, err)
	}
	t.Cleanup(func() { resp.Body.Close() })
	return resp
}

func TestOtelServeGzipEncodedTracesBodyDecodes(t *testing.T) {
	srv, rcv, _ := startOtelServer(t)
	resp := postGzip(t, srv.URL, "/v1/traces", "application/json", []byte(tokenSpanTraceBody()))
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("gzip POST /v1/traces status = %d, want 200", resp.StatusCode)
	}
	samples := flushToSamples(t, rcv)
	if len(samples) != 1 || samples[0]["input_tokens"] != 100 {
		t.Errorf("samples = %v, want one with input_tokens 100", samples)
	}
}

func TestOtelServeGzipEncodedLogsBodyDecodes(t *testing.T) {
	srv, rcv, _ := startOtelServer(t)
	postTraces(t, srv.URL, "application/json", []byte(tokenSpanTraceBody()))
	resp := postGzip(t, srv.URL, "/v1/logs", "application/json", []byte(costLogBody()))
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("gzip POST /v1/logs status = %d, want 200", resp.StatusCode)
	}
	samples := flushToSamples(t, rcv)
	if len(samples) != 1 || samples[0]["cost_microusd"] != 41230 {
		t.Errorf("samples = %v, want one with cost_microusd 41230", samples)
	}
}

func TestOtelServeGzipUndecodableBodyReturns400(t *testing.T) {
	srv, _, _ := startOtelServer(t)
	req, err := http.NewRequest(http.MethodPost, srv.URL+"/v1/traces", bytes.NewReader([]byte("not gzip at all")))
	if err != nil {
		t.Fatalf("NewRequest: %v", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Content-Encoding", "gzip")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("POST: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusBadRequest {
		t.Errorf("status = %d, want 400 (undecodable gzip)", resp.StatusCode)
	}
}

// --- File mode: mixed trace + logs export objects ---

func TestCmdOtelFileModeAcceptsLogsExportObject(t *testing.T) {
	// A JSONL file mixing a trace-export object and a cost logs-export object
	// (as an OTel Collector fileexporter would write) joins the cost at flush.
	path := filepath.Join(t.TempDir(), "mixed.jsonl")
	body := tokenSpanTraceBody() + "\n" + costLogBody() + "\n"
	if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
	code, stdout, stderr := runOtel(t, path)
	if code != 0 {
		t.Fatalf("exit code = %d, want 0 (stderr: %q)", code, stderr)
	}
	lines := strings.Split(strings.TrimSpace(stdout), "\n")
	if len(lines) != 1 {
		t.Fatalf("got %d samples, want 1 (stdout: %q)", len(lines), stdout)
	}
	var s struct {
		Values map[string]int64 `json:"values"`
	}
	if err := json.Unmarshal([]byte(lines[0]), &s); err != nil {
		t.Fatalf("sample not JSON: %v", err)
	}
	if s.Values["cost_microusd"] != 41230 {
		t.Errorf("cost_microusd = %d, want 41230", s.Values["cost_microusd"])
	}
	if strings.Contains(stderr, "invalid") {
		t.Errorf("stderr = %q, want no invalid-line report for a valid logs object", stderr)
	}
}
