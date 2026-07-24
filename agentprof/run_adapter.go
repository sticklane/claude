package main

import (
	"flag"
	"fmt"
	"io"
	"os"

	"github.com/sticklane/agentprof/internal/output"
	"github.com/sticklane/agentprof/internal/schema"
)

// oFlagUsage is the shared description for the -o output flag across the
// sample-emitting subcommands (the default-stdout variant). `otel serve`
// uses its own "-o required" variant.
const oFlagUsage = "output path: .pb.gz writes a pprof profile, anything else JSONL (default stdout)"

// singleFileCmd builds the shared head of the single-input-file subcommands
// (gcp, vertex, otel): a ContinueOnError FlagSet writing to stderr with the
// shared -o flag, any extra flags registered by extra, then parsePositionals
// enforcing exactly one input file. noun names the input in the diagnostic
// ("billing export file"); usage is the one-line usage string printed on a
// count mismatch. On a usage error it reports to stderr and returns ok=false
// with the process exit code; otherwise it returns the -o value and the single
// input path. It is the head companion to runFileAdapter's shared tail.
func singleFileCmd(
	name, noun, usage string,
	args []string,
	stderr io.Writer,
	extra func(fs *flag.FlagSet),
) (out *string, input string, code int, ok bool) {
	fs := flag.NewFlagSet(name, flag.ContinueOnError)
	fs.SetOutput(stderr)
	out = fs.String("o", "", oFlagUsage)
	if extra != nil {
		extra(fs)
	}
	inputs, parsed := parsePositionals(fs, args)
	if !parsed {
		return nil, "", 2, false
	}
	if len(inputs) != 1 {
		fmt.Fprintf(stderr, "agentprof %s: expected exactly one %s\nusage: %s\n", name, noun, usage)
		return nil, "", 2, false
	}
	return out, inputs[0], 0, true
}

// runFileAdapter is the shared tail of the gcp and vertex subcommands: it
// opens input, runs parse over it, reports skipped rows and errors, guards
// against an empty result, and writes the samples. name ("gcp" / "vertex")
// prefixes the diagnostic messages. otel deliberately does not use this
// helper (see specs/archive/adapter-file-runner/SPEC.md).
func runFileAdapter(
	name string,
	input string,
	parse func(io.Reader) ([]schema.Sample, int, error),
	out *string,
	stdout, stderr io.Writer,
) int {
	f, err := os.Open(input)
	if err != nil {
		fmt.Fprintf(stderr, "agentprof %s: %v\n", name, err)
		return 1
	}
	samples, skipped, err := parse(f)
	f.Close()
	if err != nil {
		fmt.Fprintf(stderr, "agentprof %s: reading %s: %v\n", name, input, err)
		return 1
	}

	if skipped > 0 {
		fmt.Fprintf(stderr, "skipped %d rows\n", skipped)
	}
	if len(samples) == 0 {
		fmt.Fprintf(stderr, "agentprof %s: no valid rows in input\n", name)
		return 1
	}
	if err := output.Write(samples, *out, stdout); err != nil {
		fmt.Fprintf(stderr, "agentprof %s: %v\n", name, err)
		return 1
	}
	return 0
}
