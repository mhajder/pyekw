"""
Command-line interface for pyekw.
"""

import argparse
import json
import os
import sys
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .constants import REGISTER_NUMBER_LENGTH
from .generator import CheckDigitGenerator
from .generator import is_ascii_digits
from .utils import KWUtils

_MAX_REGISTER_NUMBER = 10**REGISTER_NUMBER_LENGTH - 1


def _print_json(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _validate(args: argparse.Namespace, utils: KWUtils) -> int:
    check_court = not args.no_check_court
    auto_pad = args.auto_pad
    # Validate one at a time: validate_multiple_kw_numbers() keys results by the
    # normalized number, which would merge duplicate inputs into a single result
    results = [
        result
        for kw_number in args.kw_numbers
        for result in utils.validate_multiple_kw_numbers(
            [kw_number], check_court=check_court, auto_pad=auto_pad
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
    info = utils.get_kw_info(args.kw_number, auto_pad=args.auto_pad)

    if info is None:
        _is_valid, error = utils.validator.validate_kw_number(
            utils.normalize_kw_number(args.kw_number, auto_pad=args.auto_pad),
            auto_pad=args.auto_pad,
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
        if info.get("circuit"):
            print(f"Circuit:          {info['circuit']}")
        if info.get("voivodeship"):
            print(f"Voivodeship:      {info['voivodeship']}")
        print(f"Register number:  {info['register_number']}")
        print(f"Check digit:      {info['check_digit']}")
        print(f"Compact:          {info['compact']}")

    return 0


def _read_text(file: str) -> str:
    if file == "-":
        return sys.stdin.read()
    return Path(file).read_text(encoding="utf-8")


def _found_per_file(
    args: argparse.Namespace, utils: KWUtils, read_errors: list[str]
) -> Iterator[tuple[str, list[str]]]:
    """Yield (file, KW numbers found) one file at a time, so texts are not all kept
    in memory. Unreadable files are reported and recorded in read_errors, and the
    remaining files are still processed."""
    for file in args.files:
        try:
            text = _read_text(file)
        except (OSError, UnicodeDecodeError) as e:
            print(f"error: cannot read {file}: {e}", file=sys.stderr)
            read_errors.append(file)
            continue
        yield file, utils.extract_kw_numbers(text, include_compact=args.include_compact)


def _extract(args: argparse.Namespace, utils: KWUtils) -> int:
    read_errors: list[str] = []
    found_per_file = _found_per_file(args, utils, read_errors)

    if args.check:
        status = _check(found_per_file, args, utils)
        return 2 if read_errors else status

    # Keep the first occurrence of each KW number, in order
    kw_numbers = list(
        dict.fromkeys(kw for _file, found in found_per_file for kw in found)
    )
    if args.valid_only:
        kw_numbers = [kw for kw in kw_numbers if utils.validator.is_valid_kw_number(kw)]

    if args.json:
        _print_json(kw_numbers)
    else:
        for kw_number in kw_numbers:
            print(kw_number)

    if read_errors:
        return 2
    return 0 if kw_numbers else 1


def _check(
    found_per_file: Iterable[tuple[str, list[str]]],
    args: argparse.Namespace,
    utils: KWUtils,
) -> int:
    """Report invalid KW numbers per file. Exits with 1 only if any is invalid."""
    invalid = []
    for file, found in found_per_file:
        for kw_number in dict.fromkeys(found):
            is_valid, error = utils.validator.validate_kw_number(kw_number)
            if not is_valid:
                invalid.append({"file": file, "kw_number": kw_number, "error": error})

    if args.json:
        _print_json(invalid)
    else:
        for item in invalid:
            print(f"{item['file']}: {item['kw_number']}: invalid ({item['error']})")

    return 1 if invalid else 0


def _generate(args: argparse.Namespace, utils: KWUtils) -> int:
    court = args.court_code.strip().upper()
    if not args.no_check_court and not utils.court_registry.is_valid_court(court):
        print(f"error: unknown court code: {args.court_code}", file=sys.stderr)
        return 1

    num_str = args.number.strip()
    if not is_ascii_digits(num_str):
        print(
            f"error: register number must contain only digits: {args.number}",
            file=sys.stderr,
        )
        return 1

    if args.count < 1:
        print("error: --count must be at least 1", file=sys.stderr)
        return 1

    if len(num_str) > REGISTER_NUMBER_LENGTH:
        print(
            f"error: register number cannot exceed {REGISTER_NUMBER_LENGTH} digits,"
            f" got {len(num_str)}",
            file=sys.stderr,
        )
        return 1

    if args.no_pad and len(num_str) != REGISTER_NUMBER_LENGTH:
        print(
            f"error: register number must be exactly {REGISTER_NUMBER_LENGTH} digits"
            f" when --no-pad is set, got {len(num_str)}",
            file=sys.stderr,
        )
        return 1

    base_num = int(num_str)
    if base_num + args.count - 1 > _MAX_REGISTER_NUMBER:
        print(
            f"error: register numbers would exceed {_MAX_REGISTER_NUMBER}",
            file=sys.stderr,
        )
        return 1

    try:
        # Fail before printing anything if the court code cannot be used
        CheckDigitGenerator.calculate_check_digit(
            court, f"{base_num:0{REGISTER_NUMBER_LENGTH}d}"
        )
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    kw_numbers = (
        CheckDigitGenerator.generate_full_kw_number(
            court, f"{base_num + i:0{REGISTER_NUMBER_LENGTH}d}"
        )
        for i in range(args.count)
    )
    if args.compact:
        kw_numbers = (kw.replace("/", "") for kw in kw_numbers)

    if args.json:
        _print_json(list(kw_numbers))
    else:
        for kw_number in kw_numbers:
            print(kw_number)

    return 0


def _courts(args: argparse.Namespace, utils: KWUtils) -> int:
    registry = utils.court_registry
    # Each filter narrows the set of matching codes, using the registry lookups
    selections = []
    if args.query:
        selections.append(registry.search_courts(args.query.strip()))
    if args.voivodeship:
        selections.append(registry.get_courts_by_voivodeship(args.voivodeship))
    if args.circuit:
        selections.append(registry.get_courts_by_circuit(args.circuit))
    selected_codes = [{code for code, _name in selection} for selection in selections]

    matched = [
        {
            "court_code": code,
            "name": data["name"],
            "full_name": data["full_name"],
            "circuit": data["circuit"],
            "voivodeship": data["voivodeship"],
        }
        for code, data in registry.get_all_courts_detailed().items()
        if all(code in codes for codes in selected_codes)
    ]

    if args.json:
        _print_json(matched)
    elif matched:
        for court in matched:
            print(f"{court['court_code']}: {court['name']} ({court['voivodeship']})")
    else:
        print("No matching courts found.", file=sys.stderr)

    return 0 if matched else 1


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
    validate.add_argument(
        "--auto-pad",
        action="store_true",
        help="automatically pad register numbers shorter than 8 digits with leading zeros",
    )
    validate.add_argument("--json", action="store_true", help="print results as JSON")
    validate.set_defaults(handler=_validate)

    info = subparsers.add_parser(
        "info",
        help="show details of a KW number",
        description="Show the court, register number and check digit of a valid KW number.",
    )
    info.add_argument("kw_number", metavar="KW_NUMBER")
    info.add_argument(
        "--auto-pad",
        action="store_true",
        help="automatically pad register numbers shorter than 8 digits with leading zeros",
    )
    info.add_argument("--json", action="store_true", help="print the result as JSON")
    info.set_defaults(handler=_info)

    extract = subparsers.add_parser(
        "extract",
        help="find KW numbers in a text file",
        description=(
            "Find KW numbers in UTF-8 text files. Exits with 1 if none are found"
            " (or, with --check, if any is invalid) and with 2 if a file cannot be read."
        ),
    )
    extract.add_argument(
        "files",
        nargs="*",
        default=["-"],
        metavar="FILE",
        help="files to read, or '-' for standard input (default)",
    )
    extract_mode = extract.add_mutually_exclusive_group()
    extract_mode.add_argument(
        "--valid-only", action="store_true", help="only print valid KW numbers"
    )
    extract_mode.add_argument(
        "--check",
        action="store_true",
        help=(
            "only print invalid KW numbers with their file, and exit with 1 if any"
            " is found (for linting, e.g. as a pre-commit hook)"
        ),
    )
    extract.add_argument(
        "--include-compact",
        action="store_true",
        help="also search for 13-character compact KW numbers without separators",
    )
    extract.add_argument("--json", action="store_true", help="print results as JSON")
    extract.set_defaults(handler=_extract)

    generate = subparsers.add_parser(
        "generate",
        help="generate valid KW numbers with check digits",
        description="Generate complete KW numbers with calculated check digits.",
    )
    generate.add_argument(
        "court_code", metavar="COURT_CODE", help="4-character court code"
    )
    generate.add_argument(
        "number", metavar="NUMBER", help="register number or base number"
    )
    generate.add_argument(
        "--count",
        type=int,
        default=1,
        help="number of consecutive KW numbers to generate (default: 1)",
    )
    generate.add_argument(
        "--no-pad",
        action="store_true",
        help="do not auto-pad register number (must already be 8 digits)",
    )
    generate.add_argument(
        "--compact",
        action="store_true",
        help="output compact format without slashes (e.g. WA4M000123459)",
    )
    generate.add_argument(
        "--no-check-court",
        action="store_true",
        help="do not verify that the court code exists in the registry",
    )
    generate.add_argument("--json", action="store_true", help="print results as JSON")
    generate.set_defaults(handler=_generate)

    courts = subparsers.add_parser(
        "courts",
        help="search or list land registry courts",
        description="Search or filter Polish courts handling land registry matters.",
    )
    courts.add_argument(
        "query",
        nargs="?",
        default=None,
        metavar="QUERY",
        help="optional search term for court code, name, or city",
    )
    courts.add_argument(
        "--voivodeship",
        metavar="VOIVODESHIP",
        help="filter by voivodeship (e.g. 'mazowieckie' or 'województwo mazowieckie')",
    )
    courts.add_argument(
        "--circuit",
        metavar="CIRCUIT",
        help="filter by regional court circuit name (substring, e.g. 'Warszawie')",
    )
    courts.add_argument("--json", action="store_true", help="print results as JSON")
    courts.set_defaults(handler=_courts)

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
