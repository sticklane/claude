//! R1 minified/generated-bundle detection: classifies a CANDIDATE file (one
//! an `extract::for_extension` extractor would accept) as minified-or-not
//! before parsing, so the sync engine can skip it with a recorded reason
//! instead of burying real symbols in generated-bundle noise.
//!
//! Detection is heuristic and false-negative-favoring: the cost of a false
//! positive (a real source file silently skipped) is worse than a missed
//! minified file (which just parses as noisy symbols, same as today), so
//! every threshold below errs toward NOT flagging.

/// Why a candidate file was classified minified.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MinifiedReason {
    /// Name pattern match (`*.min.js`, `*.min.mjs`) — always skipped.
    Name,
    /// Content heuristic match on an unsuffixed bundle.
    Content,
}

impl MinifiedReason {
    /// The stable string stored in the index and shown as the `ctx tree`
    /// skip marker.
    pub fn as_str(self) -> &'static str {
        match self {
            MinifiedReason::Name => "minified-name",
            MinifiedReason::Content => "minified-content",
        }
    }

    /// Parse a stored reason string back, for readers of the index column.
    pub fn parse(s: &str) -> Option<Self> {
        match s {
            "minified-name" => Some(MinifiedReason::Name),
            "minified-content" => Some(MinifiedReason::Content),
            _ => None,
        }
    }
}

// Content heuristic tunables (pinned by tests/minified.rs's boundary cases).
const CONTENT_SIZE_THRESHOLD_BYTES: usize = 50 * 1024;
const AVG_LINE_LEN_THRESHOLD_BYTES: usize = 400;
const SHORT_FILE_LINE_COUNT: usize = 5;
const DOMINANT_LINE_FRACTION: f64 = 0.5;

/// Classify a CANDIDATE file (one an extractor would accept) as
/// minified-or-not. `rel` is the repo-relative path (the name-pattern
/// check); `content` is the file's raw bytes (the content heuristic).
pub fn classify(rel: &str, content: &[u8]) -> Option<MinifiedReason> {
    if is_minified_name(rel) {
        return Some(MinifiedReason::Name);
    }
    if is_minified_content(content) {
        return Some(MinifiedReason::Content);
    }
    None
}

fn is_minified_name(rel: &str) -> bool {
    rel.ends_with(".min.js") || rel.ends_with(".min.mjs")
}

/// File > 50 KB AND either (a) average line length > 400 bytes, or (b) line
/// count <= 5 AND the largest line holds > 50% of the file's bytes (the
/// whole-bundle-on-one-line shape). The <=5-line guard on (b) deliberately
/// exempts a normal source file with one giant embedded literal (e.g. a
/// base64 blob) amid ordinary code — that shape has many lines, not few.
/// A `//# sourceMappingURL=` comment alone never suffices — it is not
/// checked here.
///
/// (a)'s "average line length" is computed EXCLUDING the single longest
/// line — a trimmed mean, not a plain one. Untrimmed, one embedded giant
/// literal line drags a large file's plain average over 400 regardless of
/// how ordinary its other lines are, which would wrongly flag exactly the
/// file R3's false-positive guard requires stay unflagged; trimming that
/// one outlier reveals the rest of the file's true (ordinary) average. A
/// real uniformly-long-lined bundle's average is barely affected by
/// dropping one line, so detection of that shape is unchanged.
fn is_minified_content(content: &[u8]) -> bool {
    let size = content.len();
    if size <= CONTENT_SIZE_THRESHOLD_BYTES {
        return false;
    }
    let lines: Vec<&[u8]> = content.split(|&b| b == b'\n').collect();
    let line_count = lines.len();
    let (largest_idx, largest_len) = lines
        .iter()
        .enumerate()
        .max_by_key(|(_, l)| l.len())
        .map(|(i, l)| (i, l.len()))
        .unwrap_or((0, 0));

    let rest_count = line_count.saturating_sub(1);
    let rest_len: usize = lines
        .iter()
        .enumerate()
        .filter(|(i, _)| *i != largest_idx)
        .map(|(_, l)| l.len())
        .sum();
    let avg_rest = rest_len.checked_div(rest_count).unwrap_or(largest_len);
    if avg_rest > AVG_LINE_LEN_THRESHOLD_BYTES {
        return true;
    }
    if line_count <= SHORT_FILE_LINE_COUNT
        && (largest_len as f64) > size as f64 * DOMINANT_LINE_FRACTION
    {
        return true;
    }
    false
}
