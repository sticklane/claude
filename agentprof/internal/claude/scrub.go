package claude

import "regexp"

// Secret scrubbing (frame-naming SPEC R1): deterministic redaction applied to
// collapsed prompt text and to reply heads before they reach frames or the
// namer. Class (a) — a known secret prefix followed by 8+ token chars, valid
// only where the prefix starts a token run — is applied first; class (b) —
// any maximal [A-Za-z0-9_-]{24,} run mixing digits, uppercase, and lowercase
// — runs over the result.

const redactedMarker = "[redacted]"

var (
	// Token chars are [A-Za-z0-9_./+-]; {8,} is greedy, so a match extends to
	// the end of the token run. Go regexp has no lookbehind, so the
	// token-run-start requirement is checked on each match's preceding byte.
	secretPrefixRe = regexp.MustCompile(`(?:sk-|cfut_|github_pat_|ghp_|gho_|xoxb-|xoxp-|AKIA|ya29\.|AIza|eyJ)[A-Za-z0-9_./+-]{8,}`)
	// Leftmost-greedy matching makes each match a maximal run.
	longTokenRe = regexp.MustCompile(`[A-Za-z0-9_-]{24,}`)
)

// scrub replaces secret-shaped substrings with "[redacted]" (R1).
func scrub(text string) string {
	text = redactMatches(text, secretPrefixRe, func(match string, start int) bool {
		return start == 0 || !isTokenByte(text[start-1])
	})
	return redactMatches(text, longTokenRe, func(match string, _ int) bool {
		return hasDigitUpperLower(match)
	})
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
