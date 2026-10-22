"""
Tests for package metadata.
"""

import importlib
import importlib.metadata

import pyekw


def test_version_matches_installed_metadata():
    assert pyekw.__version__ == importlib.metadata.version("pyekw")


def test_version_fallback_when_not_installed(monkeypatch):
    def raise_not_found(_name):
        raise importlib.metadata.PackageNotFoundError

    monkeypatch.setattr(importlib.metadata, "version", raise_not_found)
    try:
        assert importlib.reload(pyekw).__version__ == "0.0.0"
    finally:
        monkeypatch.undo()
        importlib.reload(pyekw)
