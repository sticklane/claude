# Surface inventory fragments

`../BASELINE.json` records the toolkit surface at the start of the
toolkit-core-simplification work. Set `git_blob_pin` to `1` in each manifest.
Git history pins the baseline and each fragment to its first committed blob
with schema version 2 and that pin. The checker also reads the history of
fragment paths, so deleting a fragment doesn't erase its classifications.
Validation fails in a shallow clone because the first pinned blob might be
outside the available history. Deepen the clone before validating.

When a change adds a skill, agent, rule, hook, workflow, command-line command,
runtime profile, or canonical test, add a JSON fragment in this directory. Use
a filename that no other task uses, and set `fragment` to the filename without
`.json`. The checker rejects duplicate fragment names and duplicate surface
identities. Set `frozen_sha256` to the Secure Hash Algorithm 256-bit digest of
the canonical JSON object without that field. This digest validates a new file
before its first commit and validates scratch fixtures that don't use Git.

Each surface records its repository-relative path and Secure Hash Algorithm
256-bit content hash, known dependents, disposition, rationale, replacement,
and behavioral test pointers. Only `retain` pins the recorded content.
`repair`, `hide-stub`, and `measure-before-decision` permit content changes
but not removal or relocation. Only `retire-dead` permits the recorded surface
to disappear.

Both `retain` and `repair` require a classified behavioral test with a named
case. Use `tests/test_name.py::test_case_name` for a Python test or
`tests/test_name.sh#assert:<sha256>` for a shell test. For Python, the checker
examines only the named test function. For shell, the hash identifies one
normalized executable assertion statement. The checker ignores comments,
joins line continuations, and resolves simple file variables before hashing.
The selected function or statement must reference the surface path or
identity. Use `measure-before-decision`, with no evidence pointer, when no such
behavioral test exists.

Validate the baseline and all fragments from the repository root:

```sh
python3 scripts/inventory-core-surface.py \
  --check specs/toolkit-core-simplification/BASELINE.json
```
