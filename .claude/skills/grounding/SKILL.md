---
name: grounding
description: |
  Claims-and-evidence discipline plus banned AI-register patterns for prose.
  Every world-state claim needs checkable backing — material from the
  conversation, a named source, or a tool result — or it gets cut, downgraded
  to explicit opinion, or queried. Replaces abstraction with concrete
  specifics. Bans negative parallelism ("it's not X, it's Y"), word salad
  (stacked abstractions), sycophancy ("great question", unearned praise),
  assistant-voice leakage ("I hope this helps", "let me know if..."),
  meta-discourse and signposting, importance inflation, and formulaic
  wrap-ups. Use alongside any drafting or editing of prose that asserts
  facts: posts, papers, proposals, reports, briefs, emails. Trigger phrases -
  "ground this", "check the claims", "is this backed", "cite or cut",
  "audit the claims in this draft". NOT a style/voice
  pass (use humanizer) and NOT the full generation constraint set (use
  anti-ai-slop-writing); this skill governs what may be claimed, how claims
  are backed, and which registers are off-limits.
---

# Grounding

Prose earns trust through checkable claims made in an authored voice. This
skill governs what a draft may assert, what backing each assertion needs,
and which AI-register patterns are banned outright. It composes with the
style skills: apply it with anti-ai-slop-writing while drafting, with
humanizer while editing. Pure style tells (em dash habits, rule of three,
AI vocabulary) stay humanizer's job; this skill covers claims and register.
It applies to prose that makes claims about the world; it has nothing to
say about code.

## Rule 1 — Evidence before claims

Every claim about the world must trace to something the reader can check:

- material provided in the conversation,
- a named, findable source (a study, a document, a person on the record),
- a measurement or tool result from this session.

When a claim has none of these, do one of three things: cut it, rewrite it
as explicitly someone's opinion ("I think...", "Steven's position is..."),
or ask for the source. Never fill the gap with a plausible generality.

Smells that mark an ungrounded world-state claim:

- "studies show", "research suggests", "experts agree" — with no named
  study or expert
- statistics without a source ("70% of teams...")
- trend claims: "increasingly", "more and more", "in today's fast-paced
  world"
- audience mind-reading: "users expect", "readers want", "everyone knows"

## Rule 2 — Concrete over abstract

