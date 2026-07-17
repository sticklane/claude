//! Go extractor: functions, methods (keyed under their receiver type), type
//! declarations (struct/interface/alias), and package-level const/var. The C1
//! module component is the Go **package** name — not the file path — so a file
//! move within a package leaves qualified paths unchanged (R13 identity).
//! C8 docstrings are the contiguous `//` doc-comment block. tree-sitter-go
//! ships no locals query, so no `Scope` facts (R10 fallback).

use crate::extract::{ExtractResult, ExtractorRegistration, LanguageExtractor};
use crate::facts::{Import, Location, Point, RefKind, Reference, Span, Symbol, SymbolKind};
use crate::hash;
use crate::path;
use tree_sitter::{Node, Parser};

pub struct GoExtractor {
    language: tree_sitter::Language,
}

impl GoExtractor {
    pub fn new() -> Self {
        Self {
            language: tree_sitter_go::LANGUAGE.into(),
        }
    }
}

impl Default for GoExtractor {
    fn default() -> Self {
        Self::new()
    }
}

inventory::submit! {
    ExtractorRegistration {
        language: "go",
        extensions: &["go"],
        make: || Box::new(GoExtractor::new()),
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

/// The package name from the `package_clause`, or the file-path fallback.
fn package_name(root: Node, rel_path: &str, source: &[u8]) -> String {
    let mut cursor = root.walk();
    for child in root.children(&mut cursor) {
        if child.kind() == "package_clause"
            && let Some(id) = child.named_child(0)
        {
            return text(id, source).to_string();
        }
    }
    rel_path
        .rsplit_once('.')
        .map(|(s, _)| s)
        .unwrap_or(rel_path)
        .replace(['/', '\\'], ".")
}

/// C8 Go doc comment: the contiguous `//` (or `/* */`) comment block whose last
/// line sits immediately above `decl`, joined and stripped of markers.
fn doc_comment(decl: Node, source: &[u8]) -> String {
    let mut lines: Vec<String> = Vec::new();
    let mut expected_row = decl.start_position().row;
    let mut cur = decl.prev_sibling();
    while let Some(c) = cur {
        if c.kind() != "comment" || c.end_position().row + 1 != expected_row {
            break;
        }
        let raw = text(c, source).trim();
        let cleaned = raw
            .trim_start_matches("//")
            .trim_start_matches("/*")
            .trim_end_matches("*/")
            .trim();
        lines.push(cleaned.to_string());
        expected_row = c.start_position().row;
        cur = c.prev_sibling();
    }
    lines.reverse();
    lines.join("\n")
}

/// One definition to record: its kind, the identifier node, the full node the
/// span/hash derive from, and its C8 doc.
struct GoDef<'a> {
    kind: SymbolKind,
    name_node: Node<'a>,
    full_node: Node<'a>,
    doc: String,
}

fn push_symbol(
    def: GoDef,
    package: &str,
    containers: &[String],
    source: &[u8],
    out: &mut Vec<Symbol>,
) {
    let name = text(def.name_node, source).to_string();
    let qpath = path::build_qpath(package, containers, &name);
    // A declaration with a `body` field (func/method) trims the signature to
    // its head; a spec (type/const/var) has none, so the whole node is it.
    let signature = match def.full_node.child_by_field_name("body") {
        Some(b) => String::from_utf8_lossy(&source[def.full_node.start_byte()..b.start_byte()])
            .trim()
            .to_string(),
        None => text(def.full_node, source).trim().to_string(),
    };
    let parent = if containers.is_empty() {
        None
    } else {
        Some(path::build_qpath(package, containers, ""))
    };
    let full = (def.full_node.start_byte(), def.full_node.end_byte());
    let ident = (def.name_node.start_byte(), def.name_node.end_byte());
    out.push(Symbol {
        kind: def.kind,
        name,
        qpath,
        signature,
        docstring: def.doc,
        full_span: span_of(def.full_node),
        ident_span: span_of(def.name_node),
        parent,
        body_hash: hash::body_hash(source, full, ident),
        body_tokens: hash::body_tokens(source, full, ident),
    });
}

/// The receiver type name of a `method_declaration` (`Widget` for both
/// `(w Widget)` and `(w *Widget)`).
fn receiver_type(method: Node, source: &[u8]) -> Option<String> {
    let recv = method.child_by_field_name("receiver")?;
    let mut found = None;
    each_node(recv, &mut |n| {
        if found.is_none() && n.kind() == "type_identifier" {
            found = Some(text(n, source).to_string());
        }
    });
    found
}

fn type_spec_kind(spec: Node) -> SymbolKind {
    match spec.child_by_field_name("type").map(|t| t.kind()) {
        Some("struct_type") => SymbolKind::Struct,
        Some("interface_type") => SymbolKind::Interface,
        _ => SymbolKind::TypeAlias,
    }
}

fn collect_defs(root: Node, package: &str, source: &[u8], out: &mut Vec<Symbol>) {
    let mut cursor = root.walk();
    for child in root.children(&mut cursor) {
        match child.kind() {
            "function_declaration" => {
                if let Some(name) = child.child_by_field_name("name") {
                    push_symbol(
                        GoDef {
                            kind: SymbolKind::Function,
                            name_node: name,
                            full_node: child,
                            doc: doc_comment(child, source),
                        },
                        package,
                        &[],
                        source,
                        out,
                    );
                }
            }
            "method_declaration" => {
                if let Some(name) = child.child_by_field_name("name") {
                    let containers: Vec<String> =
                        receiver_type(child, source).into_iter().collect();
                    push_symbol(
                        GoDef {
                            kind: SymbolKind::Method,
                            name_node: name,
                            full_node: child,
                            doc: doc_comment(child, source),
                        },
                        package,
                        &containers,
                        source,
                        out,
                    );
                }
            }
            "type_declaration" => {
                let doc = doc_comment(child, source);
                let mut c = child.walk();
                for spec in child.named_children(&mut c) {
                    if spec.kind() == "type_spec"
                        && let Some(name) = spec.child_by_field_name("name")
                    {
                        push_symbol(
                            GoDef {
                                kind: type_spec_kind(spec),
                                name_node: name,
                                full_node: spec,
                                doc: doc.clone(),
                            },
                            package,
                            &[],
                            source,
                            out,
                        );
                    }
                }
            }
            "const_declaration" | "var_declaration" => {
                let kind = if child.kind() == "const_declaration" {
                    SymbolKind::Constant
                } else {
                    SymbolKind::Variable
                };
                let doc = doc_comment(child, source);
                let mut c = child.walk();
                for spec in child.named_children(&mut c) {
                    if matches!(spec.kind(), "const_spec" | "var_spec")
                        && let Some(name) = spec.child_by_field_name("name")
                    {
                        push_symbol(
                            GoDef {
                                kind,
                                name_node: name,
                                full_node: spec,
                                doc: doc.clone(),
                            },
                            package,
                            &[],
                            source,
                            out,
                        );
                    }
                }
            }
            _ => {}
        }
    }
}

/// The callee name + location for a `call_expression`'s function operand.
fn callee(func: Node, source: &[u8]) -> Option<(String, Location)> {
    match func.kind() {
        "identifier" => Some((text(func, source).to_string(), location_of(func))),
        "selector_expression" => {
            let field = func.child_by_field_name("field")?;
            Some((text(field, source).to_string(), location_of(field)))
        }
        _ => None,
    }
}

fn classify_identifier(node: Node) -> Option<RefKind> {
    let parent = node.parent()?;
    let is_field = |field: &str| parent.child_by_field_name(field) == Some(node);
    match parent.kind() {
        "function_declaration" | "method_declaration" if is_field("name") => None,
        "call_expression" if is_field("function") => None,
        "selector_expression" if is_field("operand") => Some(RefKind::Read),
        "assignment_statement" if is_field("left") => Some(RefKind::Write),
        "parameter_declaration" | "package_clause" | "import_spec" | "keyed_element" => None,
        _ => Some(RefKind::Read),
    }
}

fn collect_imports(n: Node, package: &str, source: &[u8], out: &mut Vec<Import>) {
    each_node(n, &mut |m| {
        if m.kind() == "import_spec" {
            let path_node = m.child_by_field_name("path").or_else(|| {
                let mut c = m.walk();
                m.named_children(&mut c)
                    .find(|k| k.kind() == "interpreted_string_literal")
            });
            if let Some(pn) = path_node {
                let module = text(pn, source).trim_matches(['"', '`']).to_string();
                let name = m
                    .child_by_field_name("name")
                    .map(|nm| text(nm, source).to_string());
                out.push(Import {
                    source: package.to_string(),
                    module,
                    name,
                    location: location_of(m),
                });
            }
        }
    });
}

impl LanguageExtractor for GoExtractor {
    fn language(&self) -> &'static str {
        "go"
    }

    fn extensions(&self) -> &'static [&'static str] {
        &["go"]
    }

    fn extract(&self, rel_path: &str, source: &[u8]) -> ExtractResult {
        let mut parser = Parser::new();
        if parser.set_language(&self.language).is_err() {
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
        let package = package_name(root, rel_path, source);

        let mut symbols = Vec::new();
        collect_defs(root, &package, source, &mut symbols);
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
            "import_declaration" => collect_imports(n, &package, source, &mut imports),
            _ => {}
        });

        ExtractResult {
            symbols,
            references,
            imports,
            scopes: Vec::new(),
            parse_failed,
        }
    }
}
