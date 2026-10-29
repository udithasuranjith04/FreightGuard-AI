"""Redacted local secret-pattern/path audit of reachable Git blobs and public files.

This is a small review aid, not a guarantee that arbitrary personal data is absent.
It never prints matching values, raw rows, file contents, or commit messages.
"""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "github_token": re.compile(
        rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{60,})"
    ),
    "openai_token": re.compile(rb"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{40,}"),
    "literal_credential": re.compile(
        rb"(?i)(?:api_key|api_secret|access_token|client_secret|password)"
        rb"\s*[=:]\s*[\"'][A-Za-z0-9_+/=-]{16,}[\"']"
    ),
    "email_literal": re.compile(rb"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
}
SAFE_EMAIL_DOMAINS = (
    b"example.com",
    b"example.invalid",
    b"example.org",
    b"example.test",
)


def findings(content: bytes) -> list[str]:
    """Return pattern names only, never values."""
    result = []
    for name, pattern in PATTERNS.items():
        matches = pattern.findall(content)
        if name == "email_literal":
            matches = [
                value
                for value in matches
                if value.rsplit(b"@", 1)[-1].lower() not in SAFE_EMAIL_DOMAINS
            ]
        if matches:
            result.append(name)
    return result


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def audit() -> dict:
    """Inspect all reachable file history plus public working files and build output."""
    issues = []
    history_count = 0
    objects = git("rev-list", "--objects", "--all").splitlines()
    for line in objects:
        oid, _, path = line.partition(b" ")
        if not path or git("cat-file", "-t", oid.decode()).strip() != b"blob":
            continue
        history_count += 1
        name = path.decode(errors="replace")
        if (
            name.startswith(("data/raw/", "data/processed/"))
            and not name.endswith("/.gitkeep")
        ) or (".env" in Path(name).name and not name.endswith(".env.example")):
            issues.append({"scope": "history", "path": name, "kind": "private_path"})
        for kind in findings(git("cat-file", "blob", oid.decode())):
            issues.append({"scope": "history", "path": name, "kind": kind})
    paths = git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    working = {ROOT / name.decode() for name in paths.split(b"\0") if name}
    working.update((ROOT / "frontend/dist").rglob("*"))
    count = 0
    for path in sorted(working):
        if not path.is_file():
            continue
        count += 1
        for kind in findings(path.read_bytes()):
            issues.append(
                {
                    "scope": "working_or_bundle",
                    "path": str(path.relative_to(ROOT)),
                    "kind": kind,
                }
            )
    return {
        "history_blobs_checked": history_count,
        "public_files_checked": count,
        "findings": issues,
    }


if __name__ == "__main__":
    report = audit()
    print(json.dumps(report, indent=2))
    raise SystemExit(bool(report["findings"]))
