//! C6 SQLite index store: WAL-mode persistence of per-file facts (R1/R9),
//! keyed for per-file replace-on-reparse and O(what-was-asked) queries.
//!
//! The store persists `Symbol`, `Reference`, `Import`, and `Scope` facts keyed
//! by an owning `files` row, so a re-parsed file's stale facts are replaced
//! (never accumulated) and `ctx deps`/`ctx refs` (tasks 06–07) read edges
//! straight from the index without re-parsing source.

use crate::extract::ExtractResult;
use rusqlite::{Connection, OptionalExtension, params};
use std::collections::HashMap;
use std::path::Path;
use std::time::Duration;

/// Bumped whenever the on-disk schema shape changes; a version-mismatched or
/// unreadable cache is wiped and rebuilt transparently (C4).
const SCHEMA_VERSION: i64 = 2;

const SCHEMA_SQL: &str = "
CREATE TABLE IF NOT EXISTS schema_meta (version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS sync_meta (id INTEGER PRIMARY KEY CHECK (id = 0), last_sync_ns INTEGER);
CREATE TABLE IF NOT EXISTS files (
    id       INTEGER PRIMARY KEY,
    path     TEXT NOT NULL UNIQUE,
    hash     TEXT NOT NULL,
    size     INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS symbols (
    id               INTEGER PRIMARY KEY,
    file_id          INTEGER NOT NULL,
    kind             TEXT NOT NULL,
    name             TEXT NOT NULL,
    qpath            TEXT NOT NULL,
    signature        TEXT NOT NULL,
    docstring        TEXT NOT NULL,
    full_start_byte  INTEGER NOT NULL,
    full_end_byte    INTEGER NOT NULL,
    ident_start_byte INTEGER NOT NULL,
    ident_end_byte   INTEGER NOT NULL,
    parent           TEXT,
    body_hash        TEXT NOT NULL,
    body_tokens      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS refs (
    id      INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    name    TEXT NOT NULL,
    kind    TEXT NOT NULL,
    row     INTEGER NOT NULL,
    col     INTEGER NOT NULL,
    byte    INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS imports (
    id      INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    source  TEXT NOT NULL,
    module  TEXT NOT NULL,
    name    TEXT,
    row     INTEGER NOT NULL,
    col     INTEGER NOT NULL,
    byte    INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS scopes (
    id               INTEGER PRIMARY KEY,
    file_id          INTEGER NOT NULL,
    name             TEXT NOT NULL,
    def_row          INTEGER NOT NULL,
    def_col          INTEGER NOT NULL,
    def_byte         INTEGER NOT NULL,
    scope_start_byte INTEGER NOT NULL,
    scope_end_byte   INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS notes (
    id          TEXT PRIMARY KEY,
    rel_path    TEXT NOT NULL,
    anchor_path TEXT NOT NULL,
    anchor_hash TEXT NOT NULL,
    kind        TEXT,
    author      TEXT NOT NULL,
    created     TEXT NOT NULL,
    body        TEXT NOT NULL,
    fresh       INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_notes_anchor ON notes(anchor_path);
CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_id);
CREATE INDEX IF NOT EXISTS idx_symbols_qpath ON symbols(qpath);
CREATE INDEX IF NOT EXISTS idx_refs_file ON refs(file_id);
CREATE INDEX IF NOT EXISTS idx_refs_name ON refs(name);
CREATE INDEX IF NOT EXISTS idx_imports_file ON imports(file_id);
CREATE INDEX IF NOT EXISTS idx_imports_module ON imports(module);
CREATE INDEX IF NOT EXISTS idx_scopes_file ON scopes(file_id);
";

/// Separator joining a symbol's body-token set for storage; ASCII Unit
/// Separator never appears in lexical source tokens, so the round-trip is
/// lossless.
const TOKEN_SEP: &str = "\u{1f}";

/// The per-file state the incremental scan compares against (R2).
#[derive(Debug, Clone)]
pub struct PrevState {
    pub id: i64,
    pub hash: String,
    pub size: u64,
    pub mtime_ns: i64,
}

/// A symbol read back from the index for the query commands (tasks 06–07). Carries
/// the owning file path and the C1 containment link so `ctx tree`/`ctx sig`/`ctx map`
/// render an outline, resolve a suffix, and rank without re-parsing source.
#[derive(Debug, Clone)]
pub struct SymbolRow {
    pub id: i64,
    pub kind: String,
    pub name: String,
    pub qpath: String,
    pub signature: String,
    pub docstring: String,
    pub parent: Option<String>,
    pub path: String,
    pub full_start_byte: usize,
    pub full_end_byte: usize,
    pub ident_start_byte: usize,
    /// C2 body content hash — the anchor hash `ctx notes add` records (R12).
    pub body_hash: String,
}

/// A note read back from the derived cache for `ctx notes`/`ctx notes list`
/// (R12): the frontmatter fields, the cached derived freshness, and the current
/// file of the anchored symbol (`None` when the anchor no longer resolves).
#[derive(Debug, Clone)]
pub struct NoteRow {
    pub id: String,
    pub rel_path: String,
    pub anchor_path: String,
    pub kind: Option<String>,
    pub author: String,
    pub created: String,
    pub body: String,
    pub fresh: bool,
    pub file: Option<String>,
}

/// A reference occurrence read back for `ctx refs` (R10): the referenced name,
/// its use kind, and the owning file path + position, so a heuristic global-name
/// match renders `file:line` without re-parsing source.
#[derive(Debug, Clone)]
pub struct RefRow {
    pub name: String,
    pub kind: String,
    pub path: String,
    pub row: usize,
    pub byte: usize,
}

/// A module-level import edge read back for `ctx deps` (R9): the importing file's
/// module component (`source`), the imported target string (`module`), and the
/// owning file path + line.
#[derive(Debug, Clone)]
pub struct ImportRow {
    pub source: String,
    pub module: String,
    pub path: String,
    pub row: usize,
}

/// A locals-query scope binding read back for scope-aware `ctx refs` (R10): a
/// `name` bound locally within `[scope_start_byte, scope_end_byte)` in a file.
/// A reference to `name` inside that span is a shadowed local, excluded from the
/// cross-file candidate set.
#[derive(Debug, Clone)]
pub struct ScopeRow {
    pub name: String,
    pub path: String,
    pub scope_start_byte: usize,
    pub scope_end_byte: usize,
}

/// A WAL-mode SQLite connection over the derived index at
/// `<cache_dir>/index.sqlite`.
pub struct IndexStore {
    conn: Connection,
}

impl IndexStore {
    /// Open (creating if absent) the index in `cache_dir`, in WAL mode with a
    /// busy timeout (C6). A version-mismatched cache is wiped and rebuilt (C4).
    pub fn open(cache_dir: &Path) -> rusqlite::Result<Self> {
        std::fs::create_dir_all(cache_dir).ok();
        let conn = Connection::open(cache_dir.join("index.sqlite"))?;
        conn.execute_batch("PRAGMA journal_mode=WAL;")?;
        conn.busy_timeout(Duration::from_secs(5))?;
        let store = IndexStore { conn };
        store.init_schema()?;
        Ok(store)
    }

    fn init_schema(&self) -> rusqlite::Result<()> {
        self.conn.execute_batch(SCHEMA_SQL)?;
        let version: Option<i64> = self
            .conn
            .query_row("SELECT version FROM schema_meta LIMIT 1", [], |r| r.get(0))
            .optional()?;
        match version {
            None => {
                self.conn.execute(
                    "INSERT INTO schema_meta(version) VALUES (?1)",
                    params![SCHEMA_VERSION],
                )?;
            }
            Some(v) if v != SCHEMA_VERSION => self.rebuild()?,
            Some(_) => {}
        }
        Ok(())
    }

    /// Wipe every table and recreate the schema at the current version (C4's
    /// transparent rebuild on a version mismatch).
    fn rebuild(&self) -> rusqlite::Result<()> {
        self.conn.execute_batch(
            "DROP TABLE IF EXISTS symbols;
             DROP TABLE IF EXISTS refs;
             DROP TABLE IF EXISTS imports;
             DROP TABLE IF EXISTS scopes;
             DROP TABLE IF EXISTS notes;
             DROP TABLE IF EXISTS files;
             DROP TABLE IF EXISTS sync_meta;
             DELETE FROM schema_meta;",
        )?;
        self.conn.execute_batch(SCHEMA_SQL)?;
        self.conn.execute(
            "INSERT INTO schema_meta(version) VALUES (?1)",
            params![SCHEMA_VERSION],
        )?;
        Ok(())
    }

    /// Every indexed file's prior state, keyed by repo-relative path (R2).
    pub fn file_states(&self) -> rusqlite::Result<HashMap<String, PrevState>> {
        let mut stmt = self
            .conn
            .prepare("SELECT id, path, hash, size, mtime_ns FROM files")?;
        let rows = stmt.query_map([], |r| {
            Ok((
                r.get::<_, i64>(0)?,
                r.get::<_, String>(1)?,
                r.get::<_, String>(2)?,
                r.get::<_, i64>(3)?,
                r.get::<_, i64>(4)?,
            ))
        })?;
        let mut map = HashMap::new();
        for row in rows {
            let (id, path, hash, size, mtime_ns) = row?;
            map.insert(
                path,
                PrevState {
                    id,
                    hash,
                    size: size as u64,
                    mtime_ns,
                },
            );
        }
        Ok(map)
    }

    /// Insert or update a file's tracking row, returning its stable id.
    pub fn upsert_file(
        &self,
        path: &str,
        hash: &str,
        size: u64,
        mtime_ns: i64,
    ) -> rusqlite::Result<i64> {
        self.conn.execute(
            "INSERT INTO files(path, hash, size, mtime_ns) VALUES (?1, ?2, ?3, ?4)
             ON CONFLICT(path) DO UPDATE SET hash = excluded.hash,
                                             size = excluded.size,
                                             mtime_ns = excluded.mtime_ns",
            params![path, hash, size as i64, mtime_ns],
        )?;
        self.conn
            .query_row("SELECT id FROM files WHERE path = ?1", [path], |r| r.get(0))
    }

    /// Update only a file's size/mtime after a pure mtime bump (unchanged
    /// content) — no facts change, so no re-parse is needed (R2).
    pub fn touch_file_meta(&self, path: &str, size: u64, mtime_ns: i64) -> rusqlite::Result<()> {
        self.conn.execute(
            "UPDATE files SET size = ?2, mtime_ns = ?3 WHERE path = ?1",
            params![path, size as i64, mtime_ns],
        )?;
        Ok(())
    }

    /// Replace a file's fact rows in place: stale symbol/reference/import/scope
    /// rows are deleted, then the fresh extraction is inserted. Keyed per
    /// `file_id`, so a re-parse never accumulates duplicate rows (R9).
    pub fn replace_facts(&self, file_id: i64, result: &ExtractResult) -> rusqlite::Result<()> {
        self.conn
            .execute("DELETE FROM symbols WHERE file_id = ?1", [file_id])?;
        self.conn
            .execute("DELETE FROM refs WHERE file_id = ?1", [file_id])?;
        self.conn
            .execute("DELETE FROM imports WHERE file_id = ?1", [file_id])?;
        self.conn
            .execute("DELETE FROM scopes WHERE file_id = ?1", [file_id])?;

        for s in &result.symbols {
            self.conn.execute(
                "INSERT INTO symbols(file_id, kind, name, qpath, signature, docstring,
                    full_start_byte, full_end_byte, ident_start_byte, ident_end_byte,
                    parent, body_hash, body_tokens)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13)",
                params![
                    file_id,
                    s.kind.as_str(),
                    s.name,
                    s.qpath,
                    s.signature,
                    s.docstring,
                    s.full_span.start_byte as i64,
                    s.full_span.end_byte as i64,
                    s.ident_span.start_byte as i64,
                    s.ident_span.end_byte as i64,
                    s.parent,
                    s.body_hash,
                    s.body_tokens.join(TOKEN_SEP),
                ],
            )?;
        }
        for rf in &result.references {
            self.conn.execute(
                "INSERT INTO refs(file_id, name, kind, row, col, byte)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
                params![
                    file_id,
                    rf.name,
                    rf.kind.as_str(),
                    rf.location.point.row as i64,
                    rf.location.point.column as i64,
                    rf.location.byte as i64,
                ],
            )?;
        }
        for im in &result.imports {
            self.conn.execute(
                "INSERT INTO imports(file_id, source, module, name, row, col, byte)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
                params![
                    file_id,
                    im.source,
                    im.module,
                    im.name,
                    im.location.point.row as i64,
                    im.location.point.column as i64,
                    im.location.byte as i64,
                ],
            )?;
        }
        for sc in &result.scopes {
            self.conn.execute(
                "INSERT INTO scopes(file_id, name, def_row, def_col, def_byte,
                    scope_start_byte, scope_end_byte)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
                params![
                    file_id,
                    sc.name,
                    sc.def_location.point.row as i64,
                    sc.def_location.point.column as i64,
                    sc.def_location.byte as i64,
                    sc.scope.start_byte as i64,
                    sc.scope.end_byte as i64,
                ],
            )?;
        }
        Ok(())
    }

    /// Purge a removed file's tracking row and all its facts (R2 deletion
    /// detection).
    pub fn delete_file(&self, path: &str) -> rusqlite::Result<()> {
        let id: Option<i64> = self
            .conn
            .query_row("SELECT id FROM files WHERE path = ?1", [path], |r| r.get(0))
            .optional()?;
        if let Some(id) = id {
            self.conn
                .execute("DELETE FROM symbols WHERE file_id = ?1", [id])?;
            self.conn
                .execute("DELETE FROM refs WHERE file_id = ?1", [id])?;
            self.conn
                .execute("DELETE FROM imports WHERE file_id = ?1", [id])?;
            self.conn
                .execute("DELETE FROM scopes WHERE file_id = ?1", [id])?;
            self.conn.execute("DELETE FROM files WHERE id = ?1", [id])?;
        }
        Ok(())
    }

    /// The timestamp (ns since the epoch) of the last completed sync — the
    /// racy-edit guard's reference point (R2).
    pub fn last_sync(&self) -> rusqlite::Result<Option<i64>> {
        self.conn
            .query_row("SELECT last_sync_ns FROM sync_meta WHERE id = 0", [], |r| {
                r.get(0)
            })
            .optional()
    }

    pub fn set_last_sync(&self, ns: i64) -> rusqlite::Result<()> {
        self.conn.execute(
            "INSERT INTO sync_meta(id, last_sync_ns) VALUES (0, ?1)
             ON CONFLICT(id) DO UPDATE SET last_sync_ns = ?1",
            [ns],
        )?;
        Ok(())
    }

    fn count(&self, sql: &str, path: &str) -> rusqlite::Result<usize> {
        let n: i64 = self.conn.query_row(sql, [path], |r| r.get(0))?;
        Ok(n as usize)
    }

    pub fn symbol_count_for_path(&self, path: &str) -> rusqlite::Result<usize> {
        self.count(
            "SELECT COUNT(*) FROM symbols s JOIN files f ON s.file_id = f.id WHERE f.path = ?1",
            path,
        )
    }

    pub fn imports_count_for_path(&self, path: &str) -> rusqlite::Result<usize> {
        self.count(
            "SELECT COUNT(*) FROM imports i JOIN files f ON i.file_id = f.id WHERE f.path = ?1",
            path,
        )
    }

    pub fn references_count_for_path(&self, path: &str) -> rusqlite::Result<usize> {
        self.count(
            "SELECT COUNT(*) FROM refs r JOIN files f ON r.file_id = f.id WHERE f.path = ?1",
            path,
        )
    }

    pub fn total_symbols(&self) -> rusqlite::Result<usize> {
        let n: i64 = self
            .conn
            .query_row("SELECT COUNT(*) FROM symbols", [], |r| r.get(0))?;
        Ok(n as usize)
    }

    /// Every indexed file path (repo-relative).
    pub fn indexed_paths(&self) -> rusqlite::Result<Vec<String>> {
        let mut stmt = self.conn.prepare("SELECT path FROM files ORDER BY path")?;
        let rows = stmt.query_map([], |r| r.get::<_, String>(0))?;
        rows.collect()
    }

    /// Every indexed symbol, joined to its owning file path, ordered
    /// deterministically (by path, then source order) so query output is
    /// rebuild-stable (C4).
    pub fn all_symbols(&self) -> rusqlite::Result<Vec<SymbolRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT s.id, s.kind, s.name, s.qpath, s.signature, s.docstring, s.parent,
                    f.path, s.full_start_byte, s.full_end_byte, s.ident_start_byte, s.body_hash
             FROM symbols s JOIN files f ON s.file_id = f.id
             ORDER BY f.path, s.full_start_byte",
        )?;
        let rows = stmt.query_map([], |r| {
            Ok(SymbolRow {
                id: r.get(0)?,
                kind: r.get(1)?,
                name: r.get(2)?,
                qpath: r.get(3)?,
                signature: r.get(4)?,
                docstring: r.get(5)?,
                parent: r.get(6)?,
                path: r.get(7)?,
                full_start_byte: r.get::<_, i64>(8)? as usize,
                full_end_byte: r.get::<_, i64>(9)? as usize,
                ident_start_byte: r.get::<_, i64>(10)? as usize,
                body_hash: r.get(11)?,
            })
        })?;
        rows.collect()
    }

    /// Every reference occurrence joined to its owning file path, in the index's
    /// deterministic (path, source) order — the heuristic-match input for
    /// `ctx refs` (R10).
    pub fn all_references(&self) -> rusqlite::Result<Vec<RefRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT r.name, r.kind, f.path, r.row, r.byte
             FROM refs r JOIN files f ON r.file_id = f.id
             ORDER BY f.path, r.byte",
        )?;
        let rows = stmt.query_map([], |r| {
            Ok(RefRow {
                name: r.get(0)?,
                kind: r.get(1)?,
                path: r.get(2)?,
                row: r.get::<_, i64>(3)? as usize,
                byte: r.get::<_, i64>(4)? as usize,
            })
        })?;
        rows.collect()
    }

    /// Every import edge joined to its owning file path, in deterministic order —
    /// the raw material for `ctx deps` (R9).
    pub fn all_imports(&self) -> rusqlite::Result<Vec<ImportRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT i.source, i.module, f.path, i.row
             FROM imports i JOIN files f ON i.file_id = f.id
             ORDER BY f.path, i.byte",
        )?;
        let rows = stmt.query_map([], |r| {
            Ok(ImportRow {
                source: r.get(0)?,
                module: r.get(1)?,
                path: r.get(2)?,
                row: r.get::<_, i64>(3)? as usize,
            })
        })?;
        rows.collect()
    }

    /// Every locals-query scope binding joined to its owning file path — the
    /// shadowing input for scope-aware `ctx refs` (R10).
    pub fn all_scopes(&self) -> rusqlite::Result<Vec<ScopeRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT sc.name, f.path, sc.scope_start_byte, sc.scope_end_byte
             FROM scopes sc JOIN files f ON sc.file_id = f.id
             ORDER BY f.path, sc.scope_start_byte",
        )?;
        let rows = stmt.query_map([], |r| {
            Ok(ScopeRow {
                name: r.get(0)?,
                path: r.get(1)?,
                scope_start_byte: r.get::<_, i64>(2)? as usize,
                scope_end_byte: r.get::<_, i64>(3)? as usize,
            })
        })?;
        rows.collect()
    }

    /// Reference occurrences grouped by referenced name — the reference-graph
    /// importance weight `ctx map` ranks by (R8).
    pub fn reference_counts(&self) -> rusqlite::Result<HashMap<String, usize>> {
        let mut stmt = self
            .conn
            .prepare("SELECT name, COUNT(*) FROM refs GROUP BY name")?;
        let rows = stmt.query_map([], |r| {
            Ok((r.get::<_, String>(0)?, r.get::<_, i64>(1)? as usize))
        })?;
        let mut map = HashMap::new();
        for row in rows {
            let (name, count) = row?;
            map.insert(name, count);
        }
        Ok(map)
    }

    /// C2 body hash of the unique symbol at `qpath`, or `None` when no symbol
    /// resolves — the current side of R12's freshness derivation.
    pub fn body_hash_for_qpath(&self, qpath: &str) -> rusqlite::Result<Option<String>> {
        self.conn
            .query_row(
                "SELECT body_hash FROM symbols WHERE qpath = ?1 LIMIT 1",
                [qpath],
                |r| r.get(0),
            )
            .optional()
    }

    /// Rebuild the derived note cache from the note files (R12): each note's
    /// freshness re-derives against the just-synced symbols, so the cache is a
    /// pure function of the note files plus the working tree.
    pub fn refresh_notes(&self, notes: &[crate::notes::Note]) -> rusqlite::Result<()> {
        self.conn.execute("DELETE FROM notes", [])?;
        for n in notes {
            let current = self.body_hash_for_qpath(&n.anchor_path)?;
            let fresh = crate::notes::freshness::is_fresh(current.as_deref(), &n.anchor_hash);
            self.conn.execute(
                "INSERT OR REPLACE INTO notes
                    (id, rel_path, anchor_path, anchor_hash, kind, author, created, body, fresh)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
                params![
                    n.id,
                    n.rel_path,
                    n.anchor_path,
                    n.anchor_hash,
                    n.kind,
                    n.author,
                    n.created,
                    n.body,
                    fresh as i64,
                ],
            )?;
        }
        Ok(())
    }

    /// Every cached note, joined to the current file of its anchored symbol
    /// (`NULL` when the anchor no longer resolves), ordered deterministically —
    /// the raw material for `ctx notes list`/`ctx notes <symbol>` (R12).
    pub fn all_notes(&self) -> rusqlite::Result<Vec<NoteRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT n.id, n.rel_path, n.anchor_path, n.kind, n.author, n.created, n.body,
                    n.fresh, f.path
             FROM notes n
             LEFT JOIN symbols s ON s.qpath = n.anchor_path
             LEFT JOIN files f ON f.id = s.file_id
             GROUP BY n.id
             ORDER BY n.anchor_path, n.id",
        )?;
        let rows = stmt.query_map([], |r| {
            Ok(NoteRow {
                id: r.get(0)?,
                rel_path: r.get(1)?,
                anchor_path: r.get(2)?,
                kind: r.get(3)?,
                author: r.get(4)?,
                created: r.get(5)?,
                body: r.get(6)?,
                fresh: r.get::<_, i64>(7)? != 0,
                file: r.get(8)?,
            })
        })?;
        rows.collect()
    }

    /// The C10 note marker for a symbol: `Some((count, any_stale))` when the
    /// symbol carries notes, `None` otherwise. Counts notes anchored to the
    /// symbol's qualified path in the derived cache (R12/C10).
    pub fn note_marker(&self, symbol_id: i64) -> Option<(usize, bool)> {
        let qpath: String = self
            .conn
            .query_row(
                "SELECT qpath FROM symbols WHERE id = ?1",
                [symbol_id],
                |r| r.get(0),
            )
            .optional()
            .ok()
            .flatten()?;
        let (count, stale): (i64, i64) = self
            .conn
            .query_row(
                "SELECT COUNT(*), COALESCE(SUM(CASE WHEN fresh = 0 THEN 1 ELSE 0 END), 0)
                 FROM notes WHERE anchor_path = ?1",
                [qpath],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .ok()?;
        if count == 0 {
            None
        } else {
            Some((count as usize, stale > 0))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn note_marker_returns_none_when_no_notes_exist() {
        let dir = tempfile::tempdir().unwrap();
        let store = IndexStore::open(dir.path()).unwrap();
        assert_eq!(store.note_marker(1), None);
        assert_eq!(store.note_marker(999), None);
    }
}
