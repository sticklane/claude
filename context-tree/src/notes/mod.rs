//! R12 notes storage: one ULID-named markdown file per note under
//! `.context/notes/`, YAML frontmatter (id, C1 anchor path, C2 anchor hash,
//! optional kind, C9 author/created) over a free-text body. Notes are
//! version-tracked source (R14 merges them under plain VCS semantics); the
//! system's only write to a note file after creation is the anchor path at a
//! persistence point (R13, a later task) — never the body.

pub mod anchor;
pub mod freshness;
pub mod reanchor;

use crate::project::CONTEXT_DIR;
use sha2::{Digest, Sha256};
use std::fs;
use std::io;
use std::path::Path;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

/// A parsed note: frontmatter fields plus the body and the note file's
/// repo-relative path. Freshness is not stored here — it is derived (R12).
#[derive(Debug, Clone)]
pub struct Note {
    pub id: String,
    pub anchor_path: String,
    pub anchor_hash: String,
    pub kind: Option<String>,
    pub author: String,
    pub created: String,
    pub body: String,
    pub rel_path: String,
}

/// The inputs `ctx notes add` needs to write a note; id, author, and created are
/// filled in at write time (C9).
pub struct NoteDraft {
    pub anchor_path: String,
    pub anchor_hash: String,
    pub kind: Option<String>,
    pub body: String,
}

/// Parse a note's YAML frontmatter and body. Returns `Err(reason)` — a
/// self-contained diagnostic including `rel_path` — when the frontmatter is
/// unparseable or missing a required field (R12: skipped, never fatal).
pub fn parse_note(rel_path: &str, text: &str) -> Result<Note, String> {
    let after_open = text
        .strip_prefix("---\n")
        .ok_or_else(|| format!("{rel_path}: missing YAML frontmatter opening `---`"))?;
    let close = after_open
        .find("\n---")
        .ok_or_else(|| format!("{rel_path}: unterminated YAML frontmatter"))?;
    let fm = &after_open[..close];
    let rest = &after_open[close + 1..];
    let body = rest
        .strip_prefix("---\n")
        .or_else(|| rest.strip_prefix("---"))
        .unwrap_or(rest)
        .to_string();

    let mut fields = std::collections::HashMap::new();
    for line in fm.lines() {
        if let Some((k, v)) = line.split_once(':') {
            fields.insert(k.trim().to_string(), v.trim().to_string());
        }
    }
    let required = |key: &str| -> Result<String, String> {
        fields
            .get(key)
            .filter(|s| !s.is_empty())
            .cloned()
            .ok_or_else(|| format!("{rel_path}: missing `{key}` in frontmatter"))
    };

    Ok(Note {
        id: required("id")?,
        anchor_path: required("anchor_path")?,
        anchor_hash: required("anchor_hash")?,
        kind: fields.get("kind").filter(|s| !s.is_empty()).cloned(),
        author: fields.get("author").cloned().unwrap_or_default(),
        created: fields.get("created").cloned().unwrap_or_default(),
        body,
        rel_path: rel_path.to_string(),
    })
}

/// Load every note under `root/.context/notes/`, returning the parsed notes and
/// one diagnostic string per skipped (unparseable/incomplete) file — the caller
/// emits each as a single line (R12).
pub fn load_all(root: &Path) -> (Vec<Note>, Vec<String>) {
    let dir = root.join(CONTEXT_DIR).join("notes");
    let mut notes = Vec::new();
    let mut diagnostics = Vec::new();
    let rd = match fs::read_dir(&dir) {
        Ok(rd) => rd,
        Err(_) => return (notes, diagnostics),
    };
    let mut paths: Vec<_> = rd
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|x| x.to_str()) == Some("md"))
        .collect();
    paths.sort();
    for p in paths {
        let name = p.file_name().unwrap_or_default().to_string_lossy();
        let rel = format!("{CONTEXT_DIR}/notes/{name}");
        match fs::read_to_string(&p) {
            Ok(text) => match parse_note(&rel, &text) {
                Ok(n) => notes.push(n),
                Err(reason) => diagnostics.push(reason),
            },
            Err(e) => diagnostics.push(format!("{rel}: {e}")),
        }
    }
    (notes, diagnostics)
}

/// Write a new note file, returning its repo-relative path. Fills in a fresh
/// ULID id, the resolved C9 author, and the ISO-8601 UTC creation timestamp.
pub fn write_note(root: &Path, draft: &NoteDraft) -> io::Result<String> {
    let id = ulid();
    let author = resolve_author(root);
    let created = now_iso8601();

    let mut content = String::new();
    content.push_str("---\n");
    content.push_str(&format!("id: {id}\n"));
    content.push_str(&format!("anchor_path: {}\n", draft.anchor_path));
    content.push_str(&format!("anchor_hash: {}\n", draft.anchor_hash));
    if let Some(k) = &draft.kind {
        content.push_str(&format!("kind: {k}\n"));
    }
    content.push_str(&format!("author: {author}\n"));
    content.push_str(&format!("created: {created}\n"));
    content.push_str("---\n");
    content.push_str(&draft.body);
    if !content.ends_with('\n') {
        content.push('\n');
    }

    let dir = root.join(CONTEXT_DIR).join("notes");
    fs::create_dir_all(&dir)?;
    let rel = format!("{CONTEXT_DIR}/notes/{id}.md");
    fs::write(root.join(&rel), content)?;
    Ok(rel)
}

