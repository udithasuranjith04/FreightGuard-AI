"""The review aid identifies secret-like values without returning those values."""

import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "audit_repository",
    Path(__file__).resolve().parents[1] / "scripts/audit_repository.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_scanner_redacts_matches_and_allows_synthetic_contacts():
    token = b"ghp_" + b"A" * 36
    assert MODULE.findings(token) == ["github_token"]
    assert token.decode() not in str(MODULE.findings(token))
    assert MODULE.findings(b"person@example.invalid") == []
    assert MODULE.findings(b"person@" + b"private.test") == ["email_literal"]
