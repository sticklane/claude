# slack-relay — Orientation

Notifies Slack of `/drain` DEFERRED questions and lets a threaded reply
answer them, resuming the queue with no one at a keyboard. A one-shot
poller run periodically by launchd — not a persistent server, unlike
`agent-console/` (whose zero-pip-dependency invariant this tool
deliberately does NOT share: it needs `requests`/`PyYAML`, hence its own
directory rather than living inside `agent-console/`).

## Map

- `slack_relay.py` — everything: scans repos for deferred questions (reuses
  `.claude/skills/workboard/workboard.py`'s `scan_toolkit_specs()` by
  path-import), posts new ones to Slack, polls open threads for an eligible
  reply, writes the answer back with a compare-and-swap Status check, and
  relaunches a headless `/drain` unless a live one already owns the spec.
- `slack_relay_config.example.yaml` — copy to `slack_relay_config.yaml`
  (gitignored) and fill in. The Slack bot token is never in this file — it
  lives only in macOS Keychain (`security add-generic-password -s
  slack-relay -a bot-token -w <token>`).
- `launchd/slack-relay.plist.tmpl` — service template; `install.sh` renders
  it with this machine's paths (nothing user-specific committed).
- `tests/test_slack_relay.py` — pure-function tests (diffing, reply
  eligibility, CAS write, owner-lease liveness); no real network/Slack.

## Commands

```bash
python3 -m unittest discover -s tests   # unit tests
python3 slack_relay.py --config slack_relay_config.yaml   # one manual pass
./install.sh                            # render + load the launchd service
```

## State

Reuses, never reimplements: `/drain`'s `Status:` semantics (`deferred` →
`pending`), its `## Deferred questions` / `## Answers` file format, its
`DRAIN-OWNER.md` liveness concept (simplified here to an advisory mtime
check — the real safety is `/drain`'s own compare-and-swap owner claim,
which harmlessly refuses a redundant relaunch), and its documented headless
relaunch command template (all in `.claude/skills/drain/reference.md`).
