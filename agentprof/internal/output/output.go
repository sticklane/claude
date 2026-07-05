// Package output dispatches canonical samples to their destination based on
// the -o path shared by build and the adapters (SPEC R4): a path ending
// .pb.gz gets a gzipped pprof profile, anything else (or stdout) gets JSONL.
package output

import (
	"bufio"
	"errors"
	"io"
	"os"
	"strings"

	"github.com/sticklane/agentprof/internal/pprofenc"
	"github.com/sticklane/agentprof/internal/schema"
)

// Write sends samples to path: ".pb.gz" suffix → pprof profile file, empty or
// "-" → JSONL on stdout, any other path → JSONL file. With zero samples it
// returns an error and writes nothing (callers report it and exit 1).
func Write(samples []schema.Sample, path string, stdout io.Writer) error {
	if len(samples) == 0 {
		return errors.New("no samples to write")
	}
	if strings.HasSuffix(path, ".pb.gz") {
		return writeProfile(samples, path)
	}
	if path == "" || path == "-" {
		return writeJSONL(stdout, samples)
	}
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	if err := writeJSONL(f, samples); err != nil {
		f.Close()
		return err
	}
	return f.Close()
}

func writeProfile(samples []schema.Sample, path string) error {
	prof, err := pprofenc.Build(samples)
	if err != nil {
		return err
	}
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	if err := prof.Write(f); err != nil {
		f.Close()
		return err
	}
	return f.Close()
}

func writeJSONL(w io.Writer, samples []schema.Sample) error {
	bw := bufio.NewWriter(w)
	for _, s := range samples {
		line, err := schema.MarshalLine(s)
		if err != nil {
			return err
		}
		if _, err := bw.Write(line); err != nil {
			return err
		}
		if err := bw.WriteByte('\n'); err != nil {
			return err
		}
	}
	return bw.Flush()
}
