# Task 01: /prose-review skill + doctrine (rubric, Diátaxis, reader test)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
Depends on: none
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirements R1-R6)
Touch: .claude/skills/prose-review/, CLAUDE.md

## Goal

`.claude/skills/prose-review/SKILL.md` + `reference.md` exist per SPEC
R1-R6: reference.md carries the nine-item cited rubric (item-1 carve-out
included, DeepMind noted as contributing nothing), the Diátaxis quadrant
table bound to house doc locations (with the "what does the reader need
RIGHT NOW" selector), the Google-style essentials Vale can't check, and
the distilled reader-test procedure ("stumble" report from one
fresh-context agent). SKILL.md: review mode default (Vale pass first when
available, rubric pass, reader test for orientation docs), --fix
human-typed only, description with both review and authoring trigger
phrases. CLAUDE.md gains the one-line pointer. Vale INVOCATION is a
soft dependency: reference the `vale` command; task 02 ships the
installer (skill must degrade gracefully when vale absent, per R2).

## Acceptance

- [ ] `grep -qi 'DeepMind' .claude/skills/prose-review/reference.md && grep -qi 'right now' .claude/skills/prose-review/reference.md && grep -qi 'stumble' .claude/skills/prose-review/reference.md` → all hit
- [ ] `grep -c 'developers.google.com/style\|diataxis.fr' .claude/skills/prose-review/reference.md` ≥ 2
- [ ] `grep -q 'prose-review' CLAUDE.md` → hit (0 today, verified)
- [ ] `wc -l < .claude/skills/prose-review/SKILL.md` → < 500
- [ ] MANUAL: nine items with vendor quotes; --fix rules per R3/R4; reader-test skips diffs/pasted text
