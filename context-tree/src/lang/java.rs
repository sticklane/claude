//! Java extractor: classes, interfaces, enums, methods, and constructors. The
//! C1 module component is the Java **package** (from `package …;`), not the
//! file path, so a file move within a package leaves qualified paths unchanged
//! (R13 identity). C8 docstrings are the preceding `/** … */` Javadoc block.
//! tree-sitter-java ships no locals query, so no `Scope` facts (R10 fallback).

use crate::extract::{ExtractResult, ExtractorRegistration, LanguageExtractor};
use crate::facts::{Import, Location, Point, RefKind, Reference, Span, Symbol, SymbolKind};
use crate::hash;
use crate::path;
use tree_sitter::{Node, Parser};

pub struct JavaExtractor {
    language: tree_sitter::Language,
}

impl JavaExtractor {
    pub fn new() -> Self {
        Self {
            language: tree_sitter_java::LANGUAGE.into(),
        }
    }
}

impl Default for JavaExtractor {
    fn default() -> Self {
        Self::new()
    }
}

inventory::submit! {
    ExtractorRegistration {
        language: "java",
        extensions: &["java"],
        make: || Box::new(JavaExtractor::new()),
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

/// The package name from `package …;`, or the file-path fallback.
fn package_name(root: Node, rel_path: &str, source: &[u8]) -> String {
    let mut cursor = root.walk();
    for child in root.children(&mut cursor) {
        if child.kind() == "package_declaration" {
            let mut c = child.walk();
            if let Some(id) = child
                .named_children(&mut c)
                .find(|n| matches!(n.kind(), "scoped_identifier" | "identifier"))
            {
                return text(id, source).to_string();
            }
        }
    }
    rel_path
        .rsplit_once('.')
        .map(|(s, _)| s)
        .unwrap_or(rel_path)
        .replace(['/', '\\'], ".")
}

/// C8 Javadoc: the preceding `/** … */` block comment, stripped of markers.
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

fn symbol_kind(kind: &str) -> Option<SymbolKind> {
    match kind {
        "class_declaration" => Some(SymbolKind::Class),
        "interface_declaration" | "annotation_type_declaration" => Some(SymbolKind::Interface),
        "enum_declaration" => Some(SymbolKind::Enum),
        "method_declaration" | "constructor_declaration" => Some(SymbolKind::Method),
        _ => None,
    }
}

fn is_container(kind: &str) -> bool {
    matches!(
        kind,
        "class_declaration"
            | "interface_declaration"
            | "annotation_type_declaration"
            | "enum_declaration"
    )
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
        let Some(sym_kind) = symbol_kind(child.kind()) else {
            collect_defs(child, package, containers, source, out);
            continue;
        };
        let Some(name_node) = child.child_by_field_name("name") else {
            collect_defs(child, package, containers, source, out);
            continue;
        };
        let name = text(name_node, source).to_string();
        let qpath = path::build_qpath(package, containers, &name);
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
            Some(path::build_qpath(package, containers, ""))
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
            collect_defs(child, package, containers, source, out);
            containers.pop();
        } else {
            collect_defs(child, package, containers, source, out);
        }
    }
}

fn classify_identifier(node: Node) -> Option<RefKind> {
    let parent = node.parent()?;
    let is_field = |field: &str| parent.child_by_field_name(field) == Some(node);
    match parent.kind() {
        "method_invocation" if is_field("name") => None,
        "field_access" if is_field("field") => None,
        "assignment_expression" if is_field("left") => Some(RefKind::Write),
        "variable_declarator" if is_field("name") => Some(RefKind::Write),
        "formal_parameter" | "catch_formal_parameter" => None,
        _ => Some(RefKind::Read),
    }
}

fn collect_import(n: Node, package: &str, source: &[u8], out: &mut Vec<Import>) {
    let mut cursor = n.walk();
    let path_node = n
        .named_children(&mut cursor)
        .find(|c| matches!(c.kind(), "scoped_identifier" | "identifier"));
    if let Some(pn) = path_node {
        let full = text(pn, source).to_string();
        let name = full.rsplit('.').next().unwrap_or(&full).to_string();
        out.push(Import {
            source: package.to_string(),
            module: full,
            name: Some(name),
            location: location_of(n),
        });
    }
}

impl LanguageExtractor for JavaExtractor {
    fn language(&self) -> &'static str {
        "java"
    }

    fn extensions(&self) -> &'static [&'static str] {
        &["java"]
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
        let disambiguated = path::disambiguate(&qpaths);
        for (sym, q) in symbols.iter_mut().zip(disambiguated) {
            sym.qpath = q;
        }

        let mut references = Vec::new();
        let mut imports = Vec::new();
        each_node(root, &mut |n| match n.kind() {
            "method_invocation" => {
                if let Some(name) = n.child_by_field_name("name") {
                    references.push(Reference {
                        name: text(name, source).to_string(),
                        location: location_of(name),
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
            "import_declaration" => collect_import(n, &package, source, &mut imports),
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
