//! C1 qualified-symbol-path construction and C3 suffix resolution.

/// Derive the Python-style dotted module component from a repo-relative path:
/// drop the extension, map `/` to `.`, and collapse a `__init__` package file
/// to its directory (`pkg/__init__.py` -> `pkg`).
pub fn python_module(rel_path: &str) -> String {
    let without_ext = rel_path.strip_suffix(".py").unwrap_or(rel_path);
    let dotted = without_ext.replace(['/', '\\'], ".");
    match dotted.strip_suffix(".__init__") {
        Some(pkg) => pkg.to_string(),
        None => {
            if dotted == "__init__" {
                String::new()
            } else {
                dotted
            }
        }
    }
}

/// Join a module component, a container chain, and a terminal name into a C1
/// path (`<module>.<container>…<name>`). Empty components are skipped so a
/// module-less or container-less symbol renders cleanly.
pub fn build_qpath(module: &str, containers: &[String], name: &str) -> String {
    let mut parts: Vec<&str> = Vec::new();
    if !module.is_empty() {
        parts.push(module);
    }
    for c in containers {
        if !c.is_empty() {
            parts.push(c.as_str());
        }
    }
    if !name.is_empty() {
        parts.push(name);
    }
    parts.join(".")
}

/// Append `#<n>` (1-based source order) to any qualified paths that collide
/// within the same module, leaving unique paths untouched (C1's ordinal rule).
/// `paths` is in source order; returns the disambiguated paths in that order.
pub fn disambiguate(paths: &[String]) -> Vec<String> {
    let mut counts: std::collections::HashMap<&str, usize> = std::collections::HashMap::new();
    for p in paths {
        *counts.entry(p.as_str()).or_insert(0) += 1;
    }
    let mut seen: std::collections::HashMap<&str, usize> = std::collections::HashMap::new();
    let mut out = Vec::with_capacity(paths.len());
    for p in paths {
        if counts[p.as_str()] > 1 {
            let n = seen.entry(p.as_str()).or_insert(0);
            *n += 1;
            out.push(format!("{p}#{n}"));
        } else {
            out.push(p.clone());
        }
    }
    out
}

/// A file-scoped selector: the bare name (or C1 qpath suffix) to resolve, plus
/// the owning-file constraints that narrow the C3 candidate set. Parsed once
/// from a `<path>:<name>` query argument and any repeated `--in <path-prefix>`
/// flags, then reused by every verb so selector semantics live in one place.
pub struct Selector {
    /// The name / qpath suffix handed to [`resolve_suffix`].
    pub name: String,
    /// Exact owning-file path from the `<path>:<name>` form (`None` = bare name).
    file: Option<String>,
    /// Owning-file path-prefix constraints from `--in` (any-of; empty = no filter).
    prefixes: Vec<String>,
}

impl Selector {
    /// Parse a query argument and the `--in` prefixes into a [`Selector`].
    /// A bare name with no `--in` flags preserves the existing behavior exactly:
    /// `name` is the whole query and [`accepts_file`](Self::accepts_file) is
    /// always true.
    pub fn parse(query: &str, in_prefixes: &[String]) -> Selector {
        let (file, name) = split_file_selector(query);
        Selector {
            name: name.to_string(),
            file: file.map(str::to_string),
            prefixes: in_prefixes.to_vec(),
        }
    }

    /// True when a symbol owned by `path` satisfies both file constraints: the
    /// exact `<path>:<name>` file (if given) AND at least one `--in` prefix (if
    /// any given). With neither constraint, every file is accepted.
    pub fn accepts_file(&self, path: &str) -> bool {
        if let Some(f) = &self.file
            && path != f
        {
            return false;
        }
        if !self.prefixes.is_empty() && !self.prefixes.iter().any(|p| path_under_prefix(path, p)) {
            return false;
        }
        true
    }
}

/// Split a `<path>:<name>` file-scoped selector into `(Some(path), name)`, or
/// `(None, query)` for a bare name. The split fires only when the text before
/// the LAST `:` looks like a real path component — non-empty, free of any other
/// `:`, and containing a `/` or a `.` — so a bare name, a dotted qpath suffix,
/// or a `foo::bar` never splits.
fn split_file_selector(query: &str) -> (Option<&str>, &str) {
    if let Some(idx) = query.rfind(':') {
        let (before, after) = (&query[..idx], &query[idx + 1..]);
        let path_like = !before.is_empty()
            && !before.contains(':')
            && (before.contains('/') || before.contains('.'));
        if path_like && !after.is_empty() {
            return (Some(before), after);
        }
    }
    (None, query)
}

