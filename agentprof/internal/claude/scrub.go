package claude

import "regexp"

// Secret scrubbing (frame-naming SPEC R1): deterministic redaction applied to
// collapsed prompt text and to reply heads before they reach frames or the
// namer. Three classes run in order, each over what the prior left behind:
// class (a) — a known secret prefix followed by 8+ token chars, valid only
// where the prefix starts a token run; class (b) — any maximal
// [A-Za-z0-9_-]{24,} run mixing digits, uppercase, and lowercase; class (c) —
// a maximal [0-9a-fA-F]{24,} hex run, redacted only when a secret keyword
// (word-boundary, case-insensitive) appears in the keywordWindow bytes
// immediately preceding it, so lowercase-hex API tokens are caught while git
// SHAs and UUIDs in prose stay readable.

const redactedMarker = "[redacted]"

var (
	// Token chars are [A-Za-z0-9_./+-]; {8,} is greedy, so a match extends to
	// the end of the token run. Go regexp has no lookbehind, so the
	// token-run-start requirement is checked on each match's preceding byte.
	secretPrefixRe = regexp.MustCompile(`(?:sk-|cfut_|github_pat_|ghp_|gho_|xoxb-|xoxp-|AKIA|ya29\.|AIza|eyJ)[A-Za-z0-9_./+-]{8,}`)
	// Leftmost-greedy matching makes each match a maximal run.
	longTokenRe = regexp.MustCompile(`[A-Za-z0-9_-]{24,}`)
	// Class (c): a maximal hex run, gated by a nearby secret keyword.
	hexRunRe  = regexp.MustCompile(`[0-9a-fA-F]{24,}`)
	keywordRe = regexp.MustCompile(`(?i)\b(token|key|secret|password|bearer|credential|api[-_]?key)\b`)
)

// keywordWindow is how many bytes immediately before a hex run are scanned for
// a gating secret keyword (SPEC R1).
const keywordWindow = 40

// scrub replaces secret-shaped substrings with "[redacted]" (R1).
func scrub(text string) string {
	text = redactMatches(text, secretPrefixRe, func(match string, start int) bool {
		return start == 0 || !isTokenByte(text[start-1])
	})
	text = redactMatches(text, longTokenRe, func(match string, _ int) bool {
		return hasDigitUpperLower(match)
	})
	// Class (c) runs last, over what (a)/(b) left behind; the marker they
	// insert contains no 24+ hex run, so redacted spans are not reprocessed.
	return redactMatches(text, hexRunRe, func(_ string, start int) bool {
		return keywordPrecedes(text, start)
	})
}

// keywordPrecedes reports whether a secret keyword appears in the keywordWindow
// bytes immediately before runStart.
func keywordPrecedes(text string, runStart int) bool {
	winStart := runStart - keywordWindow
	if winStart < 0 {
		winStart = 0
	}
	return keywordRe.MatchString(text[winStart:runStart])
}

// redactMatches replaces each regexp match satisfying redact with the
// redaction marker.
func redactMatches(text string, re *regexp.Regexp, redact func(match string, start int) bool) string {
	locs := re.FindAllStringIndex(text, -1)
	if locs == nil {
		return text
	}
	var out []byte
	prev := 0
	for _, loc := range locs {
		if !redact(text[loc[0]:loc[1]], loc[0]) {
			continue
		}
		out = append(out, text[prev:loc[0]]...)
		out = append(out, redactedMarker...)
		prev = loc[1]
	}
	out = append(out, text[prev:]...)
	return string(out)
}

// isTokenByte reports whether c is a class-(a) token char [A-Za-z0-9_./+-];
// the class is ASCII-only, so byte inspection suffices in UTF-8 text.
func isTokenByte(c byte) bool {
	switch {
	case 'A' <= c && c <= 'Z', 'a' <= c && c <= 'z', '0' <= c && c <= '9':
		return true
	case c == '_', c == '.', c == '/', c == '+', c == '-':
		return true
	}
	return false
}

func hasDigitUpperLower(s string) bool {
	var digit, upper, lower bool
	for i := 0; i < len(s); i++ {
		switch c := s[i]; {
		case '0' <= c && c <= '9':
			digit = true
		case 'A' <= c && c <= 'Z':
			upper = true
		case 'a' <= c && c <= 'z':
			lower = true
		}
	}
	return digit && upper && lower
}
