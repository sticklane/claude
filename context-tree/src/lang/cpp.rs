//! C++ extractor: functions and top-level const/var declarations, with
//! `namespace` blocks as containers (not the module component). A symbol inside
//! a namespace keys under the namespace chain (`app.base`); a file-scope symbol
//! falls back to the repo-relative file path as its module component, exactly
//! like C. Overloads sharing a qualified path get C1 `#<n>` ordinals. C8
//! docstrings are the contiguous leading comment block. tree-sitter-cpp ships no
//! locals query, so no `Scope` facts (R10 fallback).

use crate::extract::{ExtractResult, ExtractorRegistration, LanguageExtractor};
use crate::facts::{Import, Location, Point, RefKind, Reference, Span, Symbol, SymbolKind};
use crate::hash;
use crate::path;
use tree_sitter::{Node, Parser};

pub struct CppExtractor {
    language: tree_sitter::Language,
}

impl CppExtractor {
    pub fn new() -> Self {
        Self {
            language: tree_sitter_cpp::LANGUAGE.into(),
        }
    }
}

impl Default for CppExtractor {
    fn default() -> Self {
        Self::new()
    }
}

inventory::submit! {
    ExtractorRegistration {
        language: "cpp",
        extensions: &["cpp", "cc", "cxx", "hpp", "hxx"],
        make: || Box::new(CppExtractor::new()),
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

/// The C1 file-path module component (used only for file-scope symbols).
fn file_module(rel_path: &str) -> String {
    rel_path
        .rsplit_once('.')
        .map(|(stem, _)| stem)
        .unwrap_or(rel_path)
        .replace(['/', '\\'], ".")
}

/// C8 doc comment: the contiguous comment block immediately above `decl`.
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

/// Innermost identifier of a (possibly pointer/parenthesized) declarator.
fn declarator_identifier(decl: Node) -> Option<Node> {
    match decl.kind() {
        "identifier" | "field_identifier" => Some(decl),
        "init_declarator" | "pointer_declarator" | "parenthesized_declarator"
        | "array_declarator" | "reference_declarator" | "function_declarator" => decl
            .child_by_field_name("declarator")
            .and_then(declarator_identifier),
        _ => None,
    }
}

struct CppDef<'a> {
    kind: SymbolKind,
    name_node: Node<'a>,
    full_node: Node<'a>,
    doc: String,
}

fn push_symbol(
    def: CppDef,
    module: &str,
    containers: &[String],
    source: &[u8],
    out: &mut Vec<Symbol>,
) {
    let name = text(def.name_node, source).to_string();
    // Namespaces are containers, not the module component: a namespaced symbol
    // drops the file-path module, a file-scope symbol keeps it.
    let qpath = if containers.is_empty() {
        path::build_qpath(module, &[], &name)
    } else {
        path::build_qpath("", containers, &name)
    };
    let signature = match def.full_node.child_by_field_name("body") {
        Some(b) => String::from_utf8_lossy(&source[def.full_node.start_byte()..b.start_byte()])
            .trim()
            .to_string(),
        None => text(def.full_node, source).trim().to_string(),
    };
    let parent = if containers.is_empty() {
        None
    } else {
        Some(path::build_qpath("", containers, ""))
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

fn has_const_qualifier(decl: Node, source: &[u8]) -> bool {
    let mut cursor = decl.walk();
    decl.children(&mut cursor)
        .any(|c| c.kind() == "type_qualifier" && text(c, source) == "const")
}

fn collect_defs(
    node: Node,
    module: &str,
    containers: &[String],
    source: &[u8],
    out: &mut Vec<Symbol>,
) {
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        match child.kind() {
            "function_definition" => {
                if let Some(fdecl) = child.child_by_field_name("declarator")
                    && let Some(name) = declarator_identifier(fdecl)
                {
                    push_symbol(
                        CppDef {
                            kind: SymbolKind::Function,
                            name_node: name,
                            full_node: child,
                            doc: doc_comment(child, source),
                        },
                        module,
                        containers,
                        source,
                        out,
                    );
                }
            }
            "declaration" => {
                let kind = if has_const_qualifier(child, source) {
                    SymbolKind::Constant
                } else {
                    SymbolKind::Variable
                };
                let doc = doc_comment(child, source);
                let mut dc = child.walk();
                for d in child.children(&mut dc) {
                    if matches!(d.kind(), "init_declarator" | "identifier")
                        && let Some(name) = declarator_identifier(d)
                    {
                        push_symbol(
                            CppDef {
                                kind,
                                name_node: name,
                                full_node: child,
                                doc: doc.clone(),
                            },
                            module,
                            containers,
                            source,
                            out,
                        );
                    }
                }
            }
            "namespace_definition" => {
                if let Some(body) = child.child_by_field_name("body") {
                    let mut nested = containers.to_vec();
                    if let Some(name) = child.child_by_field_name("name") {
                        nested.push(text(name, source).to_string());
                    }
                    collect_defs(body, module, &nested, source, out);
                }
            }
            _ => {}
        }
    }
}

fn callee(func: Node, source: &[u8]) -> Option<(String, Location)> {
    match func.kind() {
        "identifier" | "qualified_identifier" | "field_identifier" => {
            Some((text(func, source).to_string(), location_of(func)))
        }
        "field_expression" => {
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
        "function_declarator" | "init_declarator" if is_field("declarator") => None,
        "call_expression" if is_field("function") => None,
        "assignment_expression" if is_field("left") => Some(RefKind::Write),
        "parameter_declaration" | "namespace_definition" => None,
        _ => Some(RefKind::Read),
    }
}

fn include_module(include: Node, source: &[u8]) -> Option<String> {
    let path_node = include.child_by_field_name("path")?;
    Some(
        text(path_node, source)
            .trim_matches(['<', '>', '"'])
            .to_string(),
    )
}

impl LanguageExtractor for CppExtractor {
    fn language(&self) -> &'static str {
        "cpp"
    }

    fn extensions(&self) -> &'static [&'static str] {
        &["cpp", "cc", "cxx", "hpp", "hxx"]
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
        collect_defs(root, &module, &[], source, &mut symbols);
        let qpaths: Vec<String> = symbols.iter().map(|s| s.qpath.clone()).collect();
        for (sym, q) in symbols.iter_mut().zip(path::disambiguate(&qpaths)) {
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
            "preproc_include" => {
                if let Some(module) = include_module(n, source) {
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
