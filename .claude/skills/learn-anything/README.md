# learn-skill

> A Claude Code skill that turns any subject into a science-backed learning system — Anki cards, Obsidian notes, and a spaced repetition schedule, in one command.

[![Install](https://img.shields.io/badge/install-one%20command-brightgreen?style=flat-square)](#installation)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-skill-blue?style=flat-square)](https://claude.ai/code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Cognitive Science](https://img.shields.io/badge/based%20on-cognitive%20science-purple?style=flat-square)](#science)

---

## What it does

You give Claude any learning material — a PDF, a concept, a vocabulary list — and `learn-skill` builds a complete learning system around it:

| Output | Description |
|--------|-------------|
| **Adaptive learning plan** | Detects content type, asks 2-3 targeted questions, generates a session plan calibrated to your available time |
| **Anki deck (.apkg)** | Exports a ready-to-import Anki file with Basic, Cloze, and reverse cards — no manual work |
| **Obsidian note** | Structured note with concept map, active recall checklist, Feynman section, and review schedule |
| **Spaced repetition schedule** | SM-2 review dates (J+1, J+6, J+14, J+30, J+60) baked into the Obsidian note |

Works for: **courses & text**, **abstract concepts**, **foreign languages** — in any language.

---

## Demo

```
/learn-anything

> I pasted my thermodynamics chapter (12 pages)

Claude detects: Type A — Text/Course
Questions:
  1. Objectif : comprendre en profondeur ou mémoriser ?  →  Comprendre
  2. Temps disponible aujourd'hui ?  →  1h30
  3. Flashcards Anki ?  →  Oui

Generating...
✓ Concept map (8 core concepts)
✓ Full session plan (3 × 50 min Pomodoros)
✓ Feynman checkpoint for entropy and enthalpy
✓ 34 Anki cards → thermodynamics.apkg
✓ Obsidian note → thermodynamics.md (with review schedule)

Next review: Tomorrow, 15 min active recall only.
```

---

## Science

This skill implements five evidence-based learning techniques:

### 1. Spaced Repetition (SM-2 algorithm)
Each card gets review intervals that expand as recall improves: 1d → 6d → 14d → 30d → 60d. The ease factor (default 2.5) adjusts per card based on recall quality.

### 2. Active Recall (Testing Effect)
Every session ends with retrieval practice — no passive re-reading. Retrieving information strengthens the memory trace 2–3× more than reviewing the source material.

### 3. Feynman Technique
After encoding, Claude prompts you to explain the concept in plain language. The points where you struggle are your exact knowledge gaps — those gaps generate targeted Anki cards.

### 4. Chunking
Content is broken into groups of 4±1 concepts (Cowan's updated model of working memory), reducing cognitive load during encoding.

### 5. Desirable Difficulties
The skill forces the **generation effect**: you attempt to recall before seeing the answer. This harder retrieval creates stronger, more durable encoding.

---

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/guepardlover77/learn-skill/main/install.sh | bash
```

Or manually:

```bash
git clone https://github.com/guepardlover77/learn-skill
cd learn-skill
./install.sh
```

Then restart Claude Code. The skill activates automatically when you say "I want to learn X" or via `/learn-anything`.

---

## Usage

### Trigger phrases (any language)
- `/learn-anything`
- "Je veux apprendre [X]"
- "Help me memorize / understand / study [X]"
- "Generate Anki cards for [X]"

### Workflow

1. **Paste your material** (text, notes, vocabulary list) or describe a concept
2. **Answer 2-3 questions** (goal, time available, Anki yes/no)
3. **Get your learning system**: plan + Anki script + Obsidian note
4. **Run the Python script** to export your `.apkg` Anki deck
5. **Follow the review schedule** — Claude tracks it in Obsidian

---

## Examples

See [`examples/`](examples/) for real session outputs:
- [`physics-thermodynamics.md`](examples/physics-thermodynamics.md) — 12-page course → 34 Anki cards
- [`japanese-n5-vocab.md`](examples/japanese-n5-vocab.md) — 50 words → bidirectional deck
- [`quantum-computing.md`](examples/quantum-computing.md) — abstract concept → concept map + Feynman

---

## Requirements

- [Claude Code](https://claude.ai/code) (any plan)
- Python 3.8+ with `genanki` for Anki export: `pip install genanki`
- [Obsidian](https://obsidian.md) (optional, for progress tracking)
- [Anki](https://apps.ankiweb.net) (optional, for spaced repetition)

---

## How it works

The skill is a single `SKILL.md` file that Claude Code reads as instructions. It contains:

1. A **content-type detector** (text/course vs abstract concept vs language)
2. An **adaptive interview** (2-3 questions max, tuned per content type)
3. A **session planner** (sprint / full / deep-dive based on available time)
4. A **card generator** (Basic, Cloze, Reverse — genanki-compatible Python output)
5. An **Obsidian template** (concept map, Feynman section, review log)
6. A **post-session protocol** (what to do in the next 24h)

---

## Contributing

PRs welcome. Especially interested in:
- New content-type detectors (e.g. code/programming, music theory)
- Better card templates for specific domains
- Anki-Connect integration (auto-import without the Python script)
- MCP server version

---

## License

MIT — use it, fork it, improve it.
