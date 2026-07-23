# Example Session — Japanese N5 Vocabulary (50 words)

> Real session output. Material: 50 JLPT N5 vocabulary words.

---

## Interview

```
Content detected: Type C — Foreign Language (Japanese vocabulary list)

Questions:
1. Native language + current level in Japanese?  →  French, absolute beginner (A1)
2. Focus: vocabulary, grammar, reading, speaking/writing?  →  Vocabulary + reading (hiragana)
3. Export Anki flashcards (.apkg)?  →  Yes
```

---

## Session Plan (detected: 50 words → recommend 2 sessions of 25)

### Session 1 — Words 1–25 (45 min)

**Semantic clustering** (don't study alphabetically):

| Cluster | Words |
|---------|-------|
| Numbers | いち、に、さん、し、ご、ろく、なな、はち、きゅう、じゅう |
| Time | いま、きょう、あした、きのう、まいにち |
| People | わたし、あなた、かれ、かのじょ、ともだち |
| Places | うち、がっこう、えき、みせ |
| Actions | たべる、のむ、みる、きく、いく、くる |

**Protocol per cluster:**
1. Read all words in cluster once
2. Cover Japanese, guess from English
3. Cover English, produce Japanese
4. Mark failures → priority Anki cards

---

## Anki Cards (50 total — bidirectional = 100 actual cards)

### Card types used

**FR → JP** (recognition)
```
Front: manger
Back: たべる (taberu)
      食べる
      [example: まいにち やさいを たべる — I eat vegetables every day]
```

**JP → FR** (production — harder, more valuable)
```
Front: たべる
Back: manger / to eat
      食べる
      [reading: taberu]
```

**Cloze in sentence**
```
わたしは まいにち がっこうに {{c1::いきます}} — I go to school every day
```

### Python script output (generates japanese-n5.apkg)

```python
import genanki, random

deck = genanki.Deck(random.randrange(1<<30,1<<31), 'Japanese N5 Vocabulary')

model = genanki.Model(random.randrange(1<<30,1<<31), 'JP-FR Bidirectional',
    fields=[{'name':'Japanese'},{'name':'Reading'},{'name':'French'},{'name':'Example'}],
    templates=[
        {'name':'JP→FR','qfmt':'{{Japanese}}<br><small>{{Reading}}</small>',
         'afmt':'{{FrontSide}}<hr>{{French}}<br><i>{{Example}}</i>'},
        {'name':'FR→JP','qfmt':'{{French}}',
         'afmt':'{{FrontSide}}<hr>{{Japanese}}<br><small>{{Reading}}</small><br><i>{{Example}}</i>'},
    ])

vocab = [
    # (japanese, reading, french, example)
    ('たべる', 'taberu', 'manger', 'まいにち やさいを たべる'),
    ('のむ', 'nomu', 'boire', 'みずを のみます'),
    ('いく', 'iku', 'aller', 'がっこうに いきます'),
    ('くる', 'kuru', 'venir', 'うちに きます'),
    ('みる', 'miru', 'voir / regarder', 'えいがを みます'),
    # ... (50 words total)
]

for jp, reading, fr, ex in vocab:
    deck.add_note(genanki.Note(model=model, fields=[jp, reading, fr, ex]))

genanki.Package(deck).write_to_file('japanese-n5.apkg')
print('✓ japanese-n5.apkg — 50 words × 2 directions = 100 cards')
```

---

## Review Schedule

```
Day 0  : Learn clusters 1-3 (25 words)
Day 1  : Active recall on Day 0 words + learn clusters 4-5 (25 words)
Day 2  : Anki session — all 50 words
Day 7  : Anki session (failed cards only)
Day 14 : Full deck review + 25 new N5 words
Day 30 : Maintenance — 10 min Anki daily
```

---

## Obsidian Note

```markdown
---
tags: [learning, japanese, jlpt-n5, vocabulary]
created: 2026-06-10
review_due: 2026-06-11
status: in-progress
mastery: 0/10
---

# Japanese N5 — Vocabulary

## Progress
- [x] Cluster 1: Numbers (10 words)
- [x] Cluster 2: Time (5 words)
- [ ] Cluster 3: People (4 words)
- [ ] Cluster 4: Places (4 words)
- [ ] Cluster 5: Actions (6 words)

## Difficult Words
| Word | Problem | Mnemonic |
|------|---------|----------|
| | | |

## Review Schedule
- [ ] J+1 : 2026-06-11
- [ ] J+7 : 2026-06-17
- [ ] J+14 : 2026-06-24
```
