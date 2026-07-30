# Now

Only a human edits this file. Order is priority: the first entry with ready
work is what a bare `/drain` focuses on, and work in progress is one focus at
a time. An entry is a list line naming a spec slug under `specs/`, with an
optional one-line why after an em dash. EVERY list line in this file must be
such an entry: the selector (`bin/now-focus`) reads any `-` or `*` bullet as
an entry and exits 2 on one that is not a slug, so prose here never uses
bullets. Non-list content — headings, paragraphs, comments, blanks — is
ignored by the selector.

An empty list is a legal state. Drain says so and stops; it never invents a
focus. Reach for `/drain --all` to work the whole queue, or `/drain
specs/<slug>` to name one focus explicitly.

Completed slugs leave this list, and `specs/QUEUE.md` keeps the historical
record.

- drain-economy — make the queue a finish line: focus, economy, ceremony
