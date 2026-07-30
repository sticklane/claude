#!/usr/bin/env python3
"""Pre-flight gate for /breakdown acceptance commands.

The helper checks explicit repository paths against the current surface-inventory
classifications. Any `retain` disposition blocks dispatch because `/drain` workers
cannot legally edit those surfaces. A path outside every namespace
`scripts/inventory-core-surface.py` scans can never be a surface, so it reports a
separate out-of-namespace note and passes instead of refusing.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys
import tempfile
from types import ModuleType
from typing import Any


def load_manifest(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover
        print(f"{path}: invalid inventory json ({exc})", file=sys.stderr)
        return None


def inventory_surfaces(root: pathlib.Path, baseline: pathlib.Path) -> dict[str, str]:
    baseline = baseline.resolve()
    if not baseline.is_absolute():
        baseline = root / baseline
    fragment_dir = baseline.parent / "surface-inventory"

    paths = [baseline]
    if fragment_dir.is_dir():
        paths.extend(sorted(fragment_dir.glob("*.json")))

    dispositions: dict[str, str] = {}
    for manifest_path in paths:
        manifest = load_manifest(manifest_path)
        if not manifest:
            continue
        for surface in manifest.get("surfaces", []):
            if not isinstance(surface, dict):
                continue
            path = surface.get("path")
            disposition = surface.get("disposition")
            if (
                isinstance(path, str)
                and isinstance(disposition, str)
                and not path.startswith("/")
                and ".." not in pathlib.PurePosixPath(path).parts
            ):
                dispositions[path] = disposition
    return dispositions


def inventory_module_candidates(root: pathlib.Path) -> list[pathlib.Path]:
    relative = pathlib.Path("scripts/inventory-core-surface.py")
    candidates = [root / relative]
    here = pathlib.Path(__file__).resolve()
    if len(here.parents) > 3:
        candidates.append(here.parents[3] / relative)
    return candidates


def import_inventory_module(root: pathlib.Path) -> ModuleType | None:
    for candidate in inventory_module_candidates(root):
        if not candidate.is_file():
            continue
        spec = importlib.util.spec_from_file_location(
            "inventory_core_surface",
            candidate,
        )
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:  # pragma: no cover
            del sys.modules[spec.name]
            print(f"{candidate}: cannot import ({exc})", file=sys.stderr)
            return None
        return module
    return None


def is_repo_relative(path: str) -> bool:
    posix = pathlib.PurePosixPath(path)
    return (
        not posix.is_absolute()
        and not path.startswith("/")
        and ".." not in posix.parts
        and posix.name != ""
    )


def discover_surfaces_would_find(module: ModuleType, path: str) -> bool:
    with tempfile.TemporaryDirectory() as probe_dir:
        probe_root = pathlib.Path(probe_dir)
        target = probe_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
        live, _ = module.discover_surfaces(probe_root)
    return any(surface.path == path for surface in live.values())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check /breakdown criterion paths")
    parser.add_argument(
        "--baseline",
        default="specs/toolkit-core-simplification/BASELINE.json",
        help="Surface inventory baseline JSON",
    )
    parser.add_argument(
        "--path",
        action="append",
        required=True,
        help="Repo-relative path touched by the acceptance criterion",
    )
    args = parser.parse_args(argv)

    root = pathlib.Path.cwd()
    surfaces = inventory_surfaces(root, pathlib.Path(args.baseline))
    module = import_inventory_module(root)
    if module is None:
        print(
            "scripts/inventory-core-surface.py unavailable; every unclassified "
            "path is treated as in-namespace",
            file=sys.stderr,
        )

    blocked = False
    for path in args.path:
        disposition = surfaces.get(path)
        if disposition is None:
            if (
                module is not None
                and is_repo_relative(path)
                and not discover_surfaces_would_find(module, path)
            ):
                print(
                    f"out-of-inventory-namespace: {path} lies outside every "
                    "namespace discover_surfaces scans, so it can never be a "
                    "classified surface",
                    file=sys.stderr,
                )
                continue
            print(f"Unclassified surface path: {path}", file=sys.stderr)
            blocked = True
            continue
        if disposition == "retain":
            print(
                f"retain-disposition refusal: {path} is classified retain",
                file=sys.stderr,
            )
            blocked = True

    if blocked:
        print(
            "Unblock: manual decision required for retain-or-unclassified path",
            file=sys.stderr,
        )
        return 1

    print("preflight: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
