#!/usr/bin/env python3
"""Bump a monorepo package's version in all three locations at once.

The three locations for each package (as configured in
`release-please-config.json`):

1. `libs/<pkg>/pyproject.toml` — the `[project].version` field.
2. `libs/<pkg>/<module>/_version.py` — the `__version__` string
   (identified by the `# x-release-please-version` trailing comment).
3. `.release-please-manifest.json` — release-please's state cursor.

Usage:
    python scripts/bump-version.py <package> <new-version>
    python scripts/bump-version.py --list

Examples:
    python scripts/bump-version.py libs/code 0.1.31
    python scripts/bump-version.py deepagents-code 0.1.31   # by package-name
    python scripts/bump-version.py code 0.1.31              # by short alias

Notes:
    - This script only edits files. It does NOT commit, tag, or push.
    - Normal releases should go through release-please via Conventional
      Commits on `main`. Only use this for manual bumps (local debug,
      fixing manifest drift, staging branches).
    - After running, regenerate the affected package's lockfile:
        (cd libs/<pkg> && uv lock)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "release-please-config.json"
MANIFEST_PATH = REPO_ROOT / ".release-please-manifest.json"

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


def load_config() -> dict:
    with CONFIG_PATH.open() as f:
        return json.load(f)


def resolve_package(config: dict, key: str) -> tuple[str, dict]:
    """Resolve a user-provided key to (package_path, package_config).

    Accepts:
      - full path: "libs/code", "libs/partners/quickjs"
      - package-name: "deepagents-code", "langchain-quickjs"
      - short alias: last path segment, e.g. "code", "quickjs"
    """
    packages: dict = config["packages"]

    if key in packages:
        return key, packages[key]

    for path, pkg in packages.items():
        if pkg.get("package-name") == key or pkg.get("component") == key:
            return path, pkg

    for path, pkg in packages.items():
        if path.split("/")[-1] == key:
            return path, pkg

    valid = ", ".join(sorted(packages))
    msg = f"Unknown package {key!r}. Valid paths: {valid}"
    raise SystemExit(msg)


def bump_pyproject(path: Path, new_version: str) -> str:
    text = path.read_text()
    pattern = re.compile(r'^(version\s*=\s*")([^"]+)(")', re.MULTILINE)
    match = pattern.search(text)
    if not match:
        msg = f"No top-level `version = \"...\"` found in {path}"
        raise SystemExit(msg)
    old = match.group(2)
    new_text = pattern.sub(rf'\g<1>{new_version}\g<3>', text, count=1)
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
            f"No `__version__ = \"...\"  # x-release-please-version` "
            f"line found in {path}. This anchor is required for "
            f"release-please to keep tracking this file."
        )
        raise SystemExit(msg)
    old = match.group(2)
    new_text = pattern.sub(rf'\g<1>{new_version}\g<3>', text, count=1)
    path.write_text(new_text)
    return old


def bump_manifest(path: Path, package_path: str, new_version: str) -> str:
    with path.open() as f:
        manifest = json.load(f)
    if package_path not in manifest:
        msg = f"Package path {package_path!r} not found in {path}"
        raise SystemExit(msg)
    old = manifest[package_path]
    manifest[package_path] = new_version
    # Preserve original key order; json.dump with indent=2 and a
    # trailing newline matches the existing file style.
    with path.open("w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    return old


def cmd_list(config: dict) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    rows = []
    for path, pkg in config["packages"].items():
        rows.append((path, pkg.get("package-name", "?"), manifest.get(path, "?")))
    width_path = max(len(r[0]) for r in rows)
    width_name = max(len(r[1]) for r in rows)
    for path, name, ver in rows:
        print(f"  {path:<{width_path}}  {name:<{width_name}}  {ver}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bump a monorepo package version in all three locations.",
    )
    parser.add_argument(
        "package",
        nargs="?",
        help="Package path (libs/code), package-name (deepagents-code), "
        "or short alias (code).",
    )
    parser.add_argument(
        "version",
        nargs="?",
        help="New version (semver, e.g. 0.1.31).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all packages and their current versions.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files.",
    )
    args = parser.parse_args()

    config = load_config()

    if args.list:
        cmd_list(config)
        return 0

    if not args.package or not args.version:
        parser.print_help()
        return 2

    if not SEMVER_RE.match(args.version):
        print(f"error: {args.version!r} is not a valid semver", file=sys.stderr)
        return 2

    package_path, pkg_config = resolve_package(config, args.package)

    extra_files = pkg_config.get("extra-files", [])
    pyproject_rel = next((f for f in extra_files if f.endswith("pyproject.toml")), None)
    version_py_rel = next((f for f in extra_files if f.endswith("_version.py")), None)

    if not pyproject_rel or not version_py_rel:
        msg = (
            f"Package {package_path!r} is missing expected extra-files "
            f"(pyproject.toml and _version.py). extra-files={extra_files}"
        )
        raise SystemExit(msg)

    pyproject_abs = REPO_ROOT / package_path / pyproject_rel
    version_py_abs = REPO_ROOT / package_path / version_py_rel

    for p in (pyproject_abs, version_py_abs, MANIFEST_PATH):
        if not p.exists():
            msg = f"Missing file: {p}"
            raise SystemExit(msg)

    print(f"Package: {package_path} ({pkg_config.get('package-name', '?')})")
    print(f"New version: {args.version}")
    print()

    if args.dry_run:
        # Read old values without writing.
        current = json.loads(MANIFEST_PATH.read_text()).get(package_path, "?")
        print(f"[dry-run] Would update 3 files (current manifest: {current}):")
        print(f"  - {pyproject_abs.relative_to(REPO_ROOT)}")
        print(f"  - {version_py_abs.relative_to(REPO_ROOT)}")
        print(f"  - {MANIFEST_PATH.relative_to(REPO_ROOT)}")
        return 0

    old_py = bump_pyproject(pyproject_abs, args.version)
    old_ver = bump_version_py(version_py_abs, args.version)
    old_manifest = bump_manifest(MANIFEST_PATH, package_path, args.version)

    print(f"  {pyproject_abs.relative_to(REPO_ROOT)}: {old_py} -> {args.version}")
    print(f"  {version_py_abs.relative_to(REPO_ROOT)}: {old_ver} -> {args.version}")
    print(
        f"  {MANIFEST_PATH.relative_to(REPO_ROOT)} "
        f"[{package_path}]: {old_manifest} -> {args.version}"
    )

    if old_py != old_ver or old_py != old_manifest:
        print()
        print("warning: previous versions were NOT in sync across the 3 files:")
        print(f"  pyproject.toml : {old_py}")
        print(f"  _version.py    : {old_ver}")
        print(f"  manifest       : {old_manifest}")
        print("They are now all set to the new version.")

    print()
    print("Next steps:")
    print(f"  (cd {package_path} && uv lock)")
    print("  git diff  # review changes")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
