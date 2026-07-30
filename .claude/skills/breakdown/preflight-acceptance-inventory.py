#!/usr/bin/env python3
"""Pre-flight gate for /breakdown acceptance commands.

The helper checks explicit repository paths against the current surface-inventory
classifications. Any `retain` disposition blocks dispatch because `/drain` workers
cannot legally edit those surfaces. A queried path that is not itself a surface
identity is resolved to the classified surface that owns it, so a file beside a
`SKILL.md` inherits that skill's disposition. A path owning nothing and owned by
nothing reports a separate out-of-namespace note and passes instead of refusing.
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


class Classifications:
    def __init__(self) -> None:
        self.by_path: dict[str, str] = {}
        self.by_identity: dict[str, str] = {}


def inventory_surfaces(root: pathlib.Path, baseline: pathlib.Path) -> Classifications:
    baseline = baseline.resolve()
    if not baseline.is_absolute():
        baseline = root / baseline
    fragment_dir = baseline.parent / "surface-inventory"

    paths = [baseline]
    if fragment_dir.is_dir():
        paths.extend(sorted(fragment_dir.glob("*.json")))

    classifications = Classifications()
    for manifest_path in paths:
        manifest = load_manifest(manifest_path)
        if not manifest:
            continue
        for surface in manifest.get("surfaces", []):
            if not isinstance(surface, dict):
                continue
            path = surface.get("path")
            identity = surface.get("identity")
            disposition = surface.get("disposition")
            if not isinstance(disposition, str):
                continue
            if (
                isinstance(path, str)
                and not path.startswith("/")
                and ".." not in pathlib.PurePosixPath(path).parts
            ):
                classifications.by_path[path] = disposition
                if isinstance(identity, str) and identity:
                    classifications.by_identity[identity] = disposition
    return classifications


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


def surfaces_by_directory(
    module: ModuleType, root: pathlib.Path
) -> dict[str, list[Any]]:
    live, _ = module.discover_surfaces(root)
    grouped: dict[str, list[Any]] = {}
    for surface in live.values():
        directory = pathlib.PurePosixPath(surface.path).parent.as_posix()
        grouped.setdefault(directory, []).append(surface)
    return grouped


def owning_surface_identities(
    grouped: dict[str, list[Any]],
    classified: dict[str, str],
    path: str,
) -> list[str]:
    for directory in pathlib.PurePosixPath(path).parents:
        residents = grouped.get(directory.as_posix())
        if not residents:
            continue
        if len({surface.path for surface in residents}) != 1:
            return []
        return sorted(
            surface.identity for surface in residents if surface.identity in classified
        )
    return []


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
    classifications = inventory_surfaces(root, pathlib.Path(args.baseline))
    module = import_inventory_module(root)
    grouped: dict[str, list[Any]] = {}
    if module is None:
        print(
            "scripts/inventory-core-surface.py unavailable; every unclassified "
            "path is treated as in-namespace",
            file=sys.stderr,
        )
    else:
        grouped = surfaces_by_directory(module, root)

    blocked = False
    for path in args.path:
        disposition = classifications.by_path.get(path)
        if disposition is not None:
            if disposition == "retain":
                print(
                    f"retain-disposition refusal: {path} is classified retain",
                    file=sys.stderr,
                )
                blocked = True
            continue

        if module is None or not is_repo_relative(path):
            print(f"Unclassified surface path: {path}", file=sys.stderr)
            blocked = True
            continue

        is_surface_identity = discover_surfaces_would_find(module, path)
        if not is_surface_identity:
            print(
                f"out-of-inventory-namespace: {path} is not a surface identity "
                "discover_surfaces would produce",
                file=sys.stderr,
            )

        owners = owning_surface_identities(
            grouped,
            classifications.by_identity,
            path,
        )
        if owners:
            print(
                f"owning-surface: {path} is owned by {', '.join(owners)}",
                file=sys.stderr,
            )
            retained = [
                identity
                for identity in owners
                if classifications.by_identity[identity] == "retain"
            ]
            if retained:
                print(
                    f"retain-disposition refusal: {path} is owned by "
                    f"{', '.join(retained)}, classified retain",
                    file=sys.stderr,
                )
                blocked = True
            continue

        if is_surface_identity:
            print(f"Unclassified surface path: {path}", file=sys.stderr)
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