/// True when `path` equals `prefix` or lies under it on a `/` boundary, so
/// `go/cmd` matches `go/cmd/main.go` but not `go/cmdx/main.go`.
fn path_under_prefix(path: &str, prefix: &str) -> bool {
    let prefix = prefix.trim_end_matches('/');
    path == prefix
        || path
            .strip_prefix(prefix)
            .is_some_and(|rest| rest.starts_with('/'))
}

/// C3 suffix resolution: return every path in `paths` that the `query` matches
/// as an exact path or as a whole-trailing-component suffix on `.` boundaries.
/// `Handler` matches `app.Handler` but not `app.AuthHandler`.
pub fn resolve_suffix<'a>(paths: &'a [String], query: &str) -> Vec<&'a str> {
    // Strip any C1 ordinal suffix when comparing components.
    let base = |p: &str| -> String { p.split('#').next().unwrap_or(p).to_string() };
    let query_comps: Vec<&str> = query.split('.').collect();
    paths
        .iter()
        .filter(|p| {
            let b = base(p);
            if b == query {
                return true;
            }
            let comps: Vec<&str> = b.split('.').collect();
            comps.len() >= query_comps.len()
                && comps[comps.len() - query_comps.len()..] == query_comps[..]
        })
        .map(|p| p.as_str())
        .collect()
}

#[cfg(test)]
mod selector_tests {
    use super::*;

    #[test]
    fn bare_name_leaves_name_whole_and_accepts_every_file() {
        let s = Selector::parse("rodSpecs", &[]);
        assert_eq!(s.name, "rodSpecs");
        assert!(s.accepts_file("go/cmd/mlhybrid/main.go"));
        assert!(s.accepts_file("anything/at/all.rs"));
    }

    #[test]
    fn dotted_qpath_suffix_without_colon_is_not_split() {
        let s = Selector::parse("main.rodSpecs", &[]);
        assert_eq!(s.name, "main.rodSpecs");
        assert!(s.accepts_file("go/cmd/mlhybrid/main.go"));
    }

    #[test]
    fn file_scoped_selector_splits_path_and_name_and_filters_by_exact_file() {
        let s = Selector::parse("go/cmd/mlhybrid/main.go:rodSpecs", &[]);
        assert_eq!(s.name, "rodSpecs");
        assert!(s.accepts_file("go/cmd/mlhybrid/main.go"));
        assert!(!s.accepts_file("go/cmd/mloverlay/main.go"));
    }

    #[test]
    fn rust_style_double_colon_never_splits() {
        // `foo::bar` before the last `:` is `foo:` which still holds a colon.
        let s = Selector::parse("foo::bar", &[]);
        assert_eq!(s.name, "foo::bar");
    }

    #[test]
    fn in_prefix_matches_on_directory_boundaries_only() {
        let s = Selector::parse("rodSpecs", &["go/cmd".to_string()]);
        assert_eq!(s.name, "rodSpecs");
        assert!(s.accepts_file("go/cmd/mlhybrid/main.go"));
        assert!(
            !s.accepts_file("go/cmdx/main.go"),
            "no boundary-crossing prefix"
        );
        assert!(!s.accepts_file("attic/go-cmd/main.go"));
    }

    #[test]
    fn multiple_in_prefixes_are_any_of() {
        let s = Selector::parse("rodSpecs", &["go/a".to_string(), "go/b".to_string()]);
        assert!(s.accepts_file("go/a/x.go"));
        assert!(s.accepts_file("go/b/y.go"));
        assert!(!s.accepts_file("go/c/z.go"));
    }

    #[test]
    fn exact_file_and_in_prefix_compose_conjunctively() {
        let s = Selector::parse("go/cmd/mlhybrid/main.go:rodSpecs", &["attic".to_string()]);
        // The exact file is under `go/`, not `attic/`, so nothing passes.
        assert!(!s.accepts_file("go/cmd/mlhybrid/main.go"));
        assert!(!s.accepts_file("attic/other.go"));
    }
}
