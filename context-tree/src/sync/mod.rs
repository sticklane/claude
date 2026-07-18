//! R2 sync engine: incrementally updates the SQLite index. An mtime+size scan
//! (via the VCS adapter's file list) proposes candidates, content hashes
//! confirm, and only genuinely changed files re-parse. A racy-edit guard
//! re-hashes files whose mtime is within the filesystem's timestamp
//! granularity of the previous sync, deletion detection purges removed files'
//! facts, and every sync appends a C5 journal record. Concurrent syncs
//! serialize on an advisory lock (C6).

pub mod journal;
pub mod lock;

use crate::index::IndexStore;
use crate::notes::reanchor::{self, Candidate, OldAnchor};
use crate::{extract, vcs};
use journal::{JournalRecord, Trigger};
use lock::AdvisoryLock;
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

/// Racy-edit window (R2): a file whose mtime falls within this of the previous
/// sync is re-hashed regardless of a size/mtime match, so a same-size
/// same-mtime edit inside the filesystem's timestamp resolution cannot be
/// missed. Chosen coarser than any real filesystem's mtime granularity; erring
/// toward an extra hash is safe, a missed edit is not.
const GRANULARITY_NS: i64 = 100_000_000;

/// `ctx sync --stats` counts (R2).
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct SyncStats {
    pub scanned: usize,
    pub hashed: usize,
    pub parsed: usize,
}

/// The derived-index cache directory for a project root.
pub fn cache_dir(root: &Path) -> PathBuf {
    root.join(crate::project::CONTEXT_DIR).join("cache")
}

fn to_io(e: rusqlite::Error) -> io::Error {
    io::Error::other(e.to_string())
}

fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    hasher
        .finalize()
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}

fn now_ns() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos() as i64)
        .unwrap_or(0)
}

fn mtime_ns(meta: &fs::Metadata) -> i64 {
    meta.modified()
        .ok()
        .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
        .map(|d| d.as_nanos() as i64)
        .unwrap_or(0)
}

/// A file's mtime is "racy" when it sits within the timestamp granularity of
/// the previous sync — mtime alone can't be trusted, so re-hash to confirm.
fn racy(mtime: i64, last_sync: Option<i64>) -> bool {
    matches!(last_sync, Some(ls) if (mtime - ls).abs() < GRANULARITY_NS)
}

