//! R12 derived freshness. A note is fresh iff its anchor path resolves to a
//! symbol AND that symbol's current C2 body hash equals the note's frontmatter
//! anchor hash. Freshness is never stored as ground truth — only cached in the
//! index — so it survives any rebuild by re-deriving from the note file plus
//! the working tree.

/// Derive a note's freshness from the anchored symbol's current C2 body hash
/// (`None` when the anchor path no longer resolves) and the note's frontmatter
/// anchor hash. Fresh iff the anchor resolves and the hashes match.
pub fn is_fresh(current_body_hash: Option<&str>, anchor_hash: &str) -> bool {
    current_body_hash == Some(anchor_hash)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fresh_when_anchor_resolves_and_hash_matches() {
        assert!(is_fresh(Some("abc"), "abc"));
    }

    #[test]
    fn stale_when_body_hash_diverges() {
        assert!(!is_fresh(Some("abc"), "def"));
    }

    #[test]
    fn stale_when_anchor_no_longer_resolves() {
        assert!(!is_fresh(None, "abc"));
    }
}
