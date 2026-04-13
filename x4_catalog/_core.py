"""
XRCatTool-equivalent for Linux: read, list, extract, pack, and diff X4 .cat/.dat archives.

Format (per community docs and Egosoft's XRCatTool readme):
- Each line in a .cat file: ``<filepath> <size> <unix_mtime> <md5hex>``
- Filenames may contain spaces; the last three space-separated fields are fixed.
- The matching .dat file stores file payloads consecutively in .cat line order.
- Later numbered catalogs override earlier ones for the same virtual path.
- Extensions use ``ext_NN.cat`` (extension-local) and ``subst_NN.cat`` (base-game override).
- Version-specific catalogs (``ext_vNNN.cat``, ``subst_vNNN.cat``) are supported.

Usage::

    # List all files in the game install
    x4cat list /path/to/X4\\ Foundations

    # List only MD scripts
    x4cat list /path/to/X4\\ Foundations -g 'md/*.xml'

    # List with regex include/exclude
    x4cat list /path/to/X4\\ Foundations --include '^aiscripts/' --exclude '\\.xsd$'

    # Extract AI scripts to a working directory
    x4cat extract /path/to/X4\\ Foundations -o ./unpacked -g 'aiscripts/*'

    # Extract everything from a DLC extension
    x4cat extract /path/to/X4\\ Foundations/extensions/ego_dlc_boron -o ./boron -p ext_

    # Pack loose files into a catalog
    x4cat pack ./my_mod_files -o ./my_mod/ext_01.cat

    # Append more files to an existing catalog
    x4cat pack ./extra_files -o ./my_mod/ext_01.cat --append

    # Generate a diff catalog (only new/changed files)
    x4cat diff --base ./original --mod ./modified -o ./my_mod/ext_01.cat
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

logger = logging.getLogger(__name__)

type _CmdHandler = Callable[[argparse.Namespace], int]


@dataclass(frozen=True, slots=True)
class CatEntry:
    """One entry from a .cat index line."""

    path: str
    size: int
    mtime: int
    md5: str
    cat_path: Path
    dat_offset: int


_MD5_RE = re.compile(r"^[0-9a-fA-F]{32}$")


def parse_cat_line(line: str) -> CatEntry:
    """Parse a single .cat index line into a CatEntry (without catalog context).

    Raises ``ValueError`` on blank/malformed lines, negative sizes,
    or invalid MD5 hashes.
    """
    stripped = line.strip()
    if not stripped:
        raise ValueError("empty line")
    # path may contain spaces; last 3 tokens are always size, mtime, md5
    parts = stripped.rsplit(" ", 3)
    if len(parts) != 4:
        raise ValueError(
            f"Malformed catalog line (expected >=4 space-separated fields): {stripped!r}"
        )
    raw_path, size_s, mtime_s, md5 = parts

    size = int(size_s)
    if size < 0:
        raise ValueError(f"Negative size: {size}")
    mtime = int(mtime_s)
    if mtime < 0:
        raise ValueError(f"Negative mtime: {mtime}")
    md5 = md5.strip()
    if not _MD5_RE.match(md5):
        raise ValueError(f"Invalid MD5 hash: {md5!r}")

    normalized = raw_path.replace("\\", "/").lstrip("/")
    return CatEntry(
        path=normalized,
        size=size,
        mtime=mtime,
        md5=md5,
        cat_path=Path(),  # placeholder — caller fills in real value
        dat_offset=0,  # placeholder
    )


def iter_cat_files(directory: Path, prefix: str = "") -> list[Path]:
    """Return .cat files matching ``{prefix}NN.cat`` sorted by numeric id.

    Default prefix "" matches base-game catalogs (01.cat, 02.cat, ...).
    Use prefix="ext_" for extension catalogs, "subst_" for substitution catalogs.
    Signature catalogs (``*_sig.cat``) are always excluded.
    """
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)\.cat$", re.IGNORECASE)
    cats: list[tuple[int, Path]] = []
    if not directory.is_dir():
        return []
    for p in directory.iterdir():
        if not p.is_file():
            continue
        if p.name.endswith("_sig.cat"):
            continue
        m = pattern.match(p.name)
        if m:
            cats.append((int(m.group(1)), p))
    cats.sort(key=lambda x: x[0])
    return [p for _, p in cats]


def _read_cat_index(cat_path: Path) -> list[CatEntry]:
    """Parse every line in a .cat file into CatEntry objects with correct offsets."""
    entries: list[CatEntry] = []
    offset = 0
    with open(cat_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                stub = parse_cat_line(line)
            except ValueError as exc:
                logger.warning("Skipping malformed line in %s: %s", cat_path, exc)
                continue
            entry = CatEntry(
                path=stub.path,
                size=stub.size,
                mtime=stub.mtime,
                md5=stub.md5,
                cat_path=cat_path,
                dat_offset=offset,
            )
            entries.append(entry)
            offset += stub.size
    return entries


def build_vfs(
    directory: Path,
    prefix: str = "",
) -> dict[str, CatEntry]:
    """Build a virtual filesystem from all matching catalogs in *directory*.

    Later catalogs override earlier ones for the same path.
    Returns ``{normalized_path: CatEntry}``.
    """
    vfs: dict[str, CatEntry] = {}
    for cat_path in iter_cat_files(directory, prefix=prefix):
        for entry in _read_cat_index(cat_path):
            vfs[entry.path] = entry
    return vfs


def build_vfs_multi(
    sources: list[tuple[Path, str]],
) -> dict[str, CatEntry]:
    """Build a merged VFS from multiple source directories.

    *sources* is a list of ``(directory, prefix)`` tuples.
    Later sources override earlier ones for the same path, matching
    XRCatTool's ``-in path1 path2 ...`` behaviour.
    """
    vfs: dict[str, CatEntry] = {}
    for directory, prefix in sources:
        for cat_path in iter_cat_files(directory, prefix=prefix):
            for entry in _read_cat_index(cat_path):
                vfs[entry.path] = entry
    return vfs


def _filter_entries(
    entries: list[CatEntry],
    glob_pattern: str | None = None,
    include_re: str | None = None,
    exclude_re: str | None = None,
) -> list[CatEntry]:
    """Apply glob, include-regex, and exclude-regex filters to a list of entries."""
    result = entries
    if glob_pattern is not None:
        result = [e for e in result if fnmatch(e.path, glob_pattern)]
    if include_re is not None:
        compiled = re.compile(include_re)
        result = [e for e in result if compiled.search(e.path)]
    if exclude_re is not None:
        compiled = re.compile(exclude_re)
        result = [e for e in result if not compiled.search(e.path)]
    return result


def list_entries(
    directory: Path,
    glob_pattern: str | None = None,
    prefix: str = "",
    include_re: str | None = None,
    exclude_re: str | None = None,
) -> list[CatEntry]:
    """Return deduplicated entries, optionally filtered by glob and/or regex."""
    vfs = build_vfs(directory, prefix=prefix)
    entries = sorted(vfs.values(), key=lambda e: e.path)
    return _filter_entries(entries, glob_pattern, include_re, exclude_re)


def _read_payload(entry: CatEntry) -> bytes:
    """Read the raw bytes for a single CatEntry from its .dat file.

    Verifies the MD5 checksum matches the catalog index.
    """
    dat_path = entry.cat_path.with_suffix(".dat")
    with open(dat_path, "rb") as f:
        f.seek(entry.dat_offset)
        data = f.read(entry.size)
    if len(data) != entry.size:
        raise OSError(f"Short read for {entry.path}: expected {entry.size}, got {len(data)}")
    actual_md5 = hashlib.md5(data).hexdigest()
    if actual_md5 != entry.md5:
        raise OSError(f"MD5 mismatch for {entry.path}: expected {entry.md5}, got {actual_md5}")
    return data


def extract_to_disk(
    directory: Path,
    output_dir: Path,
    glob_pattern: str | None = None,
    prefix: str = "",
    include_re: str | None = None,
    exclude_re: str | None = None,
) -> list[Path]:
    """Extract files to disk, preserving directory structure and mtimes.

    Returns list of written file paths.
    """
    entries = list_entries(
        directory,
        glob_pattern=glob_pattern,
        prefix=prefix,
        include_re=include_re,
        exclude_re=exclude_re,
    )
    if not entries:
        return []

    resolved_output = output_dir.resolve()
    written: list[Path] = []
    for entry in entries:
        dest = (output_dir / entry.path).resolve()
        if not dest.is_relative_to(resolved_output):
            raise ValueError(f"Path traversal detected: {entry.path!r} escapes output directory")
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = _read_payload(entry)
        dest.write_bytes(data)
        os.utime(dest, (entry.mtime, entry.mtime))
        written.append(dest)
    return written


# --- Packing / writing catalogs ---


def _collect_loose_files(root: Path) -> list[tuple[str, Path]]:
    """Walk *root* and return ``(virtual_path, disk_path)`` sorted by virtual path.

    Symlinks are skipped to prevent packing files from outside the source tree.
    """
    pairs: list[tuple[str, Path]] = []
    for disk_path in sorted(root.rglob("*")):
        if disk_path.is_symlink() or not disk_path.is_file():
            continue
        vpath = disk_path.relative_to(root).as_posix()
        pairs.append((vpath, disk_path))
    return pairs


def _md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def pack_catalog(
    source_dir: Path,
    cat_path: Path,
    append: bool = False,
) -> int:
    """Pack loose files from *source_dir* into a .cat/.dat pair at *cat_path*.

    If *append* is True and the catalog already exists, new entries are appended
    to both the .cat index and .dat data file. An appended entry with the same
    path as an existing one overrides it when read via ``build_vfs``.

    Returns the number of files packed.
    """
    cat_path.parent.mkdir(parents=True, exist_ok=True)
    dat_path = cat_path.with_suffix(".dat")

    files = _collect_loose_files(source_dir)

    if append and cat_path.exists():
        cat_mode = "a"
        dat_mode = "ab"
    else:
        cat_mode = "w"
        dat_mode = "wb"

    with open(cat_path, cat_mode, encoding="utf-8") as cf, open(dat_path, dat_mode) as df:
        for vpath, disk_path in files:
            data = disk_path.read_bytes()
            mtime = int(disk_path.stat().st_mtime)
            md5 = _md5_bytes(data)
            cf.write(f"{vpath} {len(data)} {mtime} {md5}\n")
            df.write(data)

    return len(files)


# --- Diff generation ---


def _scan_dir_md5(root: Path) -> dict[str, str]:
    """Walk *root* and return ``{virtual_path: md5hex}``.

    Symlinks are skipped.
    """
    result: dict[str, str] = {}
    for disk_path in root.rglob("*"):
        if disk_path.is_symlink() or not disk_path.is_file():
            continue
        vpath = disk_path.relative_to(root).as_posix()
        result[vpath] = _md5_bytes(disk_path.read_bytes())
    return result


def diff_file_sets(
    base_dir: Path,
    mod_dir: Path,
) -> tuple[dict[str, Path], list[str]]:
    """Compare two directories and identify changes.

    Returns ``(changed, deleted)`` where:
    - *changed*: ``{virtual_path: disk_path_in_mod}`` for new or modified files.
    - *deleted*: list of virtual paths present in base but absent in mod.
    """
    base_hashes = _scan_dir_md5(base_dir)
    mod_hashes = _scan_dir_md5(mod_dir)

    changed: dict[str, Path] = {}
    for vpath, mod_md5 in sorted(mod_hashes.items()):
        base_md5 = base_hashes.get(vpath)
        if base_md5 != mod_md5:
            changed[vpath] = mod_dir / vpath

    deleted = sorted(vp for vp in base_hashes if vp not in mod_hashes)

    return changed, deleted


def _pack_changed(changed: dict[str, Path], cat_path: Path) -> None:
    """Write only the changed/added files into a new catalog."""
    cat_path.parent.mkdir(parents=True, exist_ok=True)
    dat_path = cat_path.with_suffix(".dat")
    with open(cat_path, "w", encoding="utf-8") as cf, open(dat_path, "wb") as df:
        for vpath in sorted(changed.keys()):
            disk_path = changed[vpath]
            data = disk_path.read_bytes()
            mtime = int(disk_path.stat().st_mtime)
            md5 = _md5_bytes(data)
            cf.write(f"{vpath} {len(data)} {mtime} {md5}\n")
            df.write(data)


def diff_and_pack(
    base_dir: Path,
    mod_dir: Path,
    cat_path: Path,
) -> tuple[int, int]:
    """Generate a diff between *base_dir* and *mod_dir*, pack changed files.

    Returns ``(num_changed, num_deleted)``.
    Deleted paths are reported but not embedded in the catalog (X4 does not
    use deletion markers in extension catalogs).
    """
    changed, deleted = diff_file_sets(base_dir, mod_dir)
    _pack_changed(changed, cat_path)
    return len(changed), len(deleted)


# --- CLI ---


def _add_filter_args(parser: argparse.ArgumentParser) -> None:
    """Add shared glob / include / exclude arguments to a subparser."""
    parser.add_argument("-g", "--glob", default=None, help="Filter by glob pattern")
    parser.add_argument(
        "--include",
        default=None,
        metavar="REGEX",
        help="Include only paths matching this regex",
    )
    parser.add_argument(
        "--exclude",
        default=None,
        metavar="REGEX",
        help="Exclude paths matching this regex",
    )


def _add_prefix_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-p",
        "--prefix",
        default="",
        help="Catalog filename prefix (default: '' for NN.cat, use 'ext_' for extensions)",
    )


def _cmd_list(args: argparse.Namespace) -> int:
    entries = list_entries(
        Path(args.game_dir),
        glob_pattern=args.glob,
        prefix=args.prefix,
        include_re=args.include,
        exclude_re=args.exclude,
    )
    for e in entries:
        print(f"{e.size:>12}  {e.path}")
    print(f"\n{len(entries)} file(s)")
    return 0


def _cmd_extract(args: argparse.Namespace) -> int:
    if not args.output:
        print("error: -o / --output is required for extract", file=sys.stderr)
        return 1
    output = Path(args.output)
    written = extract_to_disk(
        Path(args.game_dir),
        output,
        glob_pattern=args.glob,
        prefix=args.prefix,
        include_re=args.include,
        exclude_re=args.exclude,
    )
    for p in written:
        print(p)
    print(f"\n{len(written)} file(s) extracted to {output}")
    return 0


def _cmd_pack(args: argparse.Namespace) -> int:
    if not args.output:
        print("error: -o / --output is required for pack", file=sys.stderr)
        return 1
    cat_path = Path(args.output)
    count = pack_catalog(Path(args.source_dir), cat_path, append=args.append)
    action = "appended to" if args.append else "packed into"
    print(f"{count} file(s) {action} {cat_path}")
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    if not args.output:
        print("error: -o / --output is required for diff", file=sys.stderr)
        return 1
    cat_path = Path(args.output)
    base_dir, mod_dir = Path(args.base), Path(args.mod)
    changed, deleted = diff_file_sets(base_dir, mod_dir)
    _pack_changed(changed, cat_path)
    print(f"{len(changed)} changed/added, {len(deleted)} deleted")
    if deleted:
        print("\nDeleted files (not in catalog — handle via XML diff patches):")
        for d in deleted:
            print(f"  - {d}")
    if changed:
        print(f"\nDiff catalog written to {cat_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="x4cat",
        description="List, extract, pack, and diff X4: Foundations .cat/.dat archives.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- list --
    p_list = sub.add_parser("list", aliases=["ls"], help="List archive contents")
    p_list.add_argument("game_dir", help="Path to X4 install or extension directory")
    _add_filter_args(p_list)
    _add_prefix_arg(p_list)

    # -- extract --
    p_ext = sub.add_parser("extract", aliases=["x"], help="Extract files to disk")
    p_ext.add_argument("game_dir", help="Path to X4 install or extension directory")
    p_ext.add_argument("-o", "--output", default=None, help="Output directory (required)")
    _add_filter_args(p_ext)
    _add_prefix_arg(p_ext)

    # -- pack --
    p_pack = sub.add_parser("pack", help="Pack loose files into a .cat/.dat catalog")
    p_pack.add_argument("source_dir", help="Directory of loose files to pack")
    p_pack.add_argument("-o", "--output", default=None, help="Output .cat path (required)")
    p_pack.add_argument(
        "--append",
        action="store_true",
        help="Append to existing catalog instead of overwriting",
    )

    # -- diff --
    p_diff = sub.add_parser(
        "diff", help="Generate a diff catalog containing only new/changed files"
    )
    p_diff.add_argument("--base", required=True, help="Base/original directory")
    p_diff.add_argument("--mod", required=True, help="Modified directory")
    p_diff.add_argument("-o", "--output", default=None, help="Output .cat path (required)")

    args = parser.parse_args(argv)
    dispatch: dict[str, _CmdHandler] = {
        "list": _cmd_list,
        "ls": _cmd_list,
        "extract": _cmd_extract,
        "x": _cmd_extract,
        "pack": _cmd_pack,
        "diff": _cmd_diff,
    }
    handler = dispatch.get(args.command)
    if handler is None:
        return 1
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
