//! Kotlin extractor: functions, classes/objects, methods, and properties. The
//! C1 module component is the Kotlin **package** (from `package …`), not the
//! file path, so a file move within a package leaves qualified paths unchanged
//! (R13 identity). C8 docstrings are the preceding `/** … */` KDoc block.
//! Imports are `import …` statements (R9). tree-sitter-kotlin-ng ships no locals
//! query, so no `Scope` facts (R10 fallback).

use crate::extract::{ExtractResult, ExtractorRegistration, LanguageExtractor};
use crate::facts::{Import, Location, Point, RefKind, Reference, Span, Symbol, SymbolKind};
use crate::hash;
use crate::path;
use tree_sitter::{Node, Parser};

pub struct KotlinExtractor {
    language: tree_sitter::Language,
}

impl KotlinExtractor {
    pub fn new() -> Self {
        Self {
            language: tree_sitter_kotlin_ng::LANGUAGE.into(),
        }
    }
}

impl Default for KotlinExtractor {
    fn default() -> Self {
        Self::new()
    }
}

inventory::submit! {
    ExtractorRegistration {
        language: "kotlin",
        extensions: &["kt", "kts"],
        make: || Box::new(KotlinExtractor::new()),
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

/// The package name from `package …`, or the file-path fallback.
fn package_name(root: Node, rel_path: &str, source: &[u8]) -> String {
    if let Some(header) = first_child_kind(root, "package_header")
        && let Some(id) = first_child_kind(header, "qualified_identifier")
    {
        return text(id, source).to_string();
    }
    rel_path
        .rsplit_once('.')
        .map(|(s, _)| s)
        .unwrap_or(rel_path)
        .replace(['/', '\\'], ".")
}

/// C8 KDoc: the preceding `/** … */` block comment, stripped of markers.
fn docstring(decl: Node, source: &[u8]) -> String {
    let Some(prev) = decl.prev_sibling() else {
        return String::new();
    };
    if prev.kind() != "block_comment" {
        return String::new();
    }
    let raw = text(prev, source).trim();
    if !raw.starts_with("/**") {
        return String::new();
    }
    let stripped = raw.trim_start_matches("/**").trim_end_matches("*/");
    stripped
        .lines()
        .map(|l| l.trim().trim_start_matches('*').trim())
        .filter(|l| !l.is_empty())
        .collect::<Vec<_>>()
        .join("\n")
}

/// The identifier of a `property_declaration`'s single binding, if any.
fn property_name(decl: Node) -> Option<Node> {
    let vd = first_child_kind(decl, "variable_declaration")?;
    first_child_kind(vd, "identifier")
}

fn push_symbol(
    kind: SymbolKind,
    name_node: Node,
    full_node: Node,
    package: &str,
    containers: &[String],
    source: &[u8],
    out: &mut Vec<Symbol>,
) {
    let name = text(name_node, source).to_string();
    let qpath = path::build_qpath(package, containers, &name);
    let signature = match full_node.child_by_field_name("body") {
        Some(b) => String::from_utf8_lossy(&source[full_node.start_byte()..b.start_byte()])
            .trim()
            .to_string(),
        None => text(full_node, source).trim().to_string(),
    };
    let parent = if containers.is_empty() {
        None
    } else {
        Some(path::build_qpath(package, containers, ""))
    };
    let full = (full_node.start_byte(), full_node.end_byte());
    let ident = (name_node.start_byte(), name_node.end_byte());
    out.push(Symbol {
        kind,
        name,
        qpath,
        signature,
        docstring: docstring(full_node, source),
        full_span: span_of(full_node),
        ident_span: span_of(name_node),
        parent,
        body_hash: hash::body_hash(source, full, ident),
        body_tokens: hash::body_tokens(source, full, ident),
    });
}

fn collect_defs(
    node: Node,
    package: &str,
    containers: &mut Vec<String>,
    source: &[u8],
    out: &mut Vec<Symbol>,
) {
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        match child.kind() {
            "class_declaration" | "object_declaration" => {
                if let Some(name) = child.child_by_field_name("name") {
                    push_symbol(
                        SymbolKind::Class,
                        name,
                        child,
                        package,
                        containers,
                        source,
                        out,
                    );
                    containers.push(text(name, source).to_string());
                    collect_defs(child, package, containers, source, out);
                    containers.pop();
                }
            }
            "function_declaration" => {
                if let Some(name) = child.child_by_field_name("name") {
                    let kind = if containers.is_empty() {
                        SymbolKind::Function
                    } else {
                        SymbolKind::Method
                    };
                    push_symbol(kind, name, child, package, containers, source, out);
                }
            }
            "property_declaration" => {
                if let Some(name) = property_name(child) {
                    let is_const = text(child, source)
                        .split_whitespace()
                        .find_map(|t| match t {
                            "val" => Some(true),
                            "var" => Some(false),
                            _ => None,
                        })
                        .unwrap_or(false);
                    let kind = if is_const {
                        SymbolKind::Constant
                    } else {
                        SymbolKind::Variable
                    };
                    push_symbol(kind, name, child, package, containers, source, out);
                }
            }
            _ => collect_defs(child, package, containers, source, out),
        }
    }
}

/// The callee identifier of a `call_expression`, if it is a bare-name call.
fn call_callee(node: Node) -> Option<Node> {
    let callee = node.child(0)?;
    (callee.kind() == "identifier").then_some(callee)
}

fn classify_identifier(node: Node) -> Option<RefKind> {
    let parent = node.parent()?;
    match parent.kind() {
        "function_declaration" if parent.child_by_field_name("name") == Some(node) => None,
        "variable_declaration" => None,
        "package_header" | "qualified_identifier" | "import" | "user_type" => None,
        "call_expression" if call_callee(parent) == Some(node) => None,
        _ => Some(RefKind::Read),
    }
}

impl LanguageExtractor for KotlinExtractor {
    fn language(&self) -> &'static str {
        "kotlin"
    }

    fn extensions(&self) -> &'static [&'static str] {
        &["kt", "kts"]
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
        let mut containers = Vec::new();
        collect_defs(root, &package, &mut containers, source, &mut symbols);
        let qpaths: Vec<String> = symbols.iter().map(|s| s.qpath.clone()).collect();
        for (sym, q) in symbols.iter_mut().zip(path::disambiguate(&qpaths)) {
            sym.qpath = q;
        }

        let mut references = Vec::new();
        let mut imports = Vec::new();
        each_node(root, &mut |n| match n.kind() {
            "call_expression" => {
                if let Some(callee) = call_callee(n) {
                    references.push(Reference {
                        name: text(callee, source).to_string(),
                        location: location_of(callee),
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
            "import" => {
                if let Some(id) = first_child_kind(n, "qualified_identifier") {
                    let full = text(id, source).to_string();
                    let name = full.rsplit('.').next().unwrap_or(&full).to_string();
                    imports.push(Import {
                        source: package.clone(),
                        module: full,
                        name: Some(name),
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
