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
use crate::{extract, vcs};
use journal::{JournalRecord, Trigger};
use lock::AdvisoryLock;
use sha2::{Digest, Sha256};
use std::collections::HashSet;
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

    let mut hashed = 0usize;
    let mut parsed = 0usize;
    let mut present: HashSet<&str> = HashSet::new();

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

    // Re-derive note freshness against the just-updated symbols (R2/R3/R12),
    // under the sync lock. A note with unparseable/incomplete frontmatter is
    // skipped with one diagnostic line; it never aborts the sync.
    let (notes, diagnostics) = crate::notes::load_all(root);
    for reason in &diagnostics {
        eprintln!("ctx: skipping note — {reason}");
    }
    store.refresh_notes(&notes).map_err(to_io)?;

    store.set_last_sync(now).map_err(to_io)?;
    journal::append(
        &cache,
        &JournalRecord {
            trigger,
            scanned,
            hashed,
            parsed,
            pending_reanchors: 0,
        },
    )?;
    Ok(SyncStats {
        scanned,
        hashed,
        parsed,
    })
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
