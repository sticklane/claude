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
