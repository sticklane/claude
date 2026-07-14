"""Structural coverage for render_markdown() — the dependency-free markdown →
HTML pass that runs on every /spec/ GET.

Assertions target parsed structure (heading tags at their source level, list
items present, fenced-code content preserved), never a full-string HTML
comparison — so a reflow of surrounding markup doesn't break them, but a real
regression in heading-level computation does (see
TestRenderMarkdownHeadingLevels).
"""

import importlib.util
import re
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "ac", str(Path(__file__).resolve().parent.parent / "agent-console.py")
)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)


# Fixture exercising: three heading levels, an unordered list (both bullet
# styles), and a fenced code block whose content includes markup-looking text
# that must be preserved as escaped literal, not re-parsed.
FIXTURE = """\
# Title One

Intro paragraph.

## Section Two

### Subsection Three

- first item
- second item
* third item

```
def make(level):
    return level
```
"""


def _headings(html):
    """[(level:int, inner_text:str)] for every <hN>...</hN> in render order."""
    return [
        (int(lvl), text) for lvl, text in re.findall(r"<h([1-6])>(.*?)</h\1>", html)
    ]


class TestRenderMarkdownHeadingLevels(unittest.TestCase):
    """The mutation-kill test: fails if heading-level parsing is stubbed to a
    constant (e.g. always <h1>)."""

    def test_headings_render_at_their_source_depth(self):
        headings = _headings(ac.render_markdown(FIXTURE))
        # Each source heading keeps its own depth — a constant-level stub
        # collapses these and this assertion fails.
        self.assertIn((1, "Title One"), headings)
        self.assertIn((2, "Section Two"), headings)
        self.assertIn((3, "Subsection Three"), headings)

    def test_distinct_source_levels_produce_distinct_tags(self):
        levels = {lvl for lvl, _ in _headings(ac.render_markdown(FIXTURE))}
        # A stub that emits one fixed level would collapse this to a single value.
        self.assertEqual(levels, {1, 2, 3})


class TestRenderMarkdownLists(unittest.TestCase):
    def test_unordered_items_each_become_list_elements(self):
        html = ac.render_markdown(FIXTURE)
        items = re.findall(r"<li>(.*?)</li>", html)
        self.assertIn("first item", items)
        self.assertIn("second item", items)
        self.assertIn("third item", items)  # '*' bullets parse too

    def test_list_is_wrapped_in_a_single_ul(self):
        html = ac.render_markdown(FIXTURE)
        self.assertEqual(html.count("<ul>"), 1)
        self.assertEqual(html.count("</ul>"), 1)


class TestRenderMarkdownCodeFence(unittest.TestCase):
    def test_fenced_content_is_preserved_inside_a_pre_code_block(self):
        html = ac.render_markdown(FIXTURE)
        block = re.search(r"<pre><code>(.*?)</code></pre>", html, re.DOTALL)
        self.assertIsNotNone(block, "no <pre><code> block emitted")
        self.assertIn("def make(level):", block.group(1))
        self.assertIn("return level", block.group(1))

    def test_markup_in_a_code_fence_is_escaped_not_reparsed(self):
        html = ac.render_markdown("```\n# not a heading <b>x</b>\n```")
        # '#' inside a fence must not become a heading, and angle brackets
        # must be escaped rather than passed through as live markup.
        self.assertNotIn("<h1>", html)
        self.assertIn("&lt;b&gt;", html)


if __name__ == "__main__":
    unittest.main()
