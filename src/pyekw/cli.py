"""
Command-line interface for pyekw.
"""

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .utils import KWUtils


def _print_json(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _validate(args: argparse.Namespace, utils: KWUtils) -> int:
    check_court = not args.no_check_court
    # Validate one at a time: validate_multiple_kw_numbers() keys results by the
    # normalized number, which would merge duplicate inputs into a single result
    results = [
        result
        for kw_number in args.kw_numbers
        for result in utils.validate_multiple_kw_numbers(
            [kw_number], check_court=check_court
        ).values()
    ]

    if args.json:
        _print_json(results)
    else:
        for result in results:
            if result["is_valid"]:
                print(f"{result['normalized']}: valid")
                continue
            print(f"{result['normalized']}: invalid ({result['error']})")
            suggestions = utils.suggest_corrections(
                result["normalized"], check_court=check_court
            )
            if suggestions:
                print(f"  did you mean: {', '.join(suggestions)}")

    return 0 if all(result["is_valid"] for result in results) else 1


def _info(args: argparse.Namespace, utils: KWUtils) -> int:
    info = utils.get_kw_info(args.kw_number)

    if info is None:
        _is_valid, error = utils.validator.validate_kw_number(
            utils.normalize_kw_number(args.kw_number)
        )
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.json:
        _print_json(info)
    else:
        print(f"KW number:        {info['kw_number']}")
        print(f"Court code:       {info['court_code']}")
        print(f"Court:            {info['court_name']}")
        print(f"Court full name:  {info['court_full_name']}")
        print(f"Register number:  {info['register_number']}")
        print(f"Check digit:      {info['check_digit']}")

    return 0


def _extract(args: argparse.Namespace, utils: KWUtils) -> int:
    try:
        if args.file == "-":
            text = sys.stdin.read()
        else:
            text = Path(args.file).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"error: cannot read {args.file}: {e}", file=sys.stderr)
        return 2

    # Keep the first occurrence of each KW number, in order
    kw_numbers = list(dict.fromkeys(utils.extract_kw_numbers(text)))
    if args.valid_only:
        kw_numbers = [kw for kw in kw_numbers if utils.validator.is_valid_kw_number(kw)]

    if args.json:
        _print_json(kw_numbers)
    else:
        for kw_number in kw_numbers:
            print(kw_number)

    return 0 if kw_numbers else 1


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the pyekw command."""
    parser = argparse.ArgumentParser(
        prog="pyekw",
        description="Validate, inspect and extract Polish land registry (eKW) numbers.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser(
        "validate",
        help="validate one or more KW numbers",
        description="Validate KW numbers. Exits with 1 if any of them is invalid.",
    )
    validate.add_argument("kw_numbers", nargs="+", metavar="KW_NUMBER")
    validate.add_argument(
        "--no-check-court",
        action="store_true",
        help="do not check the court code against the court registry",
    )
    validate.add_argument("--json", action="store_true", help="print results as JSON")
    validate.set_defaults(handler=_validate)

    info = subparsers.add_parser(
        "info",
        help="show details of a KW number",
        description="Show the court, register number and check digit of a valid KW number.",
    )
    info.add_argument("kw_number", metavar="KW_NUMBER")
    info.add_argument("--json", action="store_true", help="print the result as JSON")
    info.set_defaults(handler=_info)

    extract = subparsers.add_parser(
        "extract",
        help="find KW numbers in a text file",
        description=(
            "Find KW numbers in a UTF-8 text file. Exits with 1 if none are found"
            " and with 2 if the file cannot be read."
        ),
    )
    extract.add_argument(
        "file",
        nargs="?",
        default="-",
        metavar="FILE",
        help="file to read, or '-' for standard input (default)",
    )
    extract.add_argument(
        "--valid-only", action="store_true", help="only print valid KW numbers"
    )
    extract.add_argument("--json", action="store_true", help="print results as JSON")
    extract.set_defaults(handler=_extract)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the pyekw command and return its exit code."""
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args, KWUtils())
    except BrokenPipeError:
        # The reader closed the pipe early (e.g. `pyekw extract file | head -1`).
        # Point stdout at devnull so the flush at interpreter exit does not fail too.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 1
