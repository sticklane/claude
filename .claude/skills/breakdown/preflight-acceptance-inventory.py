#!/usr/bin/env python3
"""Pre-flight gate for /breakdown acceptance commands.

The helper checks explicit repository paths against the current surface-inventory
classifications. Any `retain` disposition blocks dispatch because `/drain` workers
cannot legally edit those surfaces.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
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

    blocked = False
    for path in args.path:
        disposition = surfaces.get(path)
        if disposition is None:
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
