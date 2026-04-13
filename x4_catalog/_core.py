"""
XRCatTool-equivalent for Linux: read, list, and extract Egosoft X4 .cat/.dat archives.

Format (per community docs and public scripts):
- Each line in a .cat file: ``<filepath> <size> <unix_mtime> <md5hex>``
- Filenames may contain spaces; the last three space-separated fields are fixed.
- The matching .dat file stores file payloads consecutively in .cat line order.
- Later numbered catalogs override earlier ones for the same virtual path.

Usage::

    # List all files in the game install
    x4cat list /path/to/X4\\ Foundations

    # List only MD scripts
    x4cat list /path/to/X4\\ Foundations -g 'md/*.xml'

    # Extract AI scripts to a working directory
    x4cat extract /path/to/X4\\ Foundations -o ./unpacked -g 'aiscripts/*'

    # Extract everything from a DLC extension
    x4cat extract /path/to/X4\\ Foundations/extensions/ego_dlc_boron -o ./boron -p ext_
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CatEntry:
    """One entry from a .cat index line."""

    path: str
    size: int
    mtime: int
    md5: str
    cat_path: Path
    dat_offset: int


def parse_cat_line(line: str) -> CatEntry:
    """Parse a single .cat index line into a CatEntry (without catalog context).

    Raises ``ValueError`` on blank/malformed lines.
    """
    stripped = line.rstrip("\r\n")
    if not stripped.strip():
        raise ValueError("empty line")
    # path may contain spaces; last 3 tokens are always size, mtime, md5
    raw_path, size_s, mtime_s, md5 = stripped.rsplit(" ", 3)
    normalized = raw_path.replace("\\", "/")
    return CatEntry(
        path=normalized,
        size=int(size_s),
        mtime=int(mtime_s),
        md5=md5,
        cat_path=Path(),  # placeholder — caller fills in real value
        dat_offset=0,  # placeholder
    )


def iter_cat_files(directory: Path, prefix: str = "") -> list[Path]:
    """Return .cat files matching ``{prefix}NN.cat`` sorted by numeric id.

    Default prefix "" matches base-game catalogs (01.cat, 02.cat, …).
    Use prefix="ext_" for extension catalogs (ext_01.cat, ext_02.cat, …).
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
            except ValueError:
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


def list_entries(
    directory: Path,
    glob_pattern: str | None = None,
    prefix: str = "",
) -> list[CatEntry]:
    """Return deduplicated entries, optionally filtered by a glob pattern."""
    vfs = build_vfs(directory, prefix=prefix)
    entries = sorted(vfs.values(), key=lambda e: e.path)
    if glob_pattern is None:
        return entries
    return [e for e in entries if fnmatch(e.path, glob_pattern)]


def _read_payload(entry: CatEntry) -> bytes:
    """Read the raw bytes for a single CatEntry from its .dat file."""
    dat_path = entry.cat_path.with_suffix(".dat")
    with open(dat_path, "rb") as f:
        f.seek(entry.dat_offset)
        data = f.read(entry.size)
    if len(data) != entry.size:
        raise OSError(f"Short read for {entry.path}: expected {entry.size}, got {len(data)}")
    return data


def extract_to_disk(
    directory: Path,
    output_dir: Path,
    glob_pattern: str | None = None,
    prefix: str = "",
) -> list[Path]:
    """Extract files to disk, preserving directory structure.

    Returns list of written file paths.
    """
    entries = list_entries(directory, glob_pattern=glob_pattern, prefix=prefix)
    if not entries:
        return []

    written: list[Path] = []
    for entry in entries:
        dest = output_dir / entry.path
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = _read_payload(entry)
        dest.write_bytes(data)
        written.append(dest)
    return written


# --- CLI ---


def _cmd_list(args: argparse.Namespace) -> int:
    entries = list_entries(
        Path(args.game_dir),
        glob_pattern=args.glob,
        prefix=args.prefix,
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
    )
    for p in written:
        print(p)
    print(f"\n{len(written)} file(s) extracted to {output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="x4cat",
        description="List and extract files from X4: Foundations .cat/.dat archives.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- list --
    p_list = sub.add_parser("list", aliases=["ls"], help="List archive contents")
    p_list.add_argument("game_dir", help="Path to X4 install or extension directory")
    p_list.add_argument("-g", "--glob", default=None, help="Filter by glob pattern")
    p_list.add_argument(
        "-p",
        "--prefix",
        default="",
        help="Catalog filename prefix (default: '' for NN.cat, use 'ext_' for extensions)",
    )

    # -- extract --
    p_ext = sub.add_parser("extract", aliases=["x"], help="Extract files to disk")
    p_ext.add_argument("game_dir", help="Path to X4 install or extension directory")
    p_ext.add_argument("-o", "--output", default=None, help="Output directory (required)")
    p_ext.add_argument("-g", "--glob", default=None, help="Filter by glob pattern")
    p_ext.add_argument(
        "-p",
        "--prefix",
        default="",
        help="Catalog filename prefix (default: '' for NN.cat, use 'ext_' for extensions)",
    )

    args = parser.parse_args(argv)
    if args.command in ("list", "ls"):
        return _cmd_list(args)
    if args.command in ("extract", "x"):
        return _cmd_extract(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
