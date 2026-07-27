# Queue re-triage against the agentic core redesign

The original markdown queue snapshot is superseded. Beads is the canonical
authority for live task status and dependencies, and
`agentic register-spec` creates only missing definitions and edges.

The Codebase-Memory hard cutover retired the former in-repository
code-exploration implementation and its pending task families rather than
carrying their historical status rows forward here. Query `bd ready`,
`bd list`, and `bd show <id>` for the current queue.
