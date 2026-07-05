package main

import (
	"bytes"
	"context"
	"flag"
	"fmt"
	"io"
	"mime"
	"net"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/sticklane/agentprof/internal/otel"
	"github.com/sticklane/agentprof/internal/output"
)

// cmdOtel emits canonical samples from an OTLP/JSON trace export file: a
// single trace-export object, or JSONL of such objects as written by the
// OTel Collector file exporter (R1, R2). `otel serve` instead runs a live
// OTLP/HTTP receiver (R8–R10).
func cmdOtel(args []string, stdout, stderr io.Writer) int {
	if len(args) > 0 && args[0] == "serve" {
		return cmdOtelServe(args[1:], stdout, stderr)
	}
	fs := flag.NewFlagSet("otel", flag.ContinueOnError)
	fs.SetOutput(stderr)
	out := fs.String("o", "", "output path: .pb.gz writes a pprof profile, anything else JSONL (default stdout)")
	inputs, ok := parsePositionals(fs, args)
	if !ok {
		return 2
	}
	if len(inputs) != 1 {
		fmt.Fprintln(stderr, "agentprof otel: expected exactly one OTLP trace file\nusage: agentprof otel <trace.json> [-o out]")
		return 2
	}

	data, err := os.ReadFile(inputs[0])
	if err != nil {
		fmt.Fprintf(stderr, "agentprof otel: %v\n", err)
		return 1
	}

	acc := otel.NewAccumulator()
	badLines := 0
	// A leading '{' is first tried as one whole-file object; on failure the
	// accumulator is untouched, so fall back to line-by-line JSONL (R2).
	whole := bytes.TrimSpace(data)
	if len(whole) == 0 || whole[0] != '{' || acc.AddJSON(whole) != nil {
		for _, line := range bytes.Split(data, []byte("\n")) {
			if line = bytes.TrimSpace(line); len(line) == 0 {
				continue
			}
			if acc.AddJSON(line) != nil {
				badLines++
			}
		}
	}
	samples, badSpans := acc.Flush()

	var parts []string
	if badLines > 0 {
		parts = append(parts, fmt.Sprintf("%d invalid line(s)", badLines))
	}
	if badSpans > 0 {
		parts = append(parts, fmt.Sprintf("%d invalid span(s)", badSpans))
	}
	if len(parts) > 0 {
		fmt.Fprintf(stderr, "skipped %s\n", strings.Join(parts, ", "))
	}
	if len(samples) == 0 {
		fmt.Fprintln(stderr, "agentprof otel: no valid samples in input")
		return 1
	}
	if err := output.Write(samples, *out, stdout); err != nil {
		fmt.Fprintf(stderr, "agentprof otel: %v\n", err)
		return 1
	}
	return 0
}

// cmdOtelServe runs an OTLP/HTTP receiver until SIGINT/SIGTERM, then drains
// in-flight requests, flushes the accumulated spans through output.Write,
// and reports counts to stderr (R8, R9).
func cmdOtelServe(args []string, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("otel serve", flag.ContinueOnError)
	fs.SetOutput(stderr)
	addr := fs.String("addr", "localhost:4318", "listen address for the OTLP/HTTP receiver")
	out := fs.String("o", "", "output path: .pb.gz writes a pprof profile, anything else JSONL (required)")
	if err := fs.Parse(args); err != nil {
		return 2
	}
	if *out == "" {
		fmt.Fprintln(stderr, "agentprof otel serve: -o is required\nusage: agentprof otel serve [--addr localhost:4318] -o <out>")
		return 1
	}

	rcv := newOtelReceiver(stderr)
	ln, err := net.Listen("tcp", *addr)
	if err != nil {
		fmt.Fprintf(stderr, "agentprof otel serve: %v\n", err)
		return 1
	}
	srv := &http.Server{Handler: rcv}
	serveErr := make(chan error, 1)
	go func() { serveErr <- srv.Serve(ln) }()

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	defer signal.Stop(sig)
	select {
	case <-sig:
	case err := <-serveErr:
		fmt.Fprintf(stderr, "agentprof otel serve: %v\n", err)
		return 1
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		fmt.Fprintf(stderr, "agentprof otel serve: shutdown: %v\n", err)
	}
	return rcv.flush(*out, stdout, stderr)
}

// otelReceiver is the OTLP/HTTP trace receiver: handlers run concurrently,
// so span accumulation and batch logging are mutex-guarded (R8).
type otelReceiver struct {
	mu   sync.Mutex
	acc  *otel.Accumulator
	logw io.Writer
}

func newOtelReceiver(logw io.Writer) *otelReceiver {
	return &otelReceiver{acc: otel.NewAccumulator(), logw: logw}
}

func (r *otelReceiver) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	if req.URL.Path != "/v1/traces" {
		http.NotFound(w, req) // includes /v1/metrics and /v1/logs (R10)
		return
	}
	if req.Method != http.MethodPost {
		w.Header().Set("Allow", http.MethodPost)
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	ct, _, _ := mime.ParseMediaType(req.Header.Get("Content-Type"))
	if ct != "application/json" && ct != "application/x-protobuf" {
		http.Error(w, "unsupported content type", http.StatusUnsupportedMediaType)
		return
	}
	body, err := io.ReadAll(req.Body)
	if err != nil {
		http.Error(w, "cannot read request body", http.StatusBadRequest)
		return
	}

	r.mu.Lock()
	before := r.acc.Len()
	if ct == "application/json" {
		err = r.acc.AddJSON(body)
	} else {
		err = r.acc.AddProto(body)
	}
	if err == nil {
		fmt.Fprintf(r.logw, "accepted %d spans\n", r.acc.Len()-before)
	}
	r.mu.Unlock()
	if err != nil {
		http.Error(w, "cannot decode request body", http.StatusBadRequest)
		return
	}

	// An ExportTraceServiceResponse with no partial success is `{}` in JSON
	// and a zero-length protobuf message; neither needs the collector
	// package (R8, R11).
	w.Header().Set("Content-Type", ct)
	if ct == "application/json" {
		w.Write([]byte("{}"))
	}
}

// flush resolves parent chains across all received batches, writes the
// result to out, and returns the process exit code (R9).
func (r *otelReceiver) flush(out string, stdout, stderr io.Writer) int {
	r.mu.Lock()
	samples, skipped := r.acc.Flush()
	r.mu.Unlock()
	if len(samples) == 0 {
		fmt.Fprintln(stderr, "agentprof otel serve: no valid samples received")
		return 1
	}
	if err := output.Write(samples, out, stdout); err != nil {
		fmt.Fprintf(stderr, "agentprof otel serve: %v\n", err)
		return 1
	}
	fmt.Fprintf(stderr, "wrote %d sample(s), skipped %d invalid span(s)\n", len(samples), skipped)
	return 0
}