Prefer the specific noun: a name, a number, a date, a file, a worked
example. A sentence built from stacked abstractions ("leveraging robust
capabilities to drive transformative outcomes across the ecosystem") is
word salad — it survives having its nouns swapped with another industry's
nouns, which means it says nothing. Rebuild the sentence around one concrete
fact, or delete it.

Test per sentence: what would be different in the world if this sentence
were false? If the answer is nothing, the sentence is filler.

## Rule 3 — Banned patterns

- **Negative parallelism.** "It's not X, it's Y", "not just X but Y", "more
  than just X", "This isn't about X; it's about Y." In generated text the
  two clauses almost always restate one idea, with the second wearing
  weightier words, so the reader gains no information — the sentence
  performs depth. State Y directly and attach its evidence. Analyses of
  large chat datasets report this tic at roughly three times the human rate,
  persisting across model generations (see Sources).
- **Sycophancy.** Flattering the reader or the subject instead of informing:
  "Great question", "You're absolutely right", "What a fascinating topic",
  and subject-puffery ("visionary", "renowned", "beloved"). Praise is a
  claim like any other — unearned unless the evidence for it is on the
  page. Sycophancy is a trained model bias, not a judgment: a 2025 Science
  study found chatbots endorse users' views about 49% more often than
  humans do (see Sources). If the subject really is exceptional, show the
  fact that proves it and drop the adjective.
- **Assistant-voice leakage.** Chat-register artifacts inside a deliverable:
  "Certainly!", "I hope this helps", "I'd be happy to...", "Feel free
  to...", "Let me know if you'd like...", closing menus of offered
  follow-ups, or addressing the reader as if they had just typed a request.
  A document is not a chat turn — delete the conversational frame and keep
  the content.
- **Meta-discourse and signposting.** Writing about the writing: "In this
  section we will...", "It's important to note that...", "It's worth
  noting...", "Let's dive into...", "As mentioned above...". Also
  knowledge-gap disclaimers that narrate what the author doesn't know
  ("While specific figures are unavailable..."). Delete it; the content
  carries its own weight or it doesn't.
- **Importance inflation.** "Crucial", "vital", "essential",
  "game-changing", "stands as a testament", "marks a pivotal moment",
  "plays a significant role" — significance asserted by adjective rather
  than argued. Show importance through consequences; delete the label.
- **Formulaic wrap-ups.** "In conclusion...", "Ultimately...", "Despite
  these challenges, X continues to...", recap paragraphs that restate
  without adding, and superficial "-ing" tails that bolt an unargued
  significance claim onto a fact ("...highlighting the importance of...",
  "...underscoring its role as..."). End on the last load-bearing fact
  instead.

## Rule 4 — Structure and reference

- **Actions lead.** In instructional prose (a handoff, a status message, a
  how-to paragraph), the reader's next action comes first, in the
  imperative, one step per line — never buried mid-sentence behind an
  announcement of how easy it is. Status facts follow the actions.
- **Every referent resolves.** Each pronoun and possessive must have one
  unambiguous antecedent ("your machine's run" names nothing; "the queue
  run on your machine" names the thing). If a reader could ask "which one?",
  rewrite the noun phrase.

## Verification pass

After drafting, or when editing someone else's text:

1. **Claim audit.** List each factual claim with its backing next to it.
   Any claim with a blank goes back through Rule 1. Praise counts as a
   claim.
2. **Pattern sweep.** Search the draft for: `not just`, `isn't just`,
   `more than just`, `it's not about`, `studies show`, `research suggests`,
   `experts`, `increasingly`, `great question`, `absolutely right`,
   `certainly`, `i hope this helps`, `let me know if`, `i'd be happy`,
   `feel free to`, `it's important to`, `it's worth noting`, `as mentioned`,
   `in this section`, `let's dive`, `in conclusion`, `ultimately`,
   `despite these challenges`, `testament`, `pivotal`, `crucial`, `vital`,
   `highlighting`, `underscoring`, `emphasizing`. Every hit gets rewritten
   or justified.
3. **Abstraction test.** Any sentence whose nouns could be swapped across
   industries gets rebuilt around a specific, or cut.
4. **Register check.** Read the opening and closing lines: if either could
   plausibly end with a smiley or an offer of further assistance, the
   chat frame is leaking — rewrite both in document voice.
5. **Instruction check.** If the text asks the reader to do anything, the
   actions appear first and in the imperative; anything the reader must
   type or run sits on its own line.

## Sources

- refine.so, "Not just X, but Y: the AI pattern you keep missing" —
  https://refine.so/blog/negative-parallelism-ai-pattern
- Humanized Copy, "The It's-Not-Just-X-It's-Y Tell: AI Negative
  Parallelism" (reports "not just X, but Y" variants in roughly 6% of
  messages in a Washington Post chat dataset) —
  https://humanizedcopy.com/posts/the-it-s-not-just-x-it-s-y-tell-ai-negative-parallelism
- Cheng et al., "Sycophantic AI decreases prosocial intentions and promotes
  dependence", Science (2025) — chatbots endorse users' actions ~49% more
  often than humans do —
  https://www.science.org/doi/10.1126/science.aec8352 (coverage:
  https://www.scientificamerican.com/article/ai-chatbots-are-sucking-up-to-you-with-consequences-for-your-relationships/)
- Tricontinental, "A Systematic Method for Controlling AI Writing Style" —
  documents chatbot artifacts ("Certainly!", "Feel free to reach out")
  leaking into prose —
  https://thetricontinental.org/a-systematic-method-for-controlling-ai-writing-style/
- Wikipedia, "Signs of AI writing" (WikiProject AI Cleanup; the basis of
  humanizer's pattern list — source of the superficial "-ing" analyses,
  knowledge-gap disclaimers, "despite these challenges" formula, and
  importance-inflation phrasings) —
  https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing

`Next stage: none — the drafting or editing skill in play (anti-ai-slop-writing or humanizer) carries the text forward`.
