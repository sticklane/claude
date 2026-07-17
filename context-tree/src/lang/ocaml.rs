//! OCaml extractor: top-level and nested-module `let` bindings. The C1 module
//! component is the OCaml module structure — the compilation unit keys on the
//! file path (C1's fallback, since the top-level module is unnamed in source),
//! and each nested `module M = struct … end` adds a C1 container. C8 docstrings
//! are the preceding `(** … *)` comment. Imports are `open …` statements (R9).
//! tree-sitter-ocaml ships a locals query with `@local.scope` captures, so
//! `Scope` facts are produced (R10); the scope-node set below mirrors that
//! query's `@local.scope` alternatives.

use crate::extract::{ExtractResult, ExtractorRegistration, LanguageExtractor};
use crate::facts::{Import, Location, Point, RefKind, Reference, Scope, Span, Symbol, SymbolKind};
use crate::hash;
use crate::path;
use tree_sitter::{Node, Parser};

pub struct OcamlExtractor {
    language: tree_sitter::Language,
}

impl OcamlExtractor {
    pub fn new() -> Self {
        Self {
            language: tree_sitter_ocaml::LANGUAGE_OCAML.into(),
        }
    }
}

impl Default for OcamlExtractor {
    fn default() -> Self {
        Self::new()
    }
}

inventory::submit! {
    ExtractorRegistration {
        language: "ocaml",
        extensions: &["ml"],
        make: || Box::new(OcamlExtractor::new()),
    }
}

/// The `@local.scope` alternatives from tree-sitter-ocaml's `queries/locals.scm`
/// — a reference inside one of these nodes to a local binding is scope-bound.
const SCOPE_KINDS: &[&str] = &[
    "let_binding",
    "class_binding",
    "class_function",
    "method_definition",
    "fun_expression",
    "object_expression",
    "for_expression",
    "match_case",
];

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

fn first_child_kind<'a>(node: Node<'a>, kind: &str) -> Option<Node<'a>> {
    let mut cursor = node.walk();
    node.children(&mut cursor).find(|c| c.kind() == kind)
}

/// The C1 module component for the compilation unit: repo-relative path,
/// extension dropped, separators mapped to dots (C1's file-path fallback).
fn file_module(rel_path: &str) -> String {
    rel_path
        .rsplit_once('.')
        .map(|(stem, _)| stem)
        .unwrap_or(rel_path)
        .replace(['/', '\\'], ".")
}

/// C8 doc comment: the preceding `(** … *)` comment, stripped of markers.
fn doc_comment(decl: Node, source: &[u8]) -> String {
    let Some(prev) = decl.prev_sibling() else {
        return String::new();
    };
    if prev.kind() != "comment" {
        return String::new();
    }
    let raw = text(prev, source).trim();
    let Some(inner) = raw.strip_prefix("(**").and_then(|s| s.strip_suffix("*)")) else {
        return String::new();
    };
    inner
        .lines()
        .map(|l| l.trim().trim_start_matches('*').trim())
        .filter(|l| !l.is_empty())
        .collect::<Vec<_>>()
        .join("\n")
}

struct OcamlDef<'a> {
    kind: SymbolKind,
    name_node: Node<'a>,
    full_node: Node<'a>,
    doc: String,
}

fn push_symbol(
    def: OcamlDef,
    module: &str,
    containers: &[String],
    source: &[u8],
    out: &mut Vec<Symbol>,
) {
    let name = text(def.name_node, source).to_string();
    let qpath = path::build_qpath(module, containers, &name);
    let signature = match def.full_node.child_by_field_name("body") {
        Some(b) => String::from_utf8_lossy(&source[def.full_node.start_byte()..b.start_byte()])
            .trim()
            .to_string(),
        None => text(def.full_node, source).trim().to_string(),
    };
    let parent = if containers.is_empty() {
        None
    } else {
        Some(path::build_qpath(module, containers, ""))
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

fn has_parameter(let_binding: Node) -> bool {
    let mut cursor = let_binding.walk();
    let_binding
        .children(&mut cursor)
        .any(|c| c.kind() == "parameter")
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
        match child.kind() {
            "value_definition" => {
                let doc = doc_comment(child, source);
                let mut bc = child.walk();
                for lb in child
                    .children(&mut bc)
                    .filter(|c| c.kind() == "let_binding")
                {
                    let Some(name) = lb.child_by_field_name("pattern") else {
                        continue;
                    };
                    if name.kind() != "value_name" {
                        continue;
                    }
                    let kind = if has_parameter(lb) {
                        SymbolKind::Function
                    } else {
                        SymbolKind::Constant
                    };
                    push_symbol(
                        OcamlDef {
                            kind,
                            name_node: name,
                            full_node: lb,
                            doc: doc.clone(),
                        },
                        module,
                        containers,
                        source,
                        out,
                    );
                }
            }
            "module_definition" => {
                let mut mc = child.walk();
                for mb in child
                    .children(&mut mc)
                    .filter(|c| c.kind() == "module_binding")
                {
                    let Some(name) = first_child_kind(mb, "module_name") else {
                        continue;
                    };
                    push_symbol(
                        OcamlDef {
                            kind: SymbolKind::Module,
                            name_node: name,
                            full_node: mb,
                            doc: doc_comment(child, source),
                        },
                        module,
                        containers,
                        source,
                        out,
                    );
                    containers.push(text(name, source).to_string());
                    collect_defs(mb, module, containers, source, out);
                    containers.pop();
                }
            }
            _ => collect_defs(child, module, containers, source, out),
        }
    }
}

/// The nearest enclosing `@local.scope` node of `node`, if any.
fn enclosing_scope(node: Node) -> Option<Node> {
    let mut cur = node.parent();
    while let Some(n) = cur {
        if SCOPE_KINDS.contains(&n.kind()) {
            return Some(n);
        }
        cur = n.parent();
    }
    None
}

impl LanguageExtractor for OcamlExtractor {
    fn language(&self) -> &'static str {
        "ocaml"
    }

    fn extensions(&self) -> &'static [&'static str] {
        &["ml"]
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
        let mut containers = Vec::new();
        collect_defs(root, &module, &mut containers, source, &mut symbols);
        let qpaths: Vec<String> = symbols.iter().map(|s| s.qpath.clone()).collect();
        for (sym, q) in symbols.iter_mut().zip(path::disambiguate(&qpaths)) {
            sym.qpath = q;
        }

        let mut references = Vec::new();
        let mut imports = Vec::new();
        let mut scopes = Vec::new();
        each_node(root, &mut |n| match n.kind() {
            "value_name" if n.parent().map(|p| p.kind()) == Some("value_path") => {
                references.push(Reference {
                    name: text(n, source).to_string(),
                    location: location_of(n),
                    kind: RefKind::Read,
                });
            }
            "value_pattern" => {
                if let Some(scope) = enclosing_scope(n) {
                    scopes.push(Scope {
                        name: text(n, source).to_string(),
                        def_location: location_of(n),
                        scope: span_of(scope),
                    });
                }
            }
            "open_module" => {
                if let Some(m) = n.child_by_field_name("module") {
                    imports.push(Import {
                        source: module.clone(),
                        module: text(m, source).to_string(),
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
            scopes,
            parse_failed,
        }
    }
}
