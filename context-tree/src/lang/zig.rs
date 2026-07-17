//! Zig extractor: top-level function and const/var declarations. Zig has no
//! module concept, so the C1 module component is the repo-relative file path
//! (slashes to dots, extension dropped) — C1's fallback. Imports are
//! `@import("…")` builtin calls (R9). C8 docstrings are the contiguous leading
//! `//` comment block, treated per C8 since no native doc-comment syntax is
//! recognized. tree-sitter-zig ships no locals query, so no `Scope` facts (R10
//! fallback).

use crate::extract::{ExtractResult, ExtractorRegistration, LanguageExtractor};
use crate::facts::{Import, Location, Point, RefKind, Reference, Span, Symbol, SymbolKind};
use crate::hash;
use crate::path;
use tree_sitter::{Node, Parser};

pub struct ZigExtractor {
    language: tree_sitter::Language,
}

impl ZigExtractor {
    pub fn new() -> Self {
        Self {
            language: tree_sitter_zig::LANGUAGE.into(),
        }
    }
}

impl Default for ZigExtractor {
    fn default() -> Self {
        Self::new()
    }
}

inventory::submit! {
    ExtractorRegistration {
        language: "zig",
        extensions: &["zig"],
        make: || Box::new(ZigExtractor::new()),
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

/// The C1 module component: repo-relative path, extension dropped, separators
/// mapped to dots (no module concept — C1's file-path fallback).
fn file_module(rel_path: &str) -> String {
    rel_path
        .rsplit_once('.')
        .map(|(stem, _)| stem)
        .unwrap_or(rel_path)
        .replace(['/', '\\'], ".")
}

/// C8 doc comment: the contiguous `//` comment block immediately above `decl`.
fn doc_comment(decl: Node, source: &[u8]) -> String {
    let mut lines: Vec<String> = Vec::new();
    let mut expected_row = decl.start_position().row;
    let mut cur = decl.prev_sibling();
    while let Some(c) = cur {
        if c.kind() != "comment" || c.end_position().row + 1 != expected_row {
            break;
        }
        let cleaned = text(c, source).trim().trim_start_matches('/').trim();
        lines.push(cleaned.to_string());
        expected_row = c.start_position().row;
        cur = c.prev_sibling();
    }
    lines.reverse();
    lines.join("\n")
}

fn first_ident_child(node: Node) -> Option<Node> {
    let mut cursor = node.walk();
    node.children(&mut cursor)
        .find(|k| k.kind() == "identifier")
}

struct ZigDef<'a> {
    kind: SymbolKind,
    name_node: Node<'a>,
    full_node: Node<'a>,
    doc: String,
}

fn push_symbol(def: ZigDef, module: &str, source: &[u8], out: &mut Vec<Symbol>) {
    let name = text(def.name_node, source).to_string();
    let qpath = path::build_qpath(module, &[], &name);
    let signature = match def.full_node.child_by_field_name("body") {
        Some(b) => String::from_utf8_lossy(&source[def.full_node.start_byte()..b.start_byte()])
            .trim()
            .to_string(),
        None => text(def.full_node, source).trim().to_string(),
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
        parent: None,
        body_hash: hash::body_hash(source, full, ident),
        body_tokens: hash::body_tokens(source, full, ident),
    });
}

fn collect_defs(root: Node, module: &str, source: &[u8], out: &mut Vec<Symbol>) {
    let mut cursor = root.walk();
    for child in root.children(&mut cursor) {
        match child.kind() {
            "function_declaration" => {
                if let Some(name) = child.child_by_field_name("name") {
                    push_symbol(
                        ZigDef {
                            kind: SymbolKind::Function,
                            name_node: name,
                            full_node: child,
                            doc: doc_comment(child, source),
                        },
                        module,
                        source,
                        out,
                    );
                }
            }
            "variable_declaration" => {
                if let Some(name) = first_ident_child(child) {
                    // `const` binding → Constant, `var` binding → Variable.
                    let head = text(child, source);
                    let kind = if head.split('=').next().unwrap_or("").contains("const") {
                        SymbolKind::Constant
                    } else {
                        SymbolKind::Variable
                    };
                    push_symbol(
                        ZigDef {
                            kind,
                            name_node: name,
                            full_node: child,
                            doc: doc_comment(child, source),
                        },
                        module,
                        source,
                        out,
                    );
                }
            }
            _ => {}
        }
    }
}

fn classify_identifier(node: Node) -> Option<RefKind> {
    let parent = node.parent()?;
    let is_field = |field: &str| parent.child_by_field_name(field) == Some(node);
    match parent.kind() {
        "function_declaration" if is_field("name") => None,
        "call_expression" if is_field("function") => None,
        "variable_declaration" if first_ident_child(parent) == Some(node) => None,
        "parameters" | "parameter" => None,
        "assignment_expression" if is_field("left") => Some(RefKind::Write),
        _ => Some(RefKind::Read),
    }
}

/// The imported module string of an `@import("…")` builtin call, if this node is
/// one.
fn import_module(builtin: Node, source: &[u8]) -> Option<String> {
    let ident = first_child_kind(builtin, "builtin_identifier")?;
    if text(ident, source) != "@import" {
        return None;
    }
    let args = first_child_kind(builtin, "arguments")?;
    let string = first_child_kind(args, "string")?;
    let content = first_child_kind(string, "string_content")?;
    Some(text(content, source).to_string())
}

fn first_child_kind<'a>(node: Node<'a>, kind: &str) -> Option<Node<'a>> {
    let mut cursor = node.walk();
    node.children(&mut cursor).find(|c| c.kind() == kind)
}

impl LanguageExtractor for ZigExtractor {
    fn language(&self) -> &'static str {
        "zig"
    }

    fn extensions(&self) -> &'static [&'static str] {
        &["zig"]
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
        let module = file_module(rel_path);

        let mut symbols = Vec::new();
        collect_defs(root, &module, source, &mut symbols);
        let qpaths: Vec<String> = symbols.iter().map(|s| s.qpath.clone()).collect();
        for (sym, q) in symbols.iter_mut().zip(path::disambiguate(&qpaths)) {
            sym.qpath = q;
        }

        let mut references = Vec::new();
        let mut imports = Vec::new();
        each_node(root, &mut |n| match n.kind() {
            "call_expression" => {
                if let Some(func) = n.child_by_field_name("function")
                    && func.kind() == "identifier"
                {
                    references.push(Reference {
                        name: text(func, source).to_string(),
                        location: location_of(func),
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
            "builtin_function" => {
                if let Some(module) = import_module(n, source) {
                    imports.push(Import {
                        source: file_module(rel_path),
                        module,
                        name: None,
                        location: location_of(n),
                    });
                }
            }
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
