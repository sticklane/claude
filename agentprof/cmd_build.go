package main

import (
	"flag"
	"fmt"
	"io"
	"os"

	"github.com/sticklane/agentprof/internal/output"
	"github.com/sticklane/agentprof/internal/schema"
)

// cmdBuild converts canonical sample JSONL files into a pprof profile (R2).
func cmdBuild(args []string, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("build", flag.ContinueOnError)
	fs.SetOutput(stderr)
	out := fs.String("o", "", "output path: .pb.gz writes a pprof profile, anything else JSONL (default stdout)")
	inputs, ok := parsePositionals(fs, args)
	if !ok {
		return 2
	}
	if len(inputs) == 0 {
		fmt.Fprintln(stderr, "agentprof build: no input files\nusage: agentprof build <samples.jsonl>... [-o out]")
		return 2
	}

	var samples []schema.Sample
	skipped := 0
	for _, path := range inputs {
		f, err := os.Open(path)
		if err != nil {
			fmt.Fprintf(stderr, "agentprof build: %v\n", err)
			return 1
		}
		s, n, err := schema.Read(f)
		f.Close()
		if err != nil {
			fmt.Fprintf(stderr, "agentprof build: reading %s: %v\n", path, err)
			return 1
		}
		samples = append(samples, s...)
		skipped += n
	}

	if skipped > 0 {
		fmt.Fprintf(stderr, "skipped %d invalid lines\n", skipped)
	}
	if len(samples) == 0 {
		fmt.Fprintln(stderr, "agentprof build: no valid samples in input")
		return 1
	}
	if err := output.Write(samples, *out, stdout); err != nil {
		fmt.Fprintf(stderr, "agentprof build: %v\n", err)
		return 1
	}
	return 0
}
