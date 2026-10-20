#!/usr/bin/env python3
"""Fail when the plugin folder breaks an Anthropic plugin directory file limit.

Limits come from the pre-submission checklist, checked on 2026-10-20:
https://claude.com/docs/plugins/pre-submission-checklist.md

`claude plugin validate` checks that manifests are well-formed; it does not check
these limits. Only Git-tracked files count, because the directory reads the
repository as GitHub archives it. Standard library only.

Usage: check_directory_limits.py [plugin_folder] [--repo ROOT]
"""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath

MAX_PLUGIN_FILES = 512  # held for a reviewer above this
MAX_TEXT_BYTES = 256 * 1024  # held: any file that is not an image or font
MAX_ANY_BYTES = 5 * 1024 * 1024  # validation stops
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024  # validation stops
MAX_UNPACKED_BYTES = 256 * 1024 * 1024  # validation stops
MAX_REPO_ENTRIES = 10_000  # files and folders; validation stops
JUNK_NAMES = {".ds_store", "thumbs.db", "desktop.ini", "__macosx"}
WINDOWS_DEVICES = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
WINDOWS_FORBIDDEN = re.compile(r'[<>:"|?*\x00-\x1f]')
PATH_SEGMENT = re.compile(r"^[A-Za-z0-9._-]+$")
FORBIDDEN_ATTRIBUTES = re.compile(r"(?:^|\s)-?(export-ignore|export-subst|filter)(?:=|\s|$)")
IMAGE_MAGIC = (
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpeg"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
)
FONT_MAGIC = (b"\x00\x01\x00\x00", b"OTTO", b"true", b"wOFF", b"wOF2", b"ttcf")


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout


def kind(data: bytes) -> str:
    """Return text, image, font, or binary from the file's bytes."""
    for magic, _ in IMAGE_MAGIC:
        if data.startswith(magic):
            return "image"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image"
    if data.startswith(FONT_MAGIC):
        return "font"
    if b"\x00" in data[:8192]:
        return "binary"
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return "binary"
    return "text"


def check(repo: Path, plugin: Path) -> tuple[list[str], dict[str, object]]:
    failures: list[str] = []
    prefix = plugin.relative_to(repo).as_posix()
    for segment in PurePosixPath(prefix).parts:
        if not PATH_SEGMENT.match(segment):
            failures.append(f"plugin path segment has characters other than letters, digits, dots, hyphens, underscores: {segment}")
    staged = git(repo, "ls-files", "-s", "-z").decode("utf-8").split("\0")
    tracked: list[tuple[str, str]] = []
    for line in filter(None, staged):
        meta, path = line.split("\t", 1)
        tracked.append((meta.split()[0], path))
    if (repo / ".gitmodules").exists():
        failures.append("Git submodules are not allowed: .gitmodules")
    seen: dict[str, str] = {}
    for mode, path in tracked:
        lowered = path.lower()
        if lowered in seen:
            failures.append(f"names differ only by capitalization: {seen[lowered]} and {path}")
        seen[lowered] = path
        for part in PurePosixPath(path).parts:
            stem = part.split(".", 1)[0].lower()
            if WINDOWS_FORBIDDEN.search(part) or part.endswith((".", " ")) or stem in WINDOWS_DEVICES:
                failures.append(f"name is invalid on Windows: {path}")
                break
        if part_is_junk(path):
            failures.append(f"operating-system junk file: {path}")
        if mode == "120000":
            failures.append(f"symbolic link: {path}")
        if mode == "160000":
            failures.append(f"Git submodule: {path}")
        if PurePosixPath(path).name == ".gitattributes":
            for number, rule in enumerate((repo / path).read_text(encoding="utf-8").splitlines(), 1):
                found = FORBIDDEN_ATTRIBUTES.search(rule.split("#", 1)[0])
                if found:
                    failures.append(f"{path}:{number} sets {found.group(1)}, which stops directory validation")
    plugin_files = [path for _, path in tracked if path == prefix or path.startswith(prefix + "/")]
    if len(plugin_files) > MAX_PLUGIN_FILES:
        failures.append(f"plugin folder has {len(plugin_files)} files; the limit is {MAX_PLUGIN_FILES}")
    for path in plugin_files:
        data = (repo / path).read_bytes()
        if data.startswith(b"version https://git-lfs.github.com/spec/"):
            failures.append(f"Git LFS pointer: {path}")
        file_kind = kind(data)
        if len(data) >= MAX_ANY_BYTES:
            failures.append(f"file is {len(data)} bytes; every file must be under {MAX_ANY_BYTES}: {path}")
        elif file_kind not in {"image", "font"} and len(data) > MAX_TEXT_BYTES:
            failures.append(f"file is {len(data)} bytes; files other than images and fonts must be at most {MAX_TEXT_BYTES}: {path}")
        if file_kind == "binary":
            failures.append(f"binary file other than PNG, JPEG, GIF, WebP, or a font: {path}")
    archive = git(repo, "archive", "--format=tar", "HEAD")
    if len(archive) >= MAX_ARCHIVE_BYTES:
        failures.append(f"repository archive is {len(archive)} bytes; the limit is {MAX_ARCHIVE_BYTES}")
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        members = tar.getmembers()
    unpacked = sum(member.size for member in members)
    if unpacked >= MAX_UNPACKED_BYTES:
        failures.append(f"repository is {unpacked} bytes unpacked; the limit is {MAX_UNPACKED_BYTES}")
    if len(members) >= MAX_REPO_ENTRIES:
        failures.append(f"repository has {len(members)} files and folders; the limit is {MAX_REPO_ENTRIES}")
    return failures, {
        "plugin": prefix,
        "plugin_files": len(plugin_files),
        "archive_bytes": len(archive),
        "unpacked_bytes": unpacked,
        "repository_entries": len(members),
    }


def part_is_junk(path: str) -> bool:
    return any(part.lower() in JUNK_NAMES for part in PurePosixPath(path).parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plugin", nargs="?", type=Path, default=Path("plugins/lago"))
    parser.add_argument("--repo", type=Path, help="repository root; defaults to the plugin folder's Git top level")
    args = parser.parse_args()
    plugin = args.plugin.resolve()
    repo = (args.repo or Path(git(plugin, "rev-parse", "--show-toplevel").decode().strip())).resolve()
    failures, counts = check(repo, plugin)
    print(json.dumps({"status": "PASS" if not failures else "FAIL", **counts, "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
