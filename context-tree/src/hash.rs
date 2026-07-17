//! C2 body content hashing: SHA-256 over the definition's full-span bytes with
//! the identifier-span bytes excised, so a pure rename leaves the hash
//! unchanged. Also produces the identifier-excised token set (R13 input).

use sha2::{Digest, Sha256};

/// Concatenate the full-span bytes with the identifier-span bytes removed.
/// `ident` must be a sub-range of `full`.
pub fn excised_bytes(source: &[u8], full: (usize, usize), ident: (usize, usize)) -> Vec<u8> {
    let (fs, fe) = full;
    let (is, ie) = ident;
    debug_assert!(fs <= is && ie <= fe, "ident span must be within full span");
    let mut out = Vec::with_capacity((fe - fs).saturating_sub(ie - is));
    out.extend_from_slice(&source[fs..is]);
    out.extend_from_slice(&source[ie..fe]);
    out
}

fn to_hex(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        s.push_str(&format!("{b:02x}"));
    }
    s
}

/// C2 hash: hex SHA-256 over the identifier-excised full-span bytes.
pub fn body_hash(source: &[u8], full: (usize, usize), ident: (usize, usize)) -> String {
    let bytes = excised_bytes(source, full, ident);
    let mut hasher = Sha256::new();
    hasher.update(&bytes);
    to_hex(&hasher.finalize())
}

/// The identifier-excised body token set (C2's byte basis, tokenized): the
/// sorted, de-duplicated `[A-Za-z0-9_]+` runs of the excised bytes.
pub fn body_tokens(source: &[u8], full: (usize, usize), ident: (usize, usize)) -> Vec<String> {
    let bytes = excised_bytes(source, full, ident);
    let text = String::from_utf8_lossy(&bytes);
    let mut set: std::collections::BTreeSet<String> = std::collections::BTreeSet::new();
    let mut cur = String::new();
    for ch in text.chars() {
        if ch.is_alphanumeric() || ch == '_' {
            cur.push(ch);
        } else if !cur.is_empty() {
            set.insert(std::mem::take(&mut cur));
        }
    }
    if !cur.is_empty() {
        set.insert(cur);
    }
    set.into_iter().collect()
}
