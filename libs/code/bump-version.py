#!/usr/bin/env python3
"""Bump the `zjcode` version in all tracked locations.

This is a single-package variant of the monorepo bump script, scoped
to this package (`libs/code`). It updates:

1. `pyproject.toml`             — the `[project].version` field.
2. `deepagents_code/_version.py` — the `__version__` string
   (identified by the `# x-release-please-version` trailing comment).
3. `../../.release-please-manifest.json` (monorepo root, optional)
   — release-please's state cursor. Skipped automatically when the
   manifest is not present (e.g. this package is used standalone).

Usage:
    python bump-version.py <new-version>
    python bump-version.py --show
    python bump-version.py --dry-run 0.1.31

Examples:
    python bump-version.py 0.1.31
    python bump-version.py 0.1.31 --dry-run

Notes:
    - This script only edits files. It does NOT commit, tag, or push.
    - After running, regenerate the lockfile:
        uv lock
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# `libs/code/` — the package root
PKG_ROOT = Path(__file__).resolve().parent
# Repo root (monorepo). May not exist if the package was extracted.
REPO_ROOT = PKG_ROOT.parent.parent

PYPROJECT_PATH = PKG_ROOT / "pyproject.toml"
VERSION_PY_PATH = PKG_ROOT / "deepagents_code" / "_version.py"
MANIFEST_PATH = REPO_ROOT / ".release-please-manifest.json"

# The key used inside `.release-please-manifest.json` for this package.
MANIFEST_KEY = "libs/code"

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


def read_pyproject_version(path: Path) -> str:
    text = path.read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        msg = f'No top-level `version = "..."` found in {path}'
        raise SystemExit(msg)
    return match.group(1)


def read_version_py(path: Path) -> str:
    text = path.read_text()
    match = re.search(
        r'^__version__\s*=\s*"([^"]+)".*# x-release-please-version',
        text,
        re.MULTILINE,
    )
    if not match:
        msg = (
            f'No `__version__ = "..."  # x-release-please-version` '
            f"line found in {path}."
        )
        raise SystemExit(msg)
    return match.group(1)


def read_manifest_version(path: Path, key: str) -> str | None:
    if not path.exists():
        return None
    manifest = json.loads(path.read_text())
    return manifest.get(key)


def bump_pyproject(path: Path, new_version: str) -> str:
    text = path.read_text()
    pattern = re.compile(r'^(version\s*=\s*")([^"]+)(")', re.MULTILINE)
    match = pattern.search(text)
    if not match:
        msg = f'No top-level `version = "..."` found in {path}'
        raise SystemExit(msg)
    old = match.group(2)
    new_text = pattern.sub(rf"\g<1>{new_version}\g<3>", text, count=1)
    path.write_text(new_text)
    return old


def bump_version_py(path: Path, new_version: str) -> str:
    text = path.read_text()
    pattern = re.compile(
        r'^(__version__\s*=\s*")([^"]+)(".*# x-release-please-version.*)$',
        re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        msg = (
            f'No `__version__ = "..."  # x-release-please-version` '
            f"line found in {path}. This anchor is required for "
            f"release-please to keep tracking this file."
        )
        raise SystemExit(msg)
    old = match.group(2)
    new_text = pattern.sub(rf"\g<1>{new_version}\g<3>", text, count=1)
    path.write_text(new_text)
    return old


def bump_manifest(path: Path, key: str, new_version: str) -> str:
    with path.open() as f:
        manifest = json.load(f)
    if key not in manifest:
        msg = f"Package key {key!r} not found in {path}"
        raise SystemExit(msg)
    old = manifest[key]
    manifest[key] = new_version
    with path.open("w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    return old


def cmd_show() -> int:
    py = read_pyproject_version(PYPROJECT_PATH)
    ver = read_version_py(VERSION_PY_PATH)
    mf = read_manifest_version(MANIFEST_PATH, MANIFEST_KEY)

    print(f"  pyproject.toml               : {py}")
    print(f"  deepagents_code/_version.py  : {ver}")
    if mf is None:
        print(f"  .release-please-manifest.json : (not found — skipped)")
    else:
        print(f"  .release-please-manifest.json [{MANIFEST_KEY}]: {mf}")

    versions = {py, ver} | ({mf} if mf else set())
    if len(versions) > 1:
        print()
        print("warning: versions are NOT in sync.")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bump the `deepagents-code` package version.",
    )
    parser.add_argument(
        "version",
        nargs="?",
        help="New version (semver, e.g. 0.1.31).",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show current versions in all tracked locations.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files.",
    )
    args = parser.parse_args()

    if args.show:
        return cmd_show()

    if not args.version:
        parser.print_help()
        return 2

    if not SEMVER_RE.match(args.version):
        print(f"error: {args.version!r} is not a valid semver", file=sys.stderr)
        return 2

    for p in (PYPROJECT_PATH, VERSION_PY_PATH):
        if not p.exists():
            msg = f"Missing file: {p}"
            raise SystemExit(msg)

    has_manifest = MANIFEST_PATH.exists()

    print(f"Package: deepagents-code ({PKG_ROOT})")
    print(f"New version: {args.version}")
    print()

    if args.dry_run:
        cur_py = read_pyproject_version(PYPROJECT_PATH)
        cur_ver = read_version_py(VERSION_PY_PATH)
        cur_mf = read_manifest_version(MANIFEST_PATH, MANIFEST_KEY)
        print("[dry-run] Would update:")
        print(f"  pyproject.toml              : {cur_py} -> {args.version}")
        print(f"  deepagents_code/_version.py : {cur_ver} -> {args.version}")
        if has_manifest and cur_mf is not None:
            print(
                f"  .release-please-manifest.json "
                f"[{MANIFEST_KEY}] : {cur_mf} -> {args.version}"
            )
        else:
            print("  .release-please-manifest.json : (not found — will be skipped)")
        return 0

    old_py = bump_pyproject(PYPROJECT_PATH, args.version)
    old_ver = bump_version_py(VERSION_PY_PATH, args.version)
    old_manifest: str | None = None
    if has_manifest:
        old_manifest = bump_manifest(MANIFEST_PATH, MANIFEST_KEY, args.version)

    print(f"  pyproject.toml              : {old_py} -> {args.version}")
    print(f"  deepagents_code/_version.py : {old_ver} -> {args.version}")
    if old_manifest is not None:
        print(
            f"  .release-please-manifest.json [{MANIFEST_KEY}] : "
            f"{old_manifest} -> {args.version}"
        )
    else:
        print("  .release-please-manifest.json : (not found — skipped)")

    prior = {old_py, old_ver} | ({old_manifest} if old_manifest else set())
    if len(prior) > 1:
        print()
        print("warning: previous versions were NOT in sync across files:")
        print(f"  pyproject.toml : {old_py}")
        print(f"  _version.py    : {old_ver}")
        if old_manifest is not None:
            print(f"  manifest       : {old_manifest}")
        print("They are now all set to the new version.")

    print()
    print("Next steps:")
    print("  uv lock       # regenerate lockfile")
    print("  git diff      # review changes")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
