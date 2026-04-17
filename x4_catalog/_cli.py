"""CLI command handlers and argument parsing for x4cat."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from x4_catalog._core import (
    _pack_changed,
    diff_file_sets,
    extract_to_disk,
    list_entries,
    pack_catalog,
)

type _CmdHandler = Callable[[argparse.Namespace], int]

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


def _list_from_index(db_path: Path, args: argparse.Namespace) -> int:
    """List files from the SQLite index game_files table."""
    import re as _re
    import sqlite3
    from fnmatch import fnmatch

    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT virtual_path, size FROM game_files ORDER BY virtual_path"
    ).fetchall()
    conn.close()

    glob_pattern = getattr(args, "glob", None)
    include_re = getattr(args, "include", None)
    exclude_re = getattr(args, "exclude", None)

    filtered: list[tuple[str, int]] = []
    inc_compiled = _re.compile(include_re) if include_re else None
    exc_compiled = _re.compile(exclude_re) if exclude_re else None

    for vpath, size in rows:
        if glob_pattern and not fnmatch(vpath, glob_pattern):
            continue
        if inc_compiled and not inc_compiled.search(vpath):
            continue
        if exc_compiled and exc_compiled.search(vpath):
            continue
        filtered.append((vpath, size))

    for vpath, size in filtered:
        print(f"{size:>12}  {vpath}")
    print(f"\n{len(filtered)} file(s)")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    game_dir = getattr(args, "game_dir", None)

    if game_dir:
        try:
            entries = list_entries(
                Path(game_dir),
                glob_pattern=args.glob,
                prefix=args.prefix,
                include_re=args.include,
                exclude_re=args.exclude,
            )
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        for e in entries:
            print(f"{e.size:>12}  {e.path}")
        print(f"\n{len(entries)} file(s)")
        return 0

    # Index mode
    db_path = _resolve_index_db(args)
    if db_path is None:
        print(
            "error: provide <game_dir> or --db for index-backed listing",
            file=sys.stderr,
        )
        return 1
    return _list_from_index(db_path, args)


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


def _cmd_validate_diff(args: argparse.Namespace) -> int:
    from x4_catalog._validate import validate_diff_directory

    game_dir, mod_dir = Path(args.game_dir), Path(args.mod_dir)
    reports = validate_diff_directory(game_dir, mod_dir, prefix=args.prefix)

    total_ops = 0
    passed = 0
    failed = 0
    warnings = 0
    skipped_files = 0

    for report in reports:
        if not report.base_found:
            skipped_files += 1
            print(f"{report.virtual_path}: SKIP (no base file found in game VFS)")
            continue
        if report.parse_error:
            failed += 1
            print(f"{report.virtual_path}: ERROR {report.parse_error}")
            continue
        for r in report.results:
            total_ops += 1
            if "unsupported" in r.sel_detail.lower():
                warnings += 1
                status = "WARN"
            elif r.sel_matched:
                passed += 1
                status = "PASS"
            else:
                failed += 1
                status = "FAIL"
            print(
                f'{report.virtual_path}:{r.op.line}: {status}  sel="{r.op.sel}"  ({r.sel_detail})'
            )
            if r.if_matched is not None:
                if "unsupported" in r.if_detail.lower():
                    if_status = "WARN"
                    warnings += 1
                elif r.if_matched:
                    if_status = "PASS"
                else:
                    # Unmet if condition means the op is conditionally skipped, not broken
                    if_status = "INFO"
                print(
                    f"{report.virtual_path}:{r.op.line}: {if_status}"
                    f'  if="{r.op.if_cond}"  ({r.if_detail})'
                )

    if reports:
        print(
            f"\n{len(reports)} file(s), {total_ops} operation(s): "
            f"{passed} passed, {failed} failed, {warnings} warning(s), "
            f"{skipped_files} skipped"
        )

    if failed > 0 or (args.strict and warnings > 0):
        return 1
    return 0


def _resolve_index_db(args: argparse.Namespace, *, required: bool = True) -> Path | None:
    """Resolve the index DB path from global --db or auto-detect."""
    from x4_catalog._index import find_index_db

    # Global --db flag
    db = getattr(args, "db", None)
    if db:
        db_path = Path(db)
        if not db_path.exists():
            if required:
                print(f"error: index not found: {db_path}", file=sys.stderr)
            return None
        return db_path

    # Auto-detect from cache
    found = find_index_db()
    if found is not None:
        return found

    if required:
        print(
            "error: no index found. Run 'x4cat index <game_dir>' first, or pass --db",
            file=sys.stderr,
        )
    return None


def _cmd_search(args: argparse.Namespace) -> int:
    from x4_catalog._search import format_search_output, search_assets

    db_path = _resolve_index_db(args)
    if db_path is None:
        return 1

    type_filter = getattr(args, "type", None)
    results = search_assets(args.term, db_path, type_filter=type_filter)
    print(format_search_output(results))
    return 0


def _cmd_validate_schema(args: argparse.Namespace) -> int:
    from x4_catalog._schema_validate import validate_schema

    db_path = _resolve_index_db(args)
    if db_path is None:
        return 1

    mod_dir = Path(args.mod_dir)
    result = validate_schema(mod_dir, db_path)

    for err in result["errors"]:
        print(f"  ERROR: {err}")
    for warn in result["warnings"]:
        print(f"  WARN:  {warn}")

    total = len(result["errors"]) + len(result["warnings"])
    if total:
        print(f"\n{len(result['errors'])} error(s), {len(result['warnings'])} warning(s)")
    else:
        print("Schema validation passed")

    return 1 if result["errors"] else 0


def _cmd_check_conflicts(args: argparse.Namespace) -> int:
    from x4_catalog._conflicts import check_conflicts

    mod_dirs = [Path(d) for d in args.mod_dirs]
    result = check_conflicts(mod_dirs)

    for c in result["conflicts"]:
        mods = ", ".join(c["mods"])
        print(f'  CONFLICT  {c["file"]}  sel="{c["sel"]}"  mods: {mods}')

    for i in result["info"]:
        mods = ", ".join(i["mods"])
        print(f'  INFO      {i["file"]}  sel="{i["sel"]}"  mods: {mods}')

    if args.verbose:
        for s in result["safe"]:
            mods = ", ".join(s["mods"])
            print(f'  SAFE      {s["file"]}  sel="{s["sel"]}"  mods: {mods}')

    print(
        f"\n{result['files_checked']} shared file(s): "
        f"{len(result['conflicts'])} conflict(s), "
        f"{len(result['safe'])} safe, "
        f"{len(result['info'])} info"
    )

    return 1 if result["conflicts"] else 0


def _cmd_validate_translations(args: argparse.Namespace) -> int:
    from x4_catalog._translations import validate_translations

    mod_dir = Path(args.mod_dir)
    db_path = _resolve_index_db(args, required=False)  # optional — for collision detection
    result = validate_translations(mod_dir, db_path=db_path)

    for err in result["errors"]:
        print(f"  {err}")
    for warn in result["warnings"]:
        print(f"  {warn}")

    total = len(result["errors"]) + len(result["warnings"])
    if total:
        print(f"\n{len(result['errors'])} error(s), {len(result['warnings'])} warning(s)")
    else:
        print("All translations valid")

    return 1 if result["errors"] else 0


def _cmd_scaffold(args: argparse.Namespace) -> int:
    scaffold_type = args.scaffold_type
    if scaffold_type is None:
        print(
            "error: specify 'ware', 'equipment', 'ship', or 'translation'",
            file=sys.stderr,
        )
        return 1

    if scaffold_type == "translation":
        from x4_catalog._translations import scaffold_translation

        output_path = Path(args.output) if args.output else None
        if output_path is None:
            print("error: -o / --output is required", file=sys.stderr)
            return 1
        scaffold_translation(Path(args.source), output_path, lang_code=args.lang)
        print(f"  {output_path}")
        return 0

    output_dir = Path(args.output) if args.output else Path.cwd() / "src"

    if scaffold_type == "ware":
        from x4_catalog._scaffold import scaffold_ware

        files = scaffold_ware(
            args.id,
            args.name,
            output_dir,
            description=args.description or "",
            group=args.group or "",
            volume=args.volume,
            price_min=args.price_min,
            price_avg=args.price_avg,
            price_max=args.price_max,
        )
        for f in files:
            print(f"  {output_dir / f}")
        return 0

    if scaffold_type == "equipment":
        from x4_catalog._scaffold import scaffold_equipment

        if not args.clone_from:
            print(
                "error: --clone-from is required for equipment scaffolding",
                file=sys.stderr,
            )
            return 1

        db_path = _resolve_index_db(args)
        if db_path is None:
            return 1

        try:
            files = scaffold_equipment(
                args.id,
                args.name,
                output_dir,
                clone_from=args.clone_from,
                db_path=db_path,
                description=args.description or "",
                price_min=args.price_min,
                price_avg=args.price_avg,
                price_max=args.price_max,
            )
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        for f in files:
            print(f"  {output_dir / f}")
        return 0

    if scaffold_type == "ship":
        from x4_catalog._scaffold import scaffold_ship

        if not args.clone_from:
            print(
                "error: --clone-from is required for ship scaffolding",
                file=sys.stderr,
            )
            return 1

        db_path = _resolve_index_db(args)
        if db_path is None:
            return 1

        try:
            files = scaffold_ship(
                args.id,
                args.name,
                output_dir,
                clone_from=args.clone_from,
                db_path=db_path,
                size=args.size,
                description=args.description or "",
                price_min=args.price_min,
                price_avg=args.price_avg,
                price_max=args.price_max,
            )
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        for f in files:
            print(f"  {output_dir / f}")
        return 0

    print(f"error: unknown scaffold type: {scaffold_type}", file=sys.stderr)
    return 1


def _cmd_extract_macro(args: argparse.Namespace) -> int:
    from x4_catalog._extract_macro import extract_macro

    db_path = _resolve_index_db(args)
    if db_path is None:
        return 1

    # Resolve game_dir: explicit flag, or from index meta
    game_dir_str = getattr(args, "game_dir", None)
    if not game_dir_str:
        import sqlite3

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT value FROM meta WHERE key = 'game_dir'").fetchone()
        conn.close()
        if row is None:
            print("error: cannot determine game directory from index", file=sys.stderr)
            return 1
        game_dir_str = row[0]

    game_dir = Path(game_dir_str)
    output_dir = Path(args.output) if args.output else Path.cwd()

    result = extract_macro(args.macro_id, db_path, game_dir, output_dir)
    if result is None:
        print(f"Macro not found: {args.macro_id}", file=sys.stderr)
        return 1

    print(f"Extracted: {result}")
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    from x4_catalog._inspect import format_inspect_output, inspect_asset

    db_path = _resolve_index_db(args)
    if db_path is None:
        return 1

    result = inspect_asset(args.asset_id, db_path)
    if result is None:
        print(f"Not found: {args.asset_id}", file=sys.stderr)
        return 1

    print(format_inspect_output(result))
    return 0


def _cmd_index(args: argparse.Namespace) -> int:
    from x4_catalog._index import build_index, db_path_for_game_dir, is_index_stale

    game_dir = Path(args.game_dir)
    db_path = Path(args.output) if args.output else db_path_for_game_dir(game_dir)

    if db_path.exists() and not args.refresh and not is_index_stale(game_dir, db_path):
        print(f"Index is up to date: {db_path}")
        return 0

    import sqlite3

    build_index(game_dir, db_path)

    conn = sqlite3.connect(db_path)
    try:
        tables = [
            "macros",
            "components",
            "wares",
            "game_files",
            "schema_groups",
            "script_properties",
        ]
        counts: dict[str, int] = {}
        for table in tables:
            try:
                row = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()  # noqa: S608
                counts[table] = int(row[0]) if row else 0
            except sqlite3.OperationalError:
                counts[table] = 0
    finally:
        conn.close()

    macro_count = counts["macros"]
    comp_count = counts["components"]
    ware_count = counts["wares"]
    file_count = counts["game_files"]
    schema_count = counts["schema_groups"]
    sp_count = counts["script_properties"]

    print(
        f"Indexed {macro_count} macros, {comp_count} components, "
        f"{ware_count} wares, {file_count} files"
    )
    if schema_count:
        print(f"  + {schema_count} schema rules, {sp_count} script properties")
    print(f"  → {db_path}")
    return 0


def _cmd_init(args: argparse.Namespace) -> int:
    from x4_catalog._init import scaffold_project

    output_dir = Path(args.output) if args.output else None
    try:
        out = scaffold_project(
            args.mod_id,
            output_dir=output_dir,
            author=args.author,
            description=args.description,
            game_version=args.game_version,
            repo=args.repo,
            init_git=args.git,
        )
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Created project: {out}")
    return 0


def _cmd_xmldiff(args: argparse.Namespace) -> int:
    from x4_catalog._xmldiff import generate_diff

    base_path, mod_path = Path(args.base), Path(args.mod)
    if not base_path.is_file():
        print(f"error: base file not found: {base_path}", file=sys.stderr)
        return 1
    if not mod_path.is_file():
        print(f"error: mod file not found: {mod_path}", file=sys.stderr)
        return 1
    base_data = base_path.read_bytes()
    mod_data = mod_path.read_bytes()
    try:
        result = generate_diff(base_data, mod_data)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(result)
        print(f"Diff patch written to {out}")
    else:
        sys.stdout.buffer.write(result)
        sys.stdout.buffer.write(b"\n")
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
    parser.add_argument(
        "--db", default=None, help="Path to index DB (supports multiple game versions)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- list --
    p_list = sub.add_parser("list", aliases=["ls"], help="List archive contents")
    p_list.add_argument(
        "game_dir", nargs="?", default=None, help="Path to X4 install (optional if --db provided)"
    )
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

    # -- xmldiff --
    p_xmldiff = sub.add_parser("xmldiff", help="Generate an XML diff patch from two XML files")
    p_xmldiff.add_argument("--base", required=True, help="Base/original XML file")
    p_xmldiff.add_argument("--mod", required=True, help="Modified XML file")
    p_xmldiff.add_argument("-o", "--output", default=None, help="Output diff patch file")

    # -- validate-diff --
    p_vdiff = sub.add_parser(
        "validate-diff", help="Validate XML diff patches against base game files"
    )
    p_vdiff.add_argument("game_dir", help="Path to X4 install or extension directory")
    p_vdiff.add_argument("mod_dir", help="Directory containing diff patch XML files")
    _add_prefix_arg(p_vdiff)
    p_vdiff.add_argument(
        "--strict",
        action="store_true",
        help="Treat unsupported XPath warnings as errors",
    )

    # -- scaffold --
    p_scaffold = sub.add_parser("scaffold", help="Scaffold new mod content")
    scaffold_sub = p_scaffold.add_subparsers(dest="scaffold_type")

    # scaffold ware
    p_sw = scaffold_sub.add_parser("ware", help="Scaffold a trade ware (Tier 1)")
    p_sw.add_argument("--id", required=True, help="Ware ID")
    p_sw.add_argument("--name", required=True, help="Ware display name")
    p_sw.add_argument("--description", default=None, help="Ware description")
    p_sw.add_argument("--group", default=None, help="Ware group (e.g. hightech, energy)")
    p_sw.add_argument("--volume", type=int, default=1, help="Volume (default: 1)")
    p_sw.add_argument("--price-min", type=int, default=0, help="Min price")
    p_sw.add_argument("--price-avg", type=int, default=0, help="Average price")
    p_sw.add_argument("--price-max", type=int, default=0, help="Max price")
    p_sw.add_argument("-o", "--output", default=None, help="Output directory")

    # scaffold equipment
    p_se = scaffold_sub.add_parser(
        "equipment", help="Scaffold equipment by cloning existing (Tier 2)"
    )
    p_se.add_argument("--id", required=True, help="New macro ID")
    p_se.add_argument("--name", required=True, help="Equipment display name")
    p_se.add_argument("--clone-from", required=True, help="Macro ID to clone")
    p_se.add_argument("--description", default=None, help="Description")
    p_se.add_argument("--price-min", type=int, default=0, help="Min price")
    p_se.add_argument("--price-avg", type=int, default=0, help="Average price")
    p_se.add_argument("--price-max", type=int, default=0, help="Max price")
    p_se.add_argument("-o", "--output", default=None, help="Output directory")

    # scaffold ship
    p_ss = scaffold_sub.add_parser(
        "ship",
        help="Scaffold a NEW ship (for stat mods, use extract-macro + xmldiff instead)",
    )
    p_ss.add_argument("--id", required=True, help="New macro ID")
    p_ss.add_argument("--name", required=True, help="Ship display name")
    p_ss.add_argument("--clone-from", required=True, help="Ship macro ID to clone")
    p_ss.add_argument("--size", default="s", choices=["s", "m", "l", "xl"], help="Ship size class")
    p_ss.add_argument("--description", default=None, help="Description")
    p_ss.add_argument("--price-min", type=int, default=0, help="Min price")
    p_ss.add_argument("--price-avg", type=int, default=0, help="Average price")
    p_ss.add_argument("--price-max", type=int, default=0, help="Max price")
    p_ss.add_argument("-o", "--output", default=None, help="Output directory")

    # scaffold translation
    p_st = scaffold_sub.add_parser(
        "translation", help="Generate a translation stub from an existing file"
    )
    p_st.add_argument("--from", dest="source", required=True, help="Source translation file")
    p_st.add_argument(
        "--lang", type=int, required=True, help="Target language code (e.g. 49=German)"
    )
    p_st.add_argument("-o", "--output", default=None, help="Output file path")

    # -- validate-schema --
    p_vschema = sub.add_parser(
        "validate-schema",
        help="Validate mod scripts against indexed schema rules",
    )
    p_vschema.add_argument("mod_dir", help="Mod directory containing MD/AI scripts")

    # -- check-conflicts --
    p_conflicts = sub.add_parser(
        "check-conflicts",
        help="Detect conflicts between multiple mods' diff patches",
    )
    p_conflicts.add_argument("mod_dirs", nargs="+", help="Two or more mod directories to compare")
    p_conflicts.add_argument(
        "--verbose",
        action="store_true",
        help="Show safe overlaps in addition to conflicts",
    )

    # -- validate-translations --
    p_vtrans = sub.add_parser(
        "validate-translations",
        help="Validate translation files against text references in mod XML",
    )
    p_vtrans.add_argument("mod_dir", help="Mod directory to validate")

    # -- extract-macro --
    p_emacro = sub.add_parser("extract-macro", help="Extract a macro file by ID")
    p_emacro.add_argument("macro_id", help="Macro name (e.g. ship_arg_s_fighter_01_a_macro)")
    p_emacro.add_argument(
        "-o", "--output", default=None, help="Output directory (default: current dir)"
    )

    # -- search --
    p_search = sub.add_parser("search", help="Search game assets by ID, group, or tags")
    p_search.add_argument("term", help="Search term (partial match)")
    p_search.add_argument(
        "--type",
        default=None,
        choices=["ware", "macro", "component", "datatype", "keyword"],
        help="Filter results by type",
    )

    # -- inspect --
    p_inspect = sub.add_parser(
        "inspect", help="Inspect a game asset by ware, macro, or component ID"
    )
    p_inspect.add_argument("asset_id", help="Ware ID, macro name, or component name")

    # -- index --
    p_index = sub.add_parser("index", help="Build a SQLite index of game data")
    p_index.add_argument("game_dir", help="Path to X4 install directory")
    p_index.add_argument(
        "-o", "--output", default=None, help="Output DB path (default: ~/.cache/x4cat/)"
    )
    p_index.add_argument(
        "--refresh", action="store_true", help="Force rebuild even if index is up to date"
    )

    # -- init --
    p_init = sub.add_parser("init", help="Scaffold a new X4 mod project")
    p_init.add_argument("mod_id", help="Mod identifier (e.g. my_awesome_mod)")
    p_init.add_argument(
        "-o", "--output", default=None, help="Output directory (default: ./<mod_id>)"
    )
    p_init.add_argument(
        "--author", default=None, help="Author name (default: git config user.name)"
    )
    p_init.add_argument("--description", default=None, help="Mod description")
    p_init.add_argument(
        "--game-version", type=int, default=900, help="Minimum game version (default: 900)"
    )
    p_init.add_argument(
        "--repo", default=None, help="Repository URL or GitHub shorthand (user/repo)"
    )
    p_init.add_argument("--git", action="store_true", help="Initialize a git repository")

    args = parser.parse_args(argv)
    dispatch: dict[str, _CmdHandler] = {
        "list": _cmd_list,
        "ls": _cmd_list,
        "extract": _cmd_extract,
        "x": _cmd_extract,
        "pack": _cmd_pack,
        "diff": _cmd_diff,
        "xmldiff": _cmd_xmldiff,
        "validate-diff": _cmd_validate_diff,
        "inspect": _cmd_inspect,
        "search": _cmd_search,
        "extract-macro": _cmd_extract_macro,
        "scaffold": _cmd_scaffold,
        "validate-translations": _cmd_validate_translations,
        "validate-schema": _cmd_validate_schema,
        "check-conflicts": _cmd_check_conflicts,
        "index": _cmd_index,
        "init": _cmd_init,
    }
    handler = dispatch.get(args.command)
    if handler is None:
        return 1
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
