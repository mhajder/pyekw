<div align="center">

# pyekw

**Validate, generate and analyze Polish land registry (eKW) numbers in Python**

[![PyPI](https://img.shields.io/pypi/v/pyekw?logo=pypi&logoColor=white)](https://pypi.org/project/pyekw/)
[![Python](https://img.shields.io/pypi/pyversions/pyekw?logo=python&logoColor=white)](https://pypi.org/project/pyekw/)
[![License](https://img.shields.io/github/license/mhajder/pyekw)](https://github.com/mhajder/pyekw/blob/main/LICENSE)

[![Pre-commit Checks](https://github.com/mhajder/pyekw/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/mhajder/pyekw/actions/workflows/pre-commit.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

[Installation](https://github.com/mhajder/pyekw#-installation) · [Quick Start](https://github.com/mhajder/pyekw#-quick-start) · [Command Line](https://github.com/mhajder/pyekw#-command-line) · [API Reference](https://github.com/mhajder/pyekw#-api-reference) · [Development](https://github.com/mhajder/pyekw#-development)

</div>

pyekw is a dependency-free Python library for working with Polish eKW (Elektroniczne Księgi Wieczyste) land registry numbers. It validates KW numbers against the official check digit algorithm and court code list, generates correct check digits, extracts KW numbers from free text and suggests corrections for mistyped ones.

A KW number has three parts:

```text
WA4M / 00123456 / 4
│      │          └── check digit (0-9)
│      └───────────── 8-digit register number
└──────────────────── 4-character court code
```

## ✨ Features

- **KW number validation**: check format, court code and check digit, with a readable error message
- **Check digit generation**: calculate check digits and build complete KW numbers
- **Court registry**: built-in database of 350+ Polish courts handling land registry matters
- **Text utilities**: normalize, extract, batch-validate and get detailed info about KW numbers
- **Error correction**: suggest valid KW numbers for an invalid input
- **Command-line tool**: validate, inspect and extract KW numbers without writing Python
- **Zero dependencies**: pure Python, fully typed, nothing else to install

## 🚀 Installation

### Prerequisites

- Python 3.10 to 3.15

### Install from PyPI

```sh
# Using UV (recommended)
uv add pyekw

# Or using pip
pip install pyekw
```

### Install from Source

```sh
uv add "git+https://github.com/mhajder/pyekw.git"
```

## ⚡ Quick Start

```pycon
>>> from pyekw import CheckDigitGenerator, CourtRegistry, KWUtils, KWValidator

>>> # Validate a KW number
>>> validator = KWValidator()
>>> validator.validate_kw_number("WA4M/00123456/4")
(True, None)
>>> validator.validate_kw_number("WA4M/00123456/5")
(False, 'Invalid check digit: expected 4, got 5')

>>> # Generate a check digit or a complete KW number
>>> CheckDigitGenerator.calculate_check_digit("WA4M", "00123456")
4
>>> CheckDigitGenerator.generate_full_kw_number("KR1P", "00012345")
'KR1P/00012345/2'

>>> # Look up courts
>>> registry = CourtRegistry()
>>> registry.get_court_name("WA4M")
'WARSZAWA (X)'
>>> registry.search_courts("Kraków")
[('KR1P', 'KRAKÓW')]

>>> # Work with KW numbers in text
>>> utils = KWUtils()
>>> utils.normalize_kw_number(" wa4m / 00123456 / 4 ")
'WA4M/00123456/4'
>>> utils.extract_kw_numbers("Nieruchomość WA4M/00123456/4 oraz KR1P/00012345/2.")
['WA4M/00123456/4', 'KR1P/00012345/2']
>>> utils.suggest_corrections("WA4M/00123456/5")
['WA4M/00123456/4']

```

More examples are in [`examples/example_all_functions.py`](https://github.com/mhajder/pyekw/blob/main/examples/example_all_functions.py):

```sh
uv run python examples/example_all_functions.py
```

## 💻 Command Line

Run it without installing using `uvx`, or as `pyekw` after `pip install pyekw`:

```sh
# Validate one or more KW numbers (exit code 1 if any is invalid)
uvx pyekw validate WA4M/00123456/4 WA4M/00123456/5
# WA4M/00123456/4: valid
# WA4M/00123456/5: invalid (Invalid check digit: expected 4, got 5)
#   did you mean: WA4M/00123456/4

# Show court and register details
uvx pyekw info WA4M/00123456/4

# Find KW numbers in a text file, or in standard input
uvx pyekw extract contract.txt
pdftotext contract.pdf - | uvx pyekw extract --valid-only
```

Every command supports `--json` for machine-readable output. Run `uvx pyekw --help` for all options.

## 📚 API Reference

### `KWValidator`

Validates Polish KW numbers.

| Method | Returns | Description |
|--------|---------|-------------|
| `validate_kw_number(kw_number, check_court=True)` | `tuple[bool, str \| None]` | Validate a complete KW number, returns `(is_valid, error_message)` |
| `is_valid_kw_number(kw_number, check_court=True)` | `bool` | Same as above, but returns only the result |
| `parse_kw_number(kw_number)` | `tuple[str, str, str]` | Split a KW number into court code, register number and check digit |
| `validate_court_code(court_code)` | `bool` | Check if the court code exists |
| `validate_check_digit(court_code, register_number, check_digit)` | `bool` | Check if the check digit is correct |

### `CheckDigitGenerator`

Generates check digits and complete KW numbers. All methods are static.

| Method | Returns | Description |
|--------|---------|-------------|
| `calculate_check_digit(court_code, register_number)` | `int` | Calculate the check digit |
| `generate_full_kw_number(court_code, register_number)` | `str` | Build a complete KW number with the correct check digit |

### `CourtRegistry`

Built-in database of Polish land registry courts.

| Method | Returns | Description |
|--------|---------|-------------|
| `is_valid_court(court_code)` | `bool` | Check if a court code exists |
| `get_court_name(court_code)` | `str \| None` | Short court name |
| `get_court_full_name(court_code)` | `str \| None` | Full court name with its territorial jurisdiction |
| `search_courts(query)` | `list[tuple[str, str]]` | Search courts by name or code |
| `get_all_courts()` | `dict[str, str]` | All court codes with short names |
| `get_all_courts_detailed()` | `dict[str, dict[str, str]]` | All court codes with short and full names |

### `KWUtils`

Helpers for working with KW numbers in real-world data.

| Method | Returns | Description |
|--------|---------|-------------|
| `normalize_kw_number(kw_number)` | `str` | Normalize spacing and letter case |
| `extract_kw_numbers(text)` | `list[str]` | Find all KW numbers in a text |
| `get_kw_info(kw_number)` | `KWInfo \| None` | Court, register number, check digit and validity in one dict |
| `validate_multiple_kw_numbers(kw_numbers, check_court=True)` | `dict[str, KWValidationResult]` | Validate many KW numbers at once |
| `generate_kw_number_variants(court_code, base_number, count=10)` | `list[str]` | Generate a series of consecutive valid KW numbers |
| `suggest_corrections(kw_number, check_court=True)` | `list[str]` | Suggest valid KW numbers for an invalid input |

### Result types

`KWInfo` and `KWValidationResult` are `TypedDict`s exported from `pyekw`, so type checkers and editors know every key of the returned dicts. In `KWValidationResult`, the court and register keys are only present when the KW number is valid.

The installed version is available as `pyekw.__version__`.

## 🔨 Development

```sh
# Clone and install with development dependencies
git clone https://github.com/mhajder/pyekw.git
cd pyekw
uv sync --group dev

# Run tests, README examples and the 100% coverage check
uv run pytest

# Run linting and formatting
uv run ruff check .
uv run ruff format .

# Run type checking
uv run ty check .

# Setup prek hooks
uv run prek install
```

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) and are checked by [commitizen](https://commitizen-tools.github.io/commitizen/).

## 🤝 Contributing

Contributions are welcome. See [CONTRIBUTING.md](https://github.com/mhajder/pyekw/blob/main/CONTRIBUTING.md) for the dev setup, checks and commit message format, and use the [issue templates](https://github.com/mhajder/pyekw/issues/new/choose) for bugs and feature requests.

Found a security problem? Please report it privately as described in [SECURITY.md](https://github.com/mhajder/pyekw/blob/main/SECURITY.md).

## 📜 License

MIT License - see [LICENSE](https://github.com/mhajder/pyekw/blob/main/LICENSE) for details.