/// C9 author resolution: `$CTX_AUTHOR`, else the VCS adapter's user identity,
/// else `unknown`.
pub fn resolve_author(root: &Path) -> String {
    std::env::var("CTX_AUTHOR")
        .ok()
        .filter(|a| !a.is_empty())
        .or_else(|| {
            crate::vcs::detect(root)
                .user_identity(root)
                .filter(|id| !id.is_empty())
        })
        .unwrap_or_else(|| "unknown".to_string())
}

static ULID_COUNTER: AtomicU64 = AtomicU64::new(0);

/// A ULID: a 48-bit millisecond timestamp followed by 80 bits of randomness,
/// Crockford base32 (26 chars). The randomness is derived from a high-resolution
/// clock, a per-process counter, and the pid — collision-resistant enough for a
/// note filename without adding a crypto-RNG dependency.
pub fn ulid() -> String {
    const ALPHABET: &[u8; 32] = b"0123456789ABCDEFGHJKMNPQRSTVWXYZ";
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default();
    let ms = (now.as_millis() as u64) & ((1u64 << 48) - 1);
    let counter = ULID_COUNTER.fetch_add(1, Ordering::Relaxed);

    let mut hasher = Sha256::new();
    hasher.update(now.as_nanos().to_le_bytes());
    hasher.update(counter.to_le_bytes());
    hasher.update(std::process::id().to_le_bytes());
    let digest = hasher.finalize();
    let mut rand80: u128 = 0;
    for &b in digest.iter().take(10) {
        rand80 = (rand80 << 8) | b as u128;
    }

    let value: u128 = ((ms as u128) << 80) | rand80;
    let mut out = [0u8; 26];
    for (i, slot) in out.iter_mut().enumerate() {
        let shift = 5 * (25 - i);
        *slot = ALPHABET[((value >> shift) & 0x1f) as usize];
    }
    String::from_utf8(out.to_vec()).unwrap_or_default()
}

/// The current time as an ISO-8601 UTC string (`YYYY-MM-DDTHH:MM:SSZ`, C9).
pub fn now_iso8601() -> String {
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    iso8601_utc(secs)
}

/// Render Unix seconds as ISO-8601 UTC via Howard Hinnant's days-from-civil
/// inverse — no calendar dependency (C9).
fn iso8601_utc(secs: u64) -> String {
    let days = (secs / 86_400) as i64;
    let rem = secs % 86_400;
    let (hh, mm, ss) = (rem / 3600, (rem % 3600) / 60, rem % 60);

    let z = days + 719_468;
    let era = (if z >= 0 { z } else { z - 146_096 }) / 146_097;
    let doe = z - era * 146_097;
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let year = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let day = doy - (153 * mp + 2) / 5 + 1;
    let month = if mp < 10 { mp + 3 } else { mp - 9 };
    let year = if month <= 2 { year + 1 } else { year };

    format!("{year:04}-{month:02}-{day:02}T{hh:02}:{mm:02}:{ss:02}Z")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_note_reads_frontmatter_and_body() {
        let text = "---\nid: 01ABC\nanchor_path: m.f\nanchor_hash: deadbeef\nkind: gotcha\nauthor: x\ncreated: 2026-01-01T00:00:00Z\n---\nbody line\n";
        let n = parse_note(".context/notes/01ABC.md", text).unwrap();
        assert_eq!(n.id, "01ABC");
        assert_eq!(n.anchor_path, "m.f");
        assert_eq!(n.anchor_hash, "deadbeef");
        assert_eq!(n.kind.as_deref(), Some("gotcha"));
        assert_eq!(n.body, "body line\n");
    }

    #[test]
    fn parse_note_rejects_missing_frontmatter() {
        assert!(parse_note("bad.md", "just text\n").is_err());
    }

    #[test]
    fn parse_note_rejects_incomplete_frontmatter() {
        let text = "---\nid: 01ABC\nkind: gotcha\n---\nbody\n";
        assert!(parse_note("bad.md", text).is_err());
    }

    #[test]
    fn ulid_is_26_crockford_chars_and_unique() {
        let a = ulid();
        let b = ulid();
        assert_eq!(a.len(), 26);
        assert_ne!(a, b);
        assert!(
            a.bytes()
                .all(|c| b"0123456789ABCDEFGHJKMNPQRSTVWXYZ".contains(&c))
        );
    }

    #[test]
    fn iso8601_utc_renders_epoch() {
        assert_eq!(iso8601_utc(0), "1970-01-01T00:00:00Z");
        assert_eq!(iso8601_utc(1_600_000_000), "2020-09-13T12:26:40Z");
    }
}
