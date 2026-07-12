// agentprof emits pprof profiles for AI-agent token and spend attribution.
package main

import (
	"flag"
	"fmt"
	"io"
	"os"
)

const version = "0.1.0"

func main() {
	os.Exit(run(os.Args[1:], os.Stdout, os.Stderr))
}

func run(args []string, stdout, stderr io.Writer) int {
	if len(args) == 0 {
		usage(stderr)
		return 2
	}
	switch args[0] {
	case "--version", "-version", "version":
		fmt.Fprintf(stdout, "agentprof %s\n", version)
		return 0
	case "claude":
		return cmdClaude(args[1:], stdout, stderr)
	case "gcp":
		return cmdGCP(args[1:], stdout, stderr)
	case "vertex":
		return cmdVertex(args[1:], stdout, stderr)
	case "otel":
		return cmdOtel(args[1:], stdout, stderr)
	case "antigravity":
		return cmdAntigravity(args[1:], stdout, stderr)
	case "build":
		return cmdBuild(args[1:], stdout, stderr)
	default:
		fmt.Fprintf(stderr, "agentprof: unknown subcommand %q\n", args[0])
		usage(stderr)
		return 2
	}
}

// parsePositionals parses fs against args, re-parsing after each positional
// so flags may follow the input files (e.g. `agentprof gcp billing.json -o
// out.pb.gz`). ok is false when flag parsing failed (fs has already reported
// the error to its output).
func parsePositionals(fs *flag.FlagSet, args []string) (inputs []string, ok bool) {
	for {
		if err := fs.Parse(args); err != nil {
			return nil, false
		}
		args = fs.Args()
		if len(args) == 0 {
			return inputs, true
		}
		inputs = append(inputs, args[0])
		args = args[1:]
	}
}

func usage(w io.Writer) {
	fmt.Fprint(w, `usage: agentprof <subcommand> [flags]

Subcommands:
  claude   emit canonical samples from Claude Code transcripts
  gcp      emit canonical samples from a GCP billing export file
  vertex   emit canonical samples from a Vertex AI request-response logging export
  otel     emit canonical samples from an OTLP/JSON trace export
  antigravity  emit canonical samples from Antigravity CLI conversation databases
  build    convert canonical sample JSONL into a pprof profile

Flags:
  --version   print version and exit
`)
}
