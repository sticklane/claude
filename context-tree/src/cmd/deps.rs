//! `ctx deps <path> [--reverse]` — module-level import edges out of (default) or
//! into (`--reverse`) a path subtree (R9). Reads edges straight from the index;
//! runs the R3 staleness sweep first via [`load_index`].

use crate::cmd::load_index;
use crate::index::ImportRow;
use serde_json::json;
use std::collections::HashSet;
use std::process::ExitCode;

/// Parsed `ctx deps` arguments.
pub struct Args {
    pub path: String,
    pub reverse: bool,
    pub json: bool,
    pub no_sync: bool,
}

/// Does the indexed file `path` fall within the requested `scope`? A scope of
/// `.` (or empty) matches everything; otherwise an exact path or a `<scope>/…`
/// directory prefix matches. (Mirrors `ctx tree`'s scope test.)
fn in_scope(path: &str, scope: &str) -> bool {
    let scope = scope.strip_prefix("./").unwrap_or(scope);
    if scope.is_empty() || scope == "." {
        return true;
    }
    path == scope || path.starts_with(&format!("{scope}/"))
}

/// Normalize an import target string to the dotted module form used to compare
/// against a file's module identity: drop a leading `./` or `.`, map path
/// separators to `.`.
fn norm_module(m: &str) -> String {
    m.trim_start_matches("./")
        .trim_start_matches('.')
        .replace(['/', '\\'], ".")
}

/// The set of module identifiers a repo-relative file could be imported as: its
/// dotted no-extension path (`pkg/util.py` → `pkg.util`), the raw no-extension
/// path (`pkg/util`), and its bare basename (`util`). Import targets are raw,
/// unresolved strings (R9), so reverse resolution matches any of these forms.
fn file_module_keys(rel: &str) -> Vec<String> {
    let no_ext = match rel.rsplit_once('.') {
        Some((stem, _)) => stem,
        None => rel,
    };
    let dotted = no_ext.replace(['/', '\\'], ".");
    let base = no_ext
        .rsplit(['/', '\\'])
        .next()
        .unwrap_or(no_ext)
        .to_string();
    let mut keys = vec![dotted, no_ext.to_string(), base];
    keys.sort();
    keys.dedup();
    keys
}

pub fn run(args: Args) -> ExitCode {
    let (out, code) = render(&args);
    print!("{out}");
    code
}

/// The exact stdout `run` would print, paired with the exit code. Shared with
/// the MCP wrapper (R15); error diagnostics still go to stderr via `eprintln!`.
pub fn render(args: &Args) -> (String, ExitCode) {
    let (_root, store) = match load_index(args.no_sync) {
        Ok(v) => v,
        Err(code) => return (String::new(), code),
    };
    let imports = match store.all_imports() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx deps: {e}");
            return (String::new(), ExitCode::FAILURE);
        }
    };

    // Reverse resolution needs the module identity of every in-scope file, so an
    // import whose (raw) target resolves to one of them counts as an edge in.
    let scope_keys: HashSet<String> = if args.reverse {
        let paths = match store.indexed_paths() {
            Ok(v) => v,
            Err(e) => {
                eprintln!("ctx deps: {e}");
                return (String::new(), ExitCode::FAILURE);
            }
        };
        paths
            .iter()
            .filter(|p| in_scope(p, &args.path))
            .flat_map(|p| file_module_keys(p))
            .collect()
    } else {
        HashSet::new()
    };

    let mut edges: Vec<&ImportRow> = imports
        .iter()
        .filter(|im| {
            if args.reverse {
                scope_keys.contains(&norm_module(&im.module))
            } else {
                in_scope(&im.path, &args.path)
            }
        })
        .collect();
    edges.sort_by(|a, b| {
        a.source
            .cmp(&b.source)
            .then(a.module.cmp(&b.module))
            .then(a.path.cmp(&b.path))
            .then(a.row.cmp(&b.row))
    });
    // Collapse duplicate (source -> module) edges to one row apiece.
    edges.dedup_by(|a, b| a.source == b.source && a.module == b.module);

    if args.json {
        let payload = json!({
            "path": args.path,
            "reverse": args.reverse,
            "edges": edges.iter().map(|e| json!({
                "from": e.source,
                "module": e.module,
                "file": e.path,
                "line": e.row + 1,
            })).collect::<Vec<_>>(),
        });
        (format!("{payload}\n"), ExitCode::SUCCESS)
    } else {
        let mut out = String::new();
        for e in &edges {
            out.push_str(&format!("{} -> {}\n", e.source, e.module));
        }
        (out, ExitCode::SUCCESS)
    }
}
