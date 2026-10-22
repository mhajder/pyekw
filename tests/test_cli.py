"""
Tests for the pyekw command-line interface.
"""

import json
import os
import runpy
import sys

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
