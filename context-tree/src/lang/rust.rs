//! Rust extractor: functions/methods, structs, enums, traits, type aliases,
//! consts/statics, and `mod` blocks. The C1 module component is the file-path
//! module (slashes → `.`, `.rs` dropped) extended by nested `mod`/`impl`/trait
//! containers — an approximation of the Rust module path sufficient for opaque
//! C1 identity. C8 docstrings are `///`/`//!`/`/** */` doc comments.
//! tree-sitter-rust ships no locals query, so no `Scope` facts (R10 fallback).

use crate::extract::{ExtractResult, ExtractorRegistration, LanguageExtractor};
use crate::facts::{Import, Location, Point, RefKind, Reference, Span, Symbol, SymbolKind};
use crate::hash;
use crate::path;
use tree_sitter::{Node, Parser};

pub struct RustExtractor {
    language: tree_sitter::Language,
}

impl RustExtractor {
    pub fn new() -> Self {
        Self {
            language: tree_sitter_rust::LANGUAGE.into(),
        }
    }
}

impl Default for RustExtractor {
    fn default() -> Self {
        Self::new()
    }
}

inventory::submit! {
    ExtractorRegistration {
        language: "rust",
        extensions: &["rs"],
        make: || Box::new(RustExtractor::new()),
    }
}

fn file_module(rel_path: &str) -> String {
    rel_path
        .rsplit_once('.')
        .map(|(s, _)| s)
        .unwrap_or(rel_path)
        .replace(['/', '\\'], ".")
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

/// C8 Rust doc comment: the contiguous `///` / `//!` / `/** */` comment block
/// immediately above `decl`, stripped of markers.
fn doc_comment(decl: Node, source: &[u8]) -> String {
    let mut lines: Vec<String> = Vec::new();
    let mut expected_row = decl.start_position().row;
    let mut cur = decl.prev_sibling();
    while let Some(c) = cur {
        let is_comment = matches!(c.kind(), "line_comment" | "block_comment");
        let raw = text(c, source).trim();
        let is_doc = raw.starts_with("///") || raw.starts_with("//!") || raw.starts_with("/**");
        // tree-sitter-rust's `line_comment` end-position rolls onto the next
        // line (col 0), so derive the comment's last content row instead.
        let last_row = if c.end_position().column == 0 {
            c.end_position().row.saturating_sub(1)
        } else {
            c.end_position().row
        };
        if !is_comment || !is_doc || last_row + 1 != expected_row {
            break;
        }
        let cleaned = raw
            .trim_start_matches("///")
            .trim_start_matches("//!")
            .trim_start_matches("/**")
            .trim_start_matches("//")
            .trim_end_matches("*/")
            .trim_start_matches('*')
            .trim();
        lines.push(cleaned.to_string());
        expected_row = c.start_position().row;
        cur = c.prev_sibling();
    }
    lines.reverse();
    lines.join("\n")
}

fn symbol_kind(kind: &str, in_type: bool) -> Option<SymbolKind> {
    match kind {
        "function_item" | "function_signature_item" => Some(if in_type {
            SymbolKind::Method
        } else {
            SymbolKind::Function
        }),
        "struct_item" => Some(SymbolKind::Struct),
        "enum_item" => Some(SymbolKind::Enum),
        "trait_item" => Some(SymbolKind::Trait),
        "mod_item" => Some(SymbolKind::Module),
        "const_item" | "static_item" => Some(SymbolKind::Constant),
        "type_item" => Some(SymbolKind::TypeAlias),
        _ => None,
    }
}

/// The container type name of an `impl_item` (`Widget` for `impl Widget` or
/// `impl Trait for Widget`).
fn impl_type_name(impl_node: Node, source: &[u8]) -> Option<String> {
    let ty = impl_node.child_by_field_name("type")?;
    if ty.kind() == "type_identifier" {
        return Some(text(ty, source).to_string());
    }
    let mut found = None;
    each_node(ty, &mut |n| {
        if found.is_none() && n.kind() == "type_identifier" {
            found = Some(text(n, source).to_string());
        }
    });
    found
}

fn push_symbol(
    kind: SymbolKind,
    name_node: Node,
    full_node: Node,
    module: &str,
    containers: &[String],
    source: &[u8],
    out: &mut Vec<Symbol>,
) {
    let name = text(name_node, source).to_string();
    let qpath = path::build_qpath(module, containers, &name);
    let signature = match full_node.child_by_field_name("body") {
        Some(b) => String::from_utf8_lossy(&source[full_node.start_byte()..b.start_byte()])
            .trim()
            .to_string(),
        None => text(full_node, source).trim().to_string(),
    };
    let parent = if containers.is_empty() {
        None
    } else {
        Some(path::build_qpath(module, containers, ""))
    };
    let full = (full_node.start_byte(), full_node.end_byte());
    let ident = (name_node.start_byte(), name_node.end_byte());
    out.push(Symbol {
        kind,
        name,
        qpath,
        signature,
        docstring: doc_comment(full_node, source),
        full_span: span_of(full_node),
        ident_span: span_of(name_node),
        parent,
        body_hash: hash::body_hash(source, full, ident),
        body_tokens: hash::body_tokens(source, full, ident),
    });
}

fn collect_defs(
    node: Node,
    module: &str,
    containers: &mut Vec<String>,
    in_type: bool,
    source: &[u8],
    out: &mut Vec<Symbol>,
) {
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        // An `impl` block is a container (its type), not a symbol.
        if child.kind() == "impl_item" {
            if let Some(ty) = impl_type_name(child, source) {
                containers.push(ty);
                collect_defs(child, module, containers, true, source, out);
                containers.pop();
            } else {
                collect_defs(child, module, containers, true, source, out);
            }
            continue;
        }
        let Some(sym_kind) = symbol_kind(child.kind(), in_type) else {
            collect_defs(child, module, containers, in_type, source, out);
            continue;
        };
        let Some(name_node) = child.child_by_field_name("name") else {
            collect_defs(child, module, containers, in_type, source, out);
            continue;
        };
        push_symbol(sym_kind, name_node, child, module, containers, source, out);
        // Traits and modules are containers for the items nested inside them.
        let name = text(name_node, source).to_string();
        let descends_as_type = matches!(child.kind(), "trait_item");
        if matches!(child.kind(), "trait_item" | "mod_item") {
            containers.push(name);
            collect_defs(child, module, containers, descends_as_type, source, out);
            containers.pop();
        } else {
            collect_defs(child, module, containers, false, source, out);
        }
    }
}

