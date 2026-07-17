//! Bash extractor: `function_definition`s and top-level `variable_assignment`s.
//! Bash has no module concept, so the C1 module component is the repo-relative
//! file path (slashes to dots, extension dropped) — C1's fallback, same as
//! C/Zig. Imports are `source`/`.` commands (R9). C8 docstrings are the
//! contiguous leading `#` comment block. tree-sitter-bash ships no locals
//! query, so no `Scope` facts (R10 fallback).

use crate::extract::{ExtractResult, ExtractorRegistration, LanguageExtractor};
use crate::facts::{Import, Location, Point, RefKind, Reference, Span, Symbol, SymbolKind};
use crate::hash;
use tree_sitter::{Node, Parser};

pub struct BashExtractor {
    language: tree_sitter::Language,
}

impl BashExtractor {
    pub fn new() -> Self {
        Self {
            language: tree_sitter_bash::LANGUAGE.into(),
        }
    }
}

impl Default for BashExtractor {
    fn default() -> Self {
        Self::new()
    }
}

inventory::submit! {
    ExtractorRegistration {
        language: "bash",
        extensions: &["sh", "bash"],
        make: || Box::new(BashExtractor::new()),
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

/// C8 doc comment: the contiguous `#` comment block immediately above `decl`.
fn doc_comment(decl: Node, source: &[u8]) -> String {
    let mut lines: Vec<String> = Vec::new();
    let mut expected_row = decl.start_position().row;
    let mut cur = decl.prev_sibling();
    while let Some(c) = cur {
        if c.kind() != "comment" || c.end_position().row + 1 != expected_row {
            break;
        }
        // Skip a shebang so it never masquerades as a docstring.
        let raw = text(c, source).trim();
        if raw.starts_with("#!") {
            break;
        }
        let cleaned = raw.trim_start_matches('#').trim();
        lines.push(cleaned.to_string());
        expected_row = c.start_position().row;
        cur = c.prev_sibling();
    }
    lines.reverse();
    lines.join("\n")
}

fn push_symbol(
    kind: SymbolKind,
    name_node: Node,
    full_node: Node,
    doc: String,
    module: &str,
    source: &[u8],
    out: &mut Vec<Symbol>,
) {
    let name = text(name_node, source).to_string();
    let qpath = crate::path::build_qpath(module, &[], &name);
    let signature = match full_node.child_by_field_name("body") {
        Some(b) => String::from_utf8_lossy(&source[full_node.start_byte()..b.start_byte()])
            .trim()
            .to_string(),
        None => text(full_node, source).trim().to_string(),
    };
    let full = (full_node.start_byte(), full_node.end_byte());
    let ident = (name_node.start_byte(), name_node.end_byte());
    out.push(Symbol {
        kind,
        name,
        qpath,
        signature,
        docstring: doc,
        full_span: span_of(full_node),
        ident_span: span_of(name_node),
        parent: None,
        body_hash: hash::body_hash(source, full, ident),
        body_tokens: hash::body_tokens(source, full, ident),
    });
}

/// Collect top-level defs, descending through wrapper nodes (`program`, and the
/// `ERROR` a syntax error reparents siblings under) but never into a symbol's
/// own body — so best-effort siblings around a parse error still surface (R1).
fn collect_defs(node: Node, module: &str, source: &[u8], out: &mut Vec<Symbol>) {
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        match child.kind() {
            "function_definition" => {
                if let Some(name) = child.child_by_field_name("name") {
                    push_symbol(
                        SymbolKind::Function,
                        name,
                        child,
                        doc_comment(child, source),
                        module,
                        source,
                        out,
                    );
                }
            }
            "variable_assignment" => {
                if let Some(name) = child.child_by_field_name("name") {
                    push_symbol(
                        SymbolKind::Variable,
                        name,
                        child,
                        doc_comment(child, source),
                        module,
                        source,
                        out,
                    );
                }
            }
            "program" | "ERROR" => collect_defs(child, module, source, out),
            _ => {}
        }
    }
}

/// The sourced path of a `source <path>` or `. <path>` command, if `n` is one.
fn source_import(n: Node, source: &[u8]) -> Option<String> {
    let name = n.child_by_field_name("name")?;
    let cmd = text(name, source);
    if cmd != "source" && cmd != "." {
        return None;
    }
    let arg = n.child_by_field_name("argument")?;
    Some(text(arg, source).to_string())
}

impl LanguageExtractor for BashExtractor {
    fn language(&self) -> &'static str {
        "bash"
    }

    fn extensions(&self) -> &'static [&'static str] {
        &["sh", "bash"]
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
        for (sym, q) in symbols.iter_mut().zip(crate::path::disambiguate(&qpaths)) {
            sym.qpath = q;
        }

        let mut references = Vec::new();
        let mut imports = Vec::new();
        each_node(root, &mut |n| match n.kind() {
            "command" => {
                if let Some(module) = source_import(n, source) {
                    imports.push(Import {
                        source: file_module(rel_path),
                        module,
                        name: None,
                        location: location_of(n),
                    });
                }
            }
            "command_name" => {
                references.push(Reference {
                    name: text(n, source).to_string(),
                    location: location_of(n),
                    kind: RefKind::Call,
                });
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
