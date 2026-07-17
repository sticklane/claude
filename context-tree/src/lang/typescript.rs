//! TypeScript/TSX/JavaScript extractor. One registration claims `.ts`, `.tsx`,
//! and `.js` and dispatches to the matching tree-sitter grammar by extension,
//! all counted under the single `typescript` coverage bucket.
//!
//! TS/JS have no C1 module concept, so the module component is the
//! repo-relative file path (slashes → `.`, extension dropped). The shipped TS
//! locals query is parameter-only, so [`LOCALS_QUERY`] is authored here
//! (function/method scopes + `variable_declarator` bindings) — its node kinds
//! are shared across all three grammars — so the shadowing R10 `Scope` fact
//! works for `.ts`/`.tsx`/`.js` alike.

use crate::extract::{ExtractResult, ExtractorRegistration, LanguageExtractor};
use crate::facts::{Import, Location, Point, RefKind, Reference, Scope, Span, Symbol, SymbolKind};
use crate::hash;
use crate::path;
use tree_sitter::{Node, Parser, Query, QueryCursor, StreamingIterator};

const LOCALS_QUERY: &str = r#"
[
  (statement_block)
  (function_declaration)
  (function_expression)
  (arrow_function)
  (method_definition)
] @local.scope

(variable_declarator name: (identifier) @local.definition)
"#;

pub struct TypescriptExtractor;

impl TypescriptExtractor {
    pub fn new() -> Self {
        Self
    }
}

impl Default for TypescriptExtractor {
    fn default() -> Self {
        Self::new()
    }
}

inventory::submit! {
    ExtractorRegistration {
        language: "typescript",
        extensions: &["ts", "tsx", "js"],
        make: || Box::new(TypescriptExtractor::new()),
    }
}

/// C1 module for a language with no module concept: repo-relative file path
/// with the extension dropped and slashes mapped to `.`.
fn file_module(rel_path: &str) -> String {
    let without_ext = match rel_path.rsplit_once('.') {
        Some((stem, _ext)) => stem,
        None => rel_path,
    };
    without_ext.replace(['/', '\\'], ".")
}

fn language_for_ext(ext: &str) -> tree_sitter::Language {
    match ext {
        "tsx" => tree_sitter_typescript::LANGUAGE_TSX.into(),
        "js" => tree_sitter_javascript::LANGUAGE.into(),
        _ => tree_sitter_typescript::LANGUAGE_TYPESCRIPT.into(),
    }
}

fn point_of(node: Node) -> Point {
    let p = node.start_position();
    Point {
        row: p.row,
        column: p.column,
    }
}

fn span_of(node: Node) -> Span {
    let s = node.start_position();
    let e = node.end_position();
    Span {
        start: Point {
            row: s.row,
            column: s.column,
        },
        end: Point {
            row: e.row,
            column: e.column,
        },
        start_byte: node.start_byte(),
        end_byte: node.end_byte(),
    }
}

fn location_of(node: Node) -> Location {
    Location {
        point: point_of(node),
        byte: node.start_byte(),
    }
}

fn text<'a>(node: Node, source: &'a [u8]) -> &'a str {
    node.utf8_text(source).unwrap_or("")
}

fn each_node(node: Node, f: &mut impl FnMut(Node)) {
    f(node);
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        each_node(child, f);
    }
}

/// The `/** … */` (JSDoc/TSDoc) block comment immediately preceding a
/// definition — reaching over an `export_statement` wrapper — cleaned of its
/// comment markers. Empty when none.
fn docstring(node: Node, source: &[u8]) -> String {
    let anchor = match node.parent() {
        Some(p) if p.kind() == "export_statement" => p,
        _ => node,
    };
    let Some(prev) = anchor.prev_sibling() else {
        return String::new();
    };
    if prev.kind() != "comment" {
        return String::new();
    }
    let raw = text(prev, source);
    if !raw.trim_start().starts_with("/**") {
        return String::new();
    }
    let stripped = raw.trim().trim_start_matches("/**").trim_end_matches("*/");
    stripped
        .lines()
        .map(|l| l.trim().trim_start_matches('*').trim())
        .filter(|l| !l.is_empty())
        .collect::<Vec<_>>()
        .join("\n")
}

