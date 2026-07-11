"""Unit tests for runtimes/parse_headless.py — the shared Headless parser.

Tests the contract three consumers (workboard.py, drain/reference.md,
evals/run.sh) will import: resolve a runtime's `## Headless` template
(joined, placeholders intact) or the `NONE` sentinel, and derive a
match-shape regex for parsing relaunch commands back out of text.
"""

import logging
import unittest

import parse_headless


class HeadlessTemplateTests(unittest.TestCase):
    def test_claude_code_returns_joined_single_line_template(self):
        template = parse_headless.headless_template("claude-code")
        # Backslash continuations collapsed to one line.
        self.assertNotIn("\n", template)
        self.assertNotIn("\\", template)
        # Base invocation shape, placeholder intact.
        self.assertTrue(template.startswith('claude -p "<prompt>"'), template)
        # Downstream flag tokens survive the join.
        self.assertIn("--allowedTools", template)
        self.assertIn("<allowlist>", template)
        self.assertIn("--model", template)

    def test_gemini_cli_returns_joined_single_line_template(self):
        template = parse_headless.headless_template("gemini-cli")
        self.assertNotIn("\n", template)
        self.assertNotIn("\\", template)
        self.assertTrue(template.startswith('gemini -p "<prompt>"'), template)
        self.assertIn("--approval-mode", template)

    def test_antigravity_has_no_fenced_block_returns_none_sentinel(self):
        self.assertEqual(
            parse_headless.headless_template("antigravity"), parse_headless.NONE
        )

    def test_unresolvable_runtime_falls_back_to_claude_code(self):
        with self.assertLogs(parse_headless.logger, level=logging.WARNING):
            fallback = parse_headless.headless_template("totally-not-a-real-runtime")
        self.assertEqual(fallback, parse_headless.headless_template("claude-code"))

    def test_unresolvable_runtime_never_raises(self):
        # Even with logging suppressed, resolution must not blow up.
        logging.getLogger(parse_headless.logger.name).setLevel(logging.CRITICAL)
        try:
            self.assertEqual(
                parse_headless.headless_template("no-such-runtime-xyz"),
                parse_headless.headless_template("claude-code"),
            )
        finally:
            logging.getLogger(parse_headless.logger.name).setLevel(logging.NOTSET)


class MatchRegexTests(unittest.TestCase):
    def _claude_regex(self):
        return parse_headless.derive_match_regex(
            parse_headless.headless_template("claude-code")
        )

    def test_regex_matches_plain_claude_invocation(self):
        regex = self._claude_regex()
        self.assertIsNotNone(regex.search('nohup claude -p "do the thing" &'))

    def test_regex_tolerates_extra_whitespace_and_tabs(self):
        regex = self._claude_regex()
        # Preserves today's BATON_CMD_RE `claude\s+-p` tolerance.
        self.assertIsNotNone(regex.search('claude  -p "x"'))
        self.assertIsNotNone(regex.search('claude\t-p "x"'))

    def test_regex_does_not_match_unrelated_string(self):
        regex = self._claude_regex()
        self.assertIsNone(regex.search("some entirely unrelated sentence"))

    def test_regex_matches_gemini_shape(self):
        regex = parse_headless.derive_match_regex(
            parse_headless.headless_template("gemini-cli")
        )
        self.assertIsNotNone(regex.search('gemini -p "port the thing"'))
        # A gemini regex must NOT claim a claude command.
        self.assertIsNone(regex.search('claude -p "x"'))

    def test_regex_is_none_when_template_is_none_sentinel(self):
        self.assertIsNone(parse_headless.derive_match_regex(parse_headless.NONE))

    def test_regex_is_none_for_no_scriptable_relaunch_runtime(self):
        self.assertIsNone(
            parse_headless.derive_match_regex(
                parse_headless.headless_template("antigravity")
            )
        )


if __name__ == "__main__":
    unittest.main()
