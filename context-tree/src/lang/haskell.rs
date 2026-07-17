//! Haskell extractor: top-level function and value bindings. The C1 module
//! component is the module name from the `module … where` header (not the file
//! path), so a file move within a package leaves qualified paths unchanged (R13
//! identity). C8 docstrings are the preceding Haddock (`-- |`) comment. Imports
//! are `import …` statements (R9). tree-sitter-haskell's locals query ships no
//! `@local.scope` captures, so no `Scope` facts are produced (R10 fallback).

use crate::extract::{ExtractResult, ExtractorRegistration, LanguageExtractor};
use crate::facts::{Import, Location, Point, RefKind, Reference, Span, Symbol, SymbolKind};
use crate::hash;
use crate::path;
use tree_sitter::{Node, Parser};

pub struct HaskellExtractor {
    language: tree_sitter::Language,
}

impl HaskellExtractor {
    pub fn new() -> Self {
        Self {
            language: tree_sitter_haskell::LANGUAGE.into(),
        }
    }
}

impl Default for HaskellExtractor {
    fn default() -> Self {
        Self::new()
    }
}

inventory::submit! {
    ExtractorRegistration {
        language: "haskell",
        extensions: &["hs"],
        make: || Box::new(HaskellExtractor::new()),
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

fn first_child_kind<'a>(node: Node<'a>, kind: &str) -> Option<Node<'a>> {
    let mut cursor = node.walk();
    node.children(&mut cursor).find(|c| c.kind() == kind)
}

/// The module name from the `module … where` header, or the file-path fallback.
fn module_name(root: Node, rel_path: &str, source: &[u8]) -> String {
    if let Some(header) = first_child_kind(root, "header")
        && let Some(m) = header.child_by_field_name("module")
    {
        return text(m, source).to_string();
    }
    rel_path
        .rsplit_once('.')
        .map(|(s, _)| s)
        .unwrap_or(rel_path)
        .replace(['/', '\\'], ".")
}

/// C8 Haddock: the preceding `-- |` comment, skipping the binding's own type
/// signature if one sits between the comment and the declaration.
fn doc_comment(decl: Node, source: &[u8]) -> String {
    let mut prev = decl.prev_sibling();
    while let Some(p) = prev {
        if p.kind() == "signature" {
            prev = p.prev_sibling();
            continue;
        }
        break;
    }
    let Some(h) = prev else {
        return String::new();
    };
    if h.kind() != "haddock" {
        return String::new();
    }
    text(h, source)
        .lines()
        .map(|l| {
            l.trim()
                .trim_start_matches('-')
                .trim()
                .trim_start_matches(['|', '^'])
                .trim()
        })
        .filter(|l| !l.is_empty())
        .collect::<Vec<_>>()
        .join("\n")
}

fn push_symbol(
    kind: SymbolKind,
    name_node: Node,
    full_node: Node,
    module: &str,
    source: &[u8],
    out: &mut Vec<Symbol>,
) {
    let name = text(name_node, source).to_string();
    let qpath = path::build_qpath(module, &[], &name);
    let signature = text(full_node, source).trim().to_string();
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
        parent: None,
        body_hash: hash::body_hash(source, full, ident),
        body_tokens: hash::body_tokens(source, full, ident),
    });
}

/// Collect top-level bindings, descending through wrapper nodes (`haskell`,
/// `declarations`, and the `ERROR` a syntax error reparents siblings under) but
/// never into a binding's own body — best-effort siblings survive a parse error.
fn collect_defs(node: Node, module: &str, source: &[u8], out: &mut Vec<Symbol>) {
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        match child.kind() {
            "bind" => {
                if let Some(name) = child.child_by_field_name("name") {
                    push_symbol(SymbolKind::Constant, name, child, module, source, out);
                }
            }
            "function" => {
                if let Some(name) = child.child_by_field_name("name") {
                    push_symbol(SymbolKind::Function, name, child, module, source, out);
                }
            }
            "haskell" | "declarations" | "ERROR" => collect_defs(child, module, source, out),
            _ => {}
        }
    }
}

/// A `variable` node is a reference unless it is a definition name or a pattern
/// binding.
fn is_reference(node: Node) -> bool {
    let Some(parent) = node.parent() else {
        return false;
    };
    if parent.child_by_field_name("name") == Some(node) {
        return false;
    }
    !matches!(parent.kind(), "patterns" | "pattern")
}

impl LanguageExtractor for HaskellExtractor {
    fn language(&self) -> &'static str {
        "haskell"
    }

    fn extensions(&self) -> &'static [&'static str] {
        &["hs"]
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
        let module = module_name(root, rel_path, source);

        let mut symbols = Vec::new();
        collect_defs(root, &module, source, &mut symbols);
        let qpaths: Vec<String> = symbols.iter().map(|s| s.qpath.clone()).collect();
        for (sym, q) in symbols.iter_mut().zip(path::disambiguate(&qpaths)) {
            sym.qpath = q;
        }

        let mut references = Vec::new();
        let mut imports = Vec::new();
        each_node(root, &mut |n| match n.kind() {
            "variable" => {
                if is_reference(n) {
                    references.push(Reference {
                        name: text(n, source).to_string(),
                        location: location_of(n),
                        kind: RefKind::Read,
                    });
                }
            }
            "import" => {
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
            scopes: Vec::new(),
            parse_failed,
        }
    }
}