fn symbol_kind(kind: &str) -> Option<SymbolKind> {
    match kind {
        "function_declaration" | "generator_function_declaration" => Some(SymbolKind::Function),
        "class_declaration" | "abstract_class_declaration" => Some(SymbolKind::Class),
        "method_definition" => Some(SymbolKind::Method),
        "interface_declaration" => Some(SymbolKind::Interface),
        "enum_declaration" => Some(SymbolKind::Enum),
        "type_alias_declaration" => Some(SymbolKind::TypeAlias),
        "internal_module" | "module" => Some(SymbolKind::Module),
        _ => None,
    }
}

/// Whether a symbol node is also a container others nest inside.
fn is_container(kind: &str) -> bool {
    matches!(
        kind,
        "function_declaration"
            | "class_declaration"
            | "abstract_class_declaration"
            | "internal_module"
            | "module"
    )
}

fn collect_defs(
    node: Node,
    module: &str,
    containers: &mut Vec<String>,
    source: &[u8],
    out: &mut Vec<Symbol>,
) {
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        let Some(sym_kind) = symbol_kind(child.kind()) else {
            collect_defs(child, module, containers, source, out);
            continue;
        };
        let Some(name_node) = child.child_by_field_name("name") else {
            collect_defs(child, module, containers, source, out);
            continue;
        };
        let name = text(name_node, source).to_string();
        let qpath = path::build_qpath(module, containers, &name);
        let body = child.child_by_field_name("body");
        let signature = match body {
            Some(b) => String::from_utf8_lossy(&source[child.start_byte()..b.start_byte()])
                .trim()
                .to_string(),
            None => text(child, source).trim().to_string(),
        };
        let parent = if containers.is_empty() {
            None
        } else {
            Some(path::build_qpath(module, containers, ""))
        };
        let full = (child.start_byte(), child.end_byte());
        let ident = (name_node.start_byte(), name_node.end_byte());
        out.push(Symbol {
            kind: sym_kind,
            name: name.clone(),
            qpath,
            signature,
            docstring: docstring(child, source),
            full_span: span_of(child),
            ident_span: span_of(name_node),
            parent,
            body_hash: hash::body_hash(source, full, ident),
            body_tokens: hash::body_tokens(source, full, ident),
        });
        if is_container(child.kind()) {
            containers.push(name);
            collect_defs(child, module, containers, source, out);
            containers.pop();
        } else {
            collect_defs(child, module, containers, source, out);
        }
    }
}

/// The terminal callee name + location for a `call_expression`'s function.
fn callee(func: Node, source: &[u8]) -> Option<(String, Location)> {
    match func.kind() {
        "identifier" => Some((text(func, source).to_string(), location_of(func))),
        "member_expression" => {
            let prop = func.child_by_field_name("property")?;
            Some((text(prop, source).to_string(), location_of(prop)))
        }
        _ => None,
    }
}

fn classify_identifier(node: Node) -> Option<RefKind> {
    let parent = node.parent()?;
    let is_field = |field: &str| parent.child_by_field_name(field) == Some(node);
    match parent.kind() {
        "function_declaration"
        | "generator_function_declaration"
        | "class_declaration"
        | "abstract_class_declaration"
        | "method_definition"
        | "interface_declaration"
        | "enum_declaration"
        | "type_alias_declaration"
        | "internal_module"
        | "module"
            if is_field("name") =>
        {
            None
        }
        "call_expression" if is_field("function") => None,
        "member_expression" if is_field("property") => None,
        "variable_declarator" if is_field("name") => Some(RefKind::Write),
        "assignment_expression" if is_field("left") => Some(RefKind::Write),
        "import_specifier" | "namespace_import" | "import_clause" | "required_parameter"
        | "optional_parameter" | "formal_parameters" => None,
        _ => Some(RefKind::Read),
    }
}

/// The string literal's inner content (quotes stripped).
fn string_content(node: Node, source: &[u8]) -> String {
    let mut cursor = node.walk();
    for child in node.named_children(&mut cursor) {
        if child.kind() == "string_fragment" {
            return text(child, source).to_string();
        }
    }
    text(node, source)
        .trim_matches(['"', '\'', '`'])
        .to_string()
}