/// Incrementally sync the index under `root`, appending one C5 journal record.
/// Serializes with concurrent syncs on the advisory lock (C6).
pub fn run_sync(root: &Path, trigger: Trigger) -> io::Result<SyncStats> {
    let cache = cache_dir(root);
    fs::create_dir_all(&cache)?;
    let _lock = AdvisoryLock::acquire(&cache)?;
    let store = IndexStore::open(&cache).map_err(to_io)?;
    let adapter = vcs::detect(root);

    // The `.context/` subtree (derived cache + notes) is never indexed (R4),
    // independent of any ignore entry.
    let files: Vec<String> = adapter
        .list_files(root)?
        .into_iter()
        .filter(|p| !p.starts_with(&format!("{}/", crate::project::CONTEXT_DIR)))
        .collect();
    let scanned = files.len();

    let prev = store.file_states().map_err(to_io)?;
    let last_sync = store.last_sync().map_err(to_io)?;
    let now = now_ns();

    // Load notes and the carried pending re-anchors, then capture each note's
    // OLD anchor identity from the pre-reparse index — the driver of R13's
    // layered match. A note whose anchor does not resolve now (e.g. after a full
    // rebuild) captures no old identity, so it is not re-anchorable this sync.
    let (notes, diagnostics) = crate::notes::load_all(root);
    for reason in &diagnostics {
        eprintln!("ctx: skipping note — {reason}");
    }
    let mut pending = store.pending_reanchors().map_err(to_io)?;
    let mut old_anchor: HashMap<String, OldAnchor> = HashMap::new();
    let mut old_anchor_file: HashMap<String, String> = HashMap::new();
    for n in &notes {
        let eff = pending
            .get(&n.id)
            .cloned()
            .unwrap_or_else(|| n.anchor_path.clone());
        if let Some(idy) = store.symbol_identity(&eff).map_err(to_io)? {
            old_anchor.insert(
                n.id.clone(),
                OldAnchor {
                    name: idy.name,
                    kind: idy.kind,
                    body_hash: idy.body_hash,
                    body_tokens: idy.body_tokens,
                },
            );
            old_anchor_file.insert(n.id.clone(), idy.file);
        }
    }

    let mut hashed = 0usize;
    let mut parsed = 0usize;
    let mut present: HashSet<&str> = HashSet::new();
    // Candidates for re-anchoring are the changed files' new symbols; a
    // parse-failed file contributes none (R13: unresolved-transient, not vanished).
    let mut changed_syms: Vec<Candidate> = Vec::new();
    let mut parse_failed_files: HashSet<String> = HashSet::new();

    for rel in &files {
        present.insert(rel.as_str());
        let abs = root.join(rel);
        let meta = match fs::metadata(&abs) {
            Ok(m) => m,
            Err(_) => continue,
        };
        let size = meta.len();
        let mtime = mtime_ns(&meta);
        let prior = prev.get(rel);

        let candidate = match prior {
            None => true,
            Some(p) => p.size != size || p.mtime_ns != mtime || racy(mtime, last_sync),
        };
        if !candidate {
            continue;
        }

        let content = match fs::read(&abs) {
            Ok(c) => c,
            Err(_) => continue,
        };
        let file_hash = sha256_hex(&content);
        hashed += 1;

        // Content unchanged (a pure mtime bump): refresh tracking, don't parse.
        if prior.is_some_and(|p| p.hash == file_hash) {
            store.touch_file_meta(rel, size, mtime).map_err(to_io)?;
            continue;
        }

        let ext = abs.extension().and_then(|e| e.to_str()).unwrap_or("");
        let file_id = store
            .upsert_file(rel, &file_hash, size, mtime)
            .map_err(to_io)?;
        // A known-language file re-parses; anything else is tracked (so it is
        // not re-hashed forever) but produces no facts.
        if let Some(extractor) = extract::for_extension(ext) {
            let result = extractor.extract(rel, &content);
            if result.parse_failed {
                parse_failed_files.insert(rel.clone());
            } else {
                for s in &result.symbols {
                    changed_syms.push(Candidate {
                        qpath: s.qpath.clone(),
                        name: s.name.clone(),
                        kind: s.kind.as_str().to_string(),
                        body_hash: s.body_hash.clone(),
                        body_tokens: s.body_tokens.clone(),
                        file: rel.clone(),
                        row: s.full_span.start.row + 1,
                    });
                }
            }
            store.replace_facts(file_id, &result).map_err(to_io)?;
            parsed += 1;
        }
    }

    // Deletion detection: an indexed file no longer scanned is purged (R2).
    for rel in prev.keys() {
        if !present.contains(rel.as_str()) {
            store.delete_file(rel).map_err(to_io)?;
        }
    }

    // R13 re-anchoring: for each note whose effective anchor no longer resolves
    // AND resolved before this sync (old identity captured) AND whose old file
    // did not just become parse-failed (transient, not vanished), apply the
    // layered algorithm over the changed files' new symbols. A resolved new
    // anchor is recorded as a pending phase-1 re-anchor.
    for n in &notes {
        let eff = pending
            .get(&n.id)
            .cloned()
            .unwrap_or_else(|| n.anchor_path.clone());
        if store.symbol_identity(&eff).map_err(to_io)?.is_some() {
            continue; // still resolves — nothing to re-anchor
        }
        let Some(old) = old_anchor.get(&n.id) else {
            continue; // never resolved before this sync — not re-anchorable now
        };
        if let Some(f) = old_anchor_file.get(&n.id)
            && parse_failed_files.contains(f)
        {
            continue; // parse-failed transient: leave the binding untouched
        }
        if let Some(new_path) = reanchor::reanchor(old, &changed_syms) {
            pending.insert(n.id.clone(), new_path);
        }
    }

    store.replace_pending_reanchors(&pending).map_err(to_io)?;
    store.refresh_notes(&notes, &pending).map_err(to_io)?;

    store.set_last_sync(now).map_err(to_io)?;
    journal::append(
        &cache,
        &JournalRecord {
            trigger,
            scanned,
            hashed,
            parsed,
            pending_reanchors: pending.len(),
        },
    )?;
    Ok(SyncStats {
        scanned,
        hashed,
        parsed,
    })
}

/// R13 phase 2 persistence point (`ctx sync --write-anchors`): run a normal sync
/// to compute the current pending re-anchors, then write each into its note
/// file's frontmatter (the only write the system makes to a note file) and clear
/// the pending set. Returns the number of anchors written.
pub fn write_anchors(root: &Path, trigger: Trigger) -> io::Result<usize> {
    run_sync(root, trigger)?;
    let cache = cache_dir(root);
    let _lock = AdvisoryLock::acquire(&cache)?;
    let store = IndexStore::open(&cache).map_err(to_io)?;
    let pending = store.pending_reanchors().map_err(to_io)?;
    if pending.is_empty() {
        return Ok(0);
    }
    // Map note id → its file, from the note files on disk.
    let (notes, _diagnostics) = crate::notes::load_all(root);
    let by_id: HashMap<&str, &str> = notes
        .iter()
        .map(|n| (n.id.as_str(), n.rel_path.as_str()))
        .collect();
    let mut written = 0usize;
    for (note_id, new_path) in &pending {
        if let Some(rel) = by_id.get(note_id.as_str()) {
            crate::notes::rewrite_anchor_path(root, rel, new_path)?;
            written += 1;
        }
    }
    store
        .replace_pending_reanchors(&HashMap::new())
        .map_err(to_io)?;
    Ok(written)
}

/// A query's staleness sweep (C6): when a sync already holds the advisory lock,
/// the query skips its own sweep and reads the current snapshot (the in-flight
/// sync publishes the update); it never blocks and never runs a second
/// concurrent sweep. When the lock is free, it runs a sweep first. Returns a
/// read handle over the resulting snapshot.
pub fn query_sweep(root: &Path) -> io::Result<IndexStore> {
    let cache = cache_dir(root);
    fs::create_dir_all(&cache)?;
    let held = AdvisoryLock::try_acquire(&cache)?.is_none();
    if !held {
        run_sync(root, Trigger::Query)?;
    }
    IndexStore::open(&cache).map_err(to_io)
}
