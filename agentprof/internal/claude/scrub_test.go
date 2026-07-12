package claude

import "testing"

func TestScrubRedactsKnownPrefixSecrets(t *testing.T) {
	cases := []struct{ name, in, want string }{
		{"cfut", "api token: cfut_FAKEfake1234FAKEfake1234 leaked", "api token: [redacted] leaked"},
		{"sk", "key sk-ant-api03-AbCdEfGh12 here", "key [redacted] here"},
		{"ghp", "ghp_abcdefgh12345678", "[redacted]"},
		{"gho", "use gho_ZYXWvut87654321q", "use [redacted]"},
		{"github_pat", "github_pat_11ABCDEFG0abcdefghijk", "[redacted]"},
		{"xoxb", "slack xoxb-1234567890-abcd", "slack [redacted]"},
		{"xoxp", "xoxp-9876543210-wxyz end", "[redacted] end"},
		{"akia", "aws AKIAIOSFODNN7EXAMPLE key", "aws [redacted] key"},
		{"ya29", "ya29.a0AfH6SMBxyzXYZ123", "[redacted]"},
		{"aiza", "AIzaSyA1234bcdEFG", "[redacted]"},
		{"jwt", "bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abc", "bearer [redacted]"},
		{"start of string", "cfut_FAKEfake1234FAKEfake1234", "[redacted]"},
		{"after paren", "(sk-abcdefghi)", "([redacted])"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := scrub(c.in); got != c.want {
				t.Errorf("scrub(%q) = %q, want %q", c.in, got, c.want)
			}
		})
	}
}

func TestScrubRedactsLongMixedCaseTokensWithDigits(t *testing.T) {
	cases := []struct{ name, in, want string }{
		{"24 chars mixed", "token aB3aB3aB3aB3aB3aB3aB3aB3 end", "token [redacted] end"},
		{"underscores and dashes", "x My-Secret_Value1234567890abcXY x", "x [redacted] x"},
		{"accepted false positive jira slug", "JIRA-1234-fix-login-page", "[redacted]"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := scrub(c.in); got != c.want {
				t.Errorf("scrub(%q) = %q, want %q", c.in, got, c.want)
			}
		})
	}
}

func TestScrubLeavesNonSecretsAlone(t *testing.T) {
	cases := []struct{ name, in string }{
		{"uuid", "id 550e8400-e29b-41d4-a716-446655440000 ok"},
		{"git sha", "commit 3f785ce13289f9b24bd53a4b0ecbeef9a2b062f3"},
		{"model id", "model claude-haiku-4-5-20251001 selected"},
		{"lowercase kebab slug", "youtube-rss-cron-pipeline"},
		{"digit-free camelCase", "surveyJsIntegrationGuide"},
		{"mid-word eyJ", "monkeyJumpsOver the fence"},
		{"mid-word sk-", "task-abcdefgh123 queued"},
		{"prefix with too few token chars", "sk-abcdefg only"},
		{"plain prose", "how are we doing?"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := scrub(c.in); got != c.in {
				t.Errorf("scrub(%q) = %q, want unchanged", c.in, got)
			}
		})
	}
}

// Class (c): keyword-gated hex. A maximal [0-9a-fA-F]{24,} run is redacted
// only when a secret keyword (word-boundary, case-insensitive) appears in the
// 40 bytes immediately preceding the run. All hex values here are SYNTHETIC.
func TestScrubRedactsKeywordGatedHex(t *testing.T) {
	cases := []struct{ name, in, want string }{
		// Observed 2026-07-11 incident shape, verbatim preceding bytes.
		{"incident shape", "Todoist token: deadbeefcafef00d1234567890abcdef01234567", "Todoist token: [redacted]"},
		{"keyword plus 40 hex", "api_key = deadbeefcafef00d1234567890abcdef01234567 done", "api_key = [redacted] done"},
		{"24 hex with keyword", "key: abcdef0123456789abcdef01", "key: [redacted]"},
		// Digit-free mixed-case hex: class (b) cannot match (no digit), so this
		// isolates class (c).
		{"digit-free mixed hex with keyword", "secret aBcDeFaBcDeFaBcDeFaBcDeF", "secret [redacted]"},
		// A larger mixed-case-with-digits run embedding a hex sub-run is
		// consumed whole by (b) before (c) runs: exactly one [redacted].
		{"whole run b before c", "secret Ab1234567890cdef1234567890XY", "secret [redacted]"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := scrub(c.in); got != c.want {
				t.Errorf("scrub(%q) = %q, want %q", c.in, got, c.want)
			}
		})
	}
}

func TestScrubLeavesKeywordlessOrShortHexAlone(t *testing.T) {
	cases := []struct{ name, in string }{
		// "monkey" embeds "key" but no \bkey\b word boundary gates it.
		{"monkey plus 40 hex", "monkey deadbeefcafef00d1234567890abcdef01234567"},
		{"bare sha in prose", "at commit a1b2c3d4e5f60718293a4b5c6d7e8f9012345678 today"},
		// Keyword sits more than 40 bytes before the run's first byte.
		{"keyword outside window", "token and here is a fairly long stretch of filler prose text zzz deadbeefcafef00d1234567890abcdef01234567"},
		// 23-char run is one byte too short for the {24,} class.
		{"23 hex with keyword", "key: abcdef0123456789abcdef0"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := scrub(c.in); got != c.in {
				t.Errorf("scrub(%q) = %q, want unchanged", c.in, got)
			}
		})
	}
}

func TestScrubAppliesClassAThenClassB(t *testing.T) {
	// The cfut_ token also matches the class-(b) shape; class (a) must
	// consume it whole so exactly one [redacted] is emitted.
	in := "cfut_FAKEfake1234FAKEfake1234"
	if got := scrub(in); got != "[redacted]" {
		t.Errorf("scrub(%q) = %q, want single [redacted]", in, got)
	}
	// A class-(b) token adjacent to a class-(a) hit is still caught.
	in = "sk-abcdefghi and My-Secret_Value1234567890abcXY"
	want := "[redacted] and [redacted]"
	if got := scrub(in); got != want {
		t.Errorf("scrub(%q) = %q, want %q", in, got, want)
	}
}
