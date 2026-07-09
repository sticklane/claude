# Task 08: Document pprof -top node-fraction pruning of small tool: frames

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: none
Priority: P3
Budget: 2 turns
Spec: ../SPEC.md
Discovered-from: specs/agentprof-instrumentation/tasks/04-e2e-duration-evidence.md
Touch: agentprof/README.md

## Goal

`agentprof/README.md` warns that `go tool pprof -top`'s default
node-fraction pruning hides small `tool:` frames on day-scale profiles —
`-nodefraction=0 -edgefraction=0` (or a narrower `--days`/project
filter) is needed to see them — placed near the existing plain `-top`
invocation examples so a human doesn't conclude the feature is broken.

## Steps

1. Add the one-paragraph note adjacent to the `-top` examples.

## Acceptance

- [ ] `grep -qi 'nodefraction' agentprof/README.md` → match
- [ ] `grep -i 'nodefraction' agentprof/README.md | grep -q 'tool:'` → match (ties pruning to tool: frames)
- [ ] `cd agentprof && bash scripts/check.sh` → exit 0