fn collect_imports(n: Node, module: &str, source: &[u8], out: &mut Vec<Import>) {
    let Some(src_node) = n.child_by_field_name("source") else {
        return;
    };
    let from = string_content(src_node, source);
    let mut pushed = false;
    each_node(n, &mut |m| match m.kind() {
        "import_specifier" => {
            let name = m
                .child_by_field_name("name")
                .map(|nm| text(nm, source).to_string());
            if let Some(name) = name {
                out.push(Import {
                    source: module.to_string(),
                    module: from.clone(),
                    name: Some(name),
                    location: location_of(m),
                });
                pushed = true;
            }
        }
        "namespace_import" => {
            out.push(Import {
                source: module.to_string(),
                module: from.clone(),
                name: Some("*".to_string()),
                location: location_of(m),
            });
            pushed = true;
        }
        _ => {}
    });
    if !pushed {
        // A default (`import foo from`) or side-effect (`import "x"`) import.
        out.push(Import {
            source: module.to_string(),
            module: from,
            name: None,
            location: location_of(n),
        });
    }
}

fn extract_scopes(language: &tree_sitter::Language, root: Node, source: &[u8]) -> Vec<Scope> {
    let Ok(query) = Query::new(language, LOCALS_QUERY) else {
        return Vec::new();
    };
    let names = query.capture_names();
    let mut scope_spans: Vec<Span> = Vec::new();
    let mut defs: Vec<(String, Location, usize)> = Vec::new();
    let mut cursor = QueryCursor::new();
    let mut matches = cursor.matches(&query, root, source);
    while let Some(m) = matches.next() {
        for cap in m.captures {
            match names[cap.index as usize] {
                "local.scope" => scope_spans.push(span_of(cap.node)),
                "local.definition" => defs.push((
                    text(cap.node, source).to_string(),
                    location_of(cap.node),
                    cap.node.start_byte(),
                )),
                _ => {}
            }
        }
    }
    let mut out = Vec::new();
    for (name, def_location, byte) in defs {
        let innermost = scope_spans
            .iter()
            .filter(|s| byte >= s.start_byte && byte < s.end_byte)
            .max_by_key(|s| s.start_byte);
        if let Some(scope) = innermost {
            out.push(Scope {
                name,
                def_location,
                scope: *scope,
            });
        }
    }
    out
}

impl LanguageExtractor for TypescriptExtractor {
    fn language(&self) -> &'static str {
        "typescript"
    }

    fn extensions(&self) -> &'static [&'static str] {
        &["ts", "tsx", "js"]
    }

    fn extract(&self, rel_path: &str, source: &[u8]) -> ExtractResult {
        let module = file_module(rel_path);
        let ext = rel_path.rsplit('.').next().unwrap_or("");
        let language = language_for_ext(ext);
        let mut parser = Parser::new();
        if parser.set_language(&language).is_err() {
            return ExtractResult {
                parse_failed: true,
                ..Default::default()
            };
        }
        let Some(tree) = parser.parse(source, None) else {
            return ExtractResult {
                parse_failed: true,
                ..Default::default()
            };
        };
        let root = tree.root_node();
        let parse_failed = root.has_error();

        let mut symbols = Vec::new();
        let mut containers = Vec::new();
        collect_defs(root, &module, &mut containers, source, &mut symbols);
        let qpaths: Vec<String> = symbols.iter().map(|s| s.qpath.clone()).collect();
        let disambiguated = path::disambiguate(&qpaths);
        for (sym, q) in symbols.iter_mut().zip(disambiguated) {
            sym.qpath = q;
        }

        let mut references = Vec::new();
        let mut imports = Vec::new();
        each_node(root, &mut |n| match n.kind() {
            "call_expression" => {
                if let Some(func) = n.child_by_field_name("function")
                    && let Some((name, location)) = callee(func, source)
                {
                    references.push(Reference {
                        name,
                        location,
                        kind: RefKind::Call,
                    });
                }
            }
            "identifier" => {
                if let Some(kind) = classify_identifier(n) {
                    references.push(Reference {
                        name: text(n, source).to_string(),
                        location: location_of(n),
                        kind,
                    });
                }
            }
            "import_statement" => collect_imports(n, &module, source, &mut imports),
            _ => {}
        });

        let scopes = extract_scopes(&language, root, source);

        ExtractResult {
            symbols,
            references,
            imports,
            scopes,
            parse_failed,
        }
    }
}