/// The callee name + location for a `call_expression`'s function operand.
fn callee(func: Node, source: &[u8]) -> Option<(String, Location)> {
    match func.kind() {
        "identifier" => Some((text(func, source).to_string(), location_of(func))),
        "field_expression" => {
            let field = func.child_by_field_name("field")?;
            Some((text(field, source).to_string(), location_of(field)))
        }
        "scoped_identifier" => {
            let name = func.child_by_field_name("name")?;
            Some((text(name, source).to_string(), location_of(name)))
        }
        _ => None,
    }
}

fn classify_identifier(node: Node) -> Option<RefKind> {
    let parent = node.parent()?;
    let is_field = |field: &str| parent.child_by_field_name(field) == Some(node);
    match parent.kind() {
        "function_item" | "struct_item" | "enum_item" | "trait_item" | "mod_item"
        | "const_item" | "static_item" | "type_item"
            if is_field("name") =>
        {
            None
        }
        "call_expression" if is_field("function") => None,
        "scoped_identifier" | "field_expression" | "use_declaration" | "use_list"
        | "scoped_use_list" => None,
        "let_declaration" if is_field("pattern") => Some(RefKind::Write),
        _ => Some(RefKind::Read),
    }
}

fn collect_import(arg: Node, module: &str, source: &[u8], out: &mut Vec<Import>) {
    match arg.kind() {
        "scoped_identifier" => {
            let name = arg
                .child_by_field_name("name")
                .map(|n| text(n, source).to_string());
            out.push(Import {
                source: module.to_string(),
                module: text(arg, source).to_string(),
                name,
                location: location_of(arg),
            });
        }
        "identifier" => {
            out.push(Import {
                source: module.to_string(),
                module: text(arg, source).to_string(),
                name: Some(text(arg, source).to_string()),
                location: location_of(arg),
            });
        }
        "use_as_clause" => {
            if let Some(path) = arg.child_by_field_name("path") {
                collect_import(path, module, source, out);
            }
        }
        "scoped_use_list" | "use_list" => {
            let prefix = arg
                .child_by_field_name("path")
                .map(|p| text(p, source).to_string());
            let mut c = arg.walk();
            for item in arg.named_children(&mut c) {
                match item.kind() {
                    "identifier" | "scoped_identifier" => {
                        let last = text(item, source).to_string();
                        let module_path = match &prefix {
                            Some(p) => format!("{p}::{last}"),
                            None => last.clone(),
                        };
                        out.push(Import {
                            source: module.to_string(),
                            module: module_path,
                            name: Some(last.rsplit("::").next().unwrap_or(&last).to_string()),
                            location: location_of(item),
                        });
                    }
                    _ => {}
                }
            }
        }
        _ => {}
    }
}

impl LanguageExtractor for RustExtractor {
    fn language(&self) -> &'static str {
        "rust"
    }

    fn extensions(&self) -> &'static [&'static str] {
        &["rs"]
    }

    fn extract(&self, rel_path: &str, source: &[u8]) -> ExtractResult {
        let module = file_module(rel_path);
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

        let mut symbols = Vec::new();
        let mut containers = Vec::new();
        collect_defs(root, &module, &mut containers, false, source, &mut symbols);
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
            "use_declaration" => {
                if let Some(arg) = n.child_by_field_name("argument") {
                    collect_import(arg, &module, source, &mut imports);
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
