"""
Tests for the pyekw command-line interface.
"""

import json
import os
import runpy
import sys
from unittest.mock import MagicMock

import pytest

import pyekw
from pyekw.cli import main


class TestCLI:
    def test_version(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])

        assert exc_info.value.code == 0
        assert capsys.readouterr().out == f"pyekw {pyekw.__version__}\n"

    def test_command_is_required(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main([])

        assert exc_info.value.code == 2
        assert "required" in capsys.readouterr().err

    def test_validate_valid(self, capsys):
        assert main(["validate", "WA4M/00123456/4", "kr1p/00012345/2"]) == 0
        assert capsys.readouterr().out == (
            "WA4M/00123456/4: valid\nKR1P/00012345/2: valid\n"
        )

    def test_validate_invalid_with_suggestion(self, capsys):
        assert main(["validate", "WA4M/00123456/4", "WA4M/00123456/5"]) == 1
        assert capsys.readouterr().out == (
            "WA4M/00123456/4: valid\n"
            "WA4M/00123456/5: invalid (Invalid check digit: expected 4, got 5)\n"
            "  did you mean: WA4M/00123456/4\n"
        )

    def test_validate_invalid_without_suggestion(self, capsys):
        assert main(["validate", "INVALID"]) == 1
        assert capsys.readouterr().out.startswith("INVALID: invalid (")

    def test_validate_no_check_court(self, capsys):
        assert main(["validate", "--no-check-court", "WA9M/00123456/9"]) == 0
        assert capsys.readouterr().out == "WA9M/00123456/9: valid\n"

    def test_validate_no_check_court_suggestion_keeps_court(self, capsys):
        assert main(["validate", "--no-check-court", "WA9M/00123456/0"]) == 1
        assert capsys.readouterr().out == (
            "WA9M/00123456/0: invalid (Invalid check digit: expected 9, got 0)\n"
            "  did you mean: WA9M/00123456/9\n"
        )

    def test_validate_keeps_duplicate_inputs(self, capsys):
        assert main(["validate", "--json", "WA4M/00123456/4", "wa4m/00123456/4"]) == 0
        results = json.loads(capsys.readouterr().out)

        assert [result["original"] for result in results] == [
            "WA4M/00123456/4",
            "wa4m/00123456/4",
        ]

    def test_validate_no_check_court_invalid_character(self, capsys):
        assert main(["validate", "--no-check-court", "WA4Q/00123456/4"]) == 1
        assert capsys.readouterr().out.splitlines() == [
            "WA4Q/00123456/4: invalid (Invalid character 'Q' in court code)",
            "  did you mean: WA4M/00123456/4, WA1G/00123456/7, WA1I/00123456/9",
        ]

    def test_validate_json(self, capsys):
        assert main(["validate", "--json", "WA4M/00123456/4"]) == 0
        results = json.loads(capsys.readouterr().out)

        assert len(results) == 1
        assert results[0]["normalized"] == "WA4M/00123456/4"
        assert results[0]["is_valid"] is True
        assert results[0]["court_name"] == "WARSZAWA (X)"

    def test_info(self, capsys):
        assert main(["info", "wa4m / 00123456 / 4"]) == 0
        out = capsys.readouterr().out

        assert "KW number:        WA4M/00123456/4\n" in out
        assert "Court:            WARSZAWA (X)\n" in out
        assert "Check digit:      4\n" in out

    def test_info_without_circuit_or_voivodeship(self, capsys, monkeypatch):
        from pyekw.utils import KWUtils

        original_get = KWUtils.get_kw_info

        def mock_get(self, kw, auto_pad=False):
            info = original_get(self, kw, auto_pad=auto_pad)
            if info:
                info["circuit"] = None
                info["voivodeship"] = None
            return info

        monkeypatch.setattr(KWUtils, "get_kw_info", mock_get)
        assert main(["info", "WA4M/00123456/4"]) == 0
        out = capsys.readouterr().out
        assert "Circuit:" not in out
        assert "Voivodeship:" not in out
        assert "Compact:          WA4M001234564" in out

    def test_info_json(self, capsys):
        assert main(["info", "--json", "WA4M/00123456/4"]) == 0
        info = json.loads(capsys.readouterr().out)

        assert info["court_code"] == "WA4M"
        assert info["check_digit"] == 4

    def test_info_invalid(self, capsys):
        assert main(["info", "WA4M/00123456/5"]) == 1
        captured = capsys.readouterr()

        assert captured.out == ""
        assert captured.err == "error: Invalid check digit: expected 4, got 5\n"

    def test_extract_file(self, capsys, tmp_path):
        text_file = tmp_path / "umowa.txt"
        text_file.write_text(
            "KW WA4M / 00123456 / 4, KR1P/00012345/2,\n"
            "ponownie WA4M/00123456/4 i błędna WA4M/00123456/5.\n",
            encoding="utf-8",
        )

        assert main(["extract", str(text_file)]) == 0
        assert capsys.readouterr().out == (
            "WA4M/00123456/4\nKR1P/00012345/2\nWA4M/00123456/5\n"
        )

    def test_extract_stdin_valid_only_json(self, capsys, monkeypatch):
        monkeypatch.setattr("sys.stdin.read", lambda: "WA4M/00123456/4 WA4M/00123456/5")

        assert main(["extract", "--valid-only", "--json"]) == 0
        assert json.loads(capsys.readouterr().out) == ["WA4M/00123456/4"]

    def test_extract_nothing_found(self, capsys, tmp_path):
        text_file = tmp_path / "empty.txt"
        text_file.write_text("No KW numbers here", encoding="utf-8")

        assert main(["extract", str(text_file)]) == 1
        assert capsys.readouterr().out == ""

    def test_extract_missing_file(self, capsys, tmp_path):
        missing = tmp_path / "missing.txt"

        assert main(["extract", str(missing)]) == 2
        captured = capsys.readouterr()

        assert captured.out == ""
        assert captured.err.startswith(f"error: cannot read {missing}: ")

    def test_extract_non_utf8_file(self, capsys, tmp_path):
        text_file = tmp_path / "cp1250.txt"
        text_file.write_bytes("Księga WA4M/00123456/4".encode("cp1250"))

        assert main(["extract", str(text_file)]) == 2
        assert capsys.readouterr().err.startswith(f"error: cannot read {text_file}: ")

    def test_extract_check_continues_after_unreadable_file(self, capsys, tmp_path):
        unreadable = tmp_path / "cp1250.txt"
        unreadable.write_bytes("Księga WA4M/00123456/4".encode("cp1250"))
        docs = tmp_path / "docs.md"
        docs.write_text("WA4M/00123456/5", encoding="utf-8")

        assert main(["extract", "--check", str(unreadable), str(docs)]) == 2
        captured = capsys.readouterr()
        assert captured.err.startswith(f"error: cannot read {unreadable}: ")
        assert captured.out == (
            f"{docs}: WA4M/00123456/5: invalid"
            " (Invalid check digit: expected 4, got 5)\n"
        )

    def test_extract_continues_after_missing_file(self, capsys, tmp_path):
        missing = tmp_path / "missing.txt"
        docs = tmp_path / "docs.md"
        docs.write_text("WA4M/00123456/4", encoding="utf-8")

        assert main(["extract", str(missing), str(docs)]) == 2
        captured = capsys.readouterr()
        assert captured.err.startswith(f"error: cannot read {missing}: ")
        assert captured.out == "WA4M/00123456/4\n"

    def test_broken_pipe(self, capfd, monkeypatch):
        """A closed stdout pipe (e.g. `| head -1`) exits quietly instead of a traceback."""

        def raise_broken_pipe(*_args, **_kwargs):
            raise BrokenPipeError

        dup2_calls = []
        monkeypatch.setattr("builtins.print", raise_broken_pipe)
        monkeypatch.setattr(os, "dup2", lambda fd, fd2: dup2_calls.append((fd, fd2)))

        assert main(["validate", "WA4M/00123456/4"]) == 1
        assert capfd.readouterr().err == ""
        [(devnull_fd, stdout_fd)] = dup2_calls
        os.close(devnull_fd)
        assert stdout_fd == sys.stdout.fileno()

    def test_run_as_module(self, capsys, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["pyekw", "validate", "WA4M/00123456/4"])

        with pytest.raises(SystemExit) as exc_info:
            runpy.run_module("pyekw", run_name="__main__")

        assert exc_info.value.code == 0
        assert capsys.readouterr().out == "WA4M/00123456/4: valid\n"

    def test_validate_auto_pad(self, capsys):
        assert main(["validate", "--auto-pad", "WA4M/123456/4"]) == 0
        assert capsys.readouterr().out == "WA4M/00123456/4: valid\n"

    def test_info_with_auto_pad_and_regional_info(self, capsys):
        assert main(["info", "--auto-pad", "WA4M/123456/4"]) == 0
        out = capsys.readouterr().out
        assert "KW number:        WA4M/00123456/4\n" in out
        assert "Circuit:          Sąd Okręgowy w Warszawie\n" in out
        assert "Voivodeship:      mazowieckie\n" in out
        assert "Compact:          WA4M001234564\n" in out

    def test_extract_include_compact(self, capsys, tmp_path):
        text_file = tmp_path / "compact.txt"
        text_file.write_text(
            "Text with WA4M001234564 and KR1P000123452", encoding="utf-8"
        )
        assert main(["extract", "--include-compact", str(text_file)]) == 0
        assert capsys.readouterr().out == "WA4M/00123456/4\nKR1P/00012345/2\n"

    def test_extract_multiple_files(self, capsys, tmp_path):
        first = tmp_path / "a.md"
        first.write_text("WA4M/00123456/4 i KR1P/00012345/2", encoding="utf-8")
        second = tmp_path / "b.md"
        second.write_text("KR1P/00012345/2 oraz WA4M/00000001/2", encoding="utf-8")

        assert main(["extract", str(first), str(second)]) == 0
        assert capsys.readouterr().out == (
            "WA4M/00123456/4\nKR1P/00012345/2\nWA4M/00000001/2\n"
        )

    def test_extract_check_passes_without_invalid_numbers(self, capsys, tmp_path):
        valid = tmp_path / "valid.md"
        valid.write_text("WA4M/00123456/4", encoding="utf-8")
        empty = tmp_path / "empty.md"
        empty.write_text("No KW numbers here", encoding="utf-8")

        assert main(["extract", "--check", str(valid), str(empty)]) == 0
        assert capsys.readouterr().out == ""

    def test_extract_check_reports_invalid_numbers(self, capsys, tmp_path):
        text_file = tmp_path / "docs.md"
        text_file.write_text(
            "WA4M/00123456/4, WA4M/00123456/5, again WA4M/00123456/5", encoding="utf-8"
        )

        assert main(["extract", "--check", str(text_file)]) == 1
        assert capsys.readouterr().out == (
            f"{text_file}: WA4M/00123456/5: invalid"
            " (Invalid check digit: expected 4, got 5)\n"
        )

    def test_extract_check_json(self, capsys, tmp_path):
        text_file = tmp_path / "docs.md"
        text_file.write_text("ZZ9Z/00012345/5", encoding="utf-8")

        assert main(["extract", "--check", "--json", str(text_file)]) == 1
        assert json.loads(capsys.readouterr().out) == [
            {
                "file": str(text_file),
                "kw_number": "ZZ9Z/00012345/5",
                "error": "Unknown court code: ZZ9Z",
            }
        ]

    def test_extract_check_and_valid_only_are_exclusive(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["extract", "--check", "--valid-only"])
        assert exc_info.value.code == 2
        assert "not allowed with argument" in capsys.readouterr().err

    def test_generate_single(self, capsys):
        assert main(["generate", "WA4M", "12345"]) == 0
        assert capsys.readouterr().out == "WA4M/00012345/2\n"

    def test_generate_multiple(self, capsys):
        assert main(["generate", "WA4M", "12345", "--count", "3"]) == 0
        assert capsys.readouterr().out == (
            "WA4M/00012345/2\nWA4M/00012346/9\nWA4M/00012347/6\n"
        )

    def test_generate_count_zero(self, capsys):
        assert main(["generate", "WA4M", "12345", "--count", "0"]) == 1
        assert "error: --count must be at least 1" in capsys.readouterr().err

    def test_generate_compact(self, capsys):
        assert main(["generate", "WA4M", "12345", "--compact"]) == 0
        assert capsys.readouterr().out == "WA4M000123452\n"

    def test_generate_json(self, capsys):
        assert main(["generate", "WA4M", "12345", "--json"]) == 0
        assert json.loads(capsys.readouterr().out) == ["WA4M/00012345/2"]

    def test_generate_no_pad_valid(self, capsys):
        assert main(["generate", "WA4M", "00012345", "--no-pad"]) == 0
        assert capsys.readouterr().out == "WA4M/00012345/2\n"

    def test_generate_no_pad_invalid_length(self, capsys):
        assert main(["generate", "WA4M", "12345", "--no-pad"]) == 1
        assert (
            "error: register number must be exactly 8 digits" in capsys.readouterr().err
        )

    def test_generate_invalid_number_chars(self, capsys):
        assert main(["generate", "WA4M", "abc"]) == 1
        assert (
            "error: register number must contain only digits" in capsys.readouterr().err
        )

    @pytest.mark.parametrize("number", ["²", "١٢٣"])
    def test_generate_rejects_non_ascii_digits(self, capsys, number):
        assert main(["generate", "WA4M", number]) == 1
        assert (
            "error: register number must contain only digits" in capsys.readouterr().err
        )

    def test_generate_overflow(self, capsys):
        assert main(["generate", "WA4M", "99999999", "--count", "2"]) == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "error: register numbers would exceed 99999999" in captured.err

    def test_generate_rejects_too_many_digits(self, capsys):
        assert main(["generate", "WA4M", "000000000012345"]) == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "error: register number cannot exceed 8 digits, got 15" in captured.err

    def test_generate_last_register_number(self, capsys):
        assert main(["generate", "WA4M", "99999999", "--compact"]) == 0
        assert capsys.readouterr().out.startswith("WA4M99999999")

    def test_generate_unknown_court(self, capsys):
        assert main(["generate", "ZZ9Z", "00012345"]) == 1
        assert "error: unknown court code: ZZ9Z" in capsys.readouterr().err

    def test_generate_unknown_court_allowed(self, capsys):
        assert main(["generate", "ZZ9Z", "00012345", "--no-check-court"]) == 0
        assert capsys.readouterr().out == "ZZ9Z/00012345/5\n"

    def test_generate_invalid_character_value(self, capsys, monkeypatch):
        import pyekw.cli

        monkeypatch.setattr(
            pyekw.cli.CheckDigitGenerator,
            "calculate_check_digit",
            MagicMock(side_effect=ValueError("Test error")),
        )
        assert main(["generate", "WA4M", "00012345", "--no-check-court"]) == 1
        assert "error: Test error" in capsys.readouterr().err

    def test_courts_list_and_search(self, capsys):
        assert main(["courts", "Kraków"]) == 0
        out = capsys.readouterr().out
        assert "KR1P: KRAKÓW (małopolskie)" in out

    def test_courts_filter_voivodeship(self, capsys):
        assert main(["courts", "--voivodeship", "małopolskie"]) == 0
        out = capsys.readouterr().out
        assert "KR1P: KRAKÓW (małopolskie)" in out

    def test_courts_filter_circuit(self, capsys):
        assert main(["courts", "--circuit", "Warszawie"]) == 0
        out = capsys.readouterr().out
        assert "WA4M: WARSZAWA (X) (mazowieckie)" in out

    def test_courts_json(self, capsys):
        assert main(["courts", "KR1P", "--json"]) == 0
        results = json.loads(capsys.readouterr().out)
        assert len(results) == 1
        assert results[0]["court_code"] == "KR1P"
        assert results[0]["circuit"] == "Sąd Okręgowy w Krakowie"
        assert results[0]["voivodeship"] == "małopolskie"

    def test_courts_no_matches(self, capsys):
        assert main(["courts", "NONEXISTENT_COURT_SEARCH"]) == 1
        assert "No matching courts found." in capsys.readouterr().err

    def test_courts_no_matches_json(self, capsys):
        assert main(["courts", "NONEXISTENT_COURT_SEARCH", "--json"]) == 1
        captured = capsys.readouterr()
        assert json.loads(captured.out) == []
        assert captured.err == ""

    def test_courts_filter_voivodeship_with_prefix(self, capsys):
        assert main(["courts", "--voivodeship", "województwo Małopolskie"]) == 0
        assert "KR1P: KRAKÓW (małopolskie)" in capsys.readouterr().out

    def test_courts_query_does_not_match_circuit(self):
        assert main(["courts", "Sąd Okręgowy"]) == 1

    def test_courts_combined_filters(self, capsys):
        assert main(["courts", "KR", "--circuit", "Krakowie", "--json"]) == 0
        results = json.loads(capsys.readouterr().out)
        assert results
        assert all(court["circuit"] == "Sąd Okręgowy w Krakowie" for court in results)

    def test_courts_list_all(self, capsys):
        assert main(["courts", "--json"]) == 0
        assert len(json.loads(capsys.readouterr().out)) == len(
            pyekw.CourtRegistry().get_all_courts()
        )
