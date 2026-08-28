#!/usr/bin/env python3
"""Create or verify a deterministic SHA-256 manifest for the plugin bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


IGNORED_PARTS = {".git", ".pytest_cache", ".venv", "__pycache__"}
MANIFEST_NAME = "RELEASE-MANIFEST.json"
MAX_FILE_BYTES = 50_000_000


class IntegrityError(ValueError):
    """The bundle cannot be represented or verified safely."""


def digest(path: Path) -> str:
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise IntegrityError(f"file exceeds {MAX_FILE_BYTES} bytes: {path}")
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def bundle_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if any(part in IGNORED_PARTS for part in path.parts):
            continue
        if path.name in {MANIFEST_NAME, ".DS_Store"}:
            continue
        if path.is_symlink():
            raise IntegrityError(f"symbolic links are not allowed in the release bundle: {path}")
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            files[relative] = digest(path)
    return files


def safe_manifest_files(root: Path, value: object) -> dict[str, str]:
    if not isinstance(value, dict) or value.get("schema") != 1:
        raise IntegrityError("manifest schema must be 1")
    if value.get("algorithm") != "sha256":
        raise IntegrityError("manifest algorithm must be sha256")
    files = value.get("files")
    if not isinstance(files, dict) or not files:
        raise IntegrityError("manifest files must be a non-empty object")
    checked: dict[str, str] = {}
    for raw_path, raw_digest in files.items():
        if not isinstance(raw_path, str) or not isinstance(raw_digest, str):
            raise IntegrityError("manifest paths and digests must be strings")
        relative = PurePosixPath(raw_path)
        if relative.is_absolute() or ".." in relative.parts or raw_path == MANIFEST_NAME:
            raise IntegrityError(f"unsafe manifest path: {raw_path}")
        if not re_full_sha256(raw_digest):
            raise IntegrityError(f"invalid SHA-256 for {raw_path}")
        resolved = (root / Path(*relative.parts)).resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError as error:
            raise IntegrityError(f"manifest path escapes bundle: {raw_path}") from error
        checked[raw_path] = raw_digest
    return checked


def re_full_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def create(root: Path, output: Path) -> dict[str, object]:
    files = bundle_files(root)
    manifest = {"schema": 1, "algorithm": "sha256", "files": files}
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"status": "PASS", "files": len(files), "output": str(output)}


def check(root: Path, manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = safe_manifest_files(root, manifest)
    actual = bundle_files(root)
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    changed = sorted(
        path for path in expected.keys() & actual.keys() if expected[path] != actual[path]
    )
    return {
        "status": "PASS" if not (missing or unexpected or changed) else "FAIL",
        "files": len(expected),
        "missing": missing,
        "unexpected": unexpected,
        "changed": changed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("root", type=Path)
    create_parser.add_argument("--output", type=Path, required=True)
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("root", type=Path)
    check_parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        if args.command == "create":
            result = create(root, args.output.resolve())
        else:
            result = check(root, args.manifest.resolve())
    except (OSError, UnicodeError, json.JSONDecodeError, IntegrityError) as error:
        result = {"status": "FAIL", "error": str(error)}
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
