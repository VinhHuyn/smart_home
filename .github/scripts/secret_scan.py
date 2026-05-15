#!/usr/bin/env python3
"""Small repository secret scan for CI.

This intentionally scans only git-tracked text files. It is not a replacement for
GitHub secret scanning, but catches common accidental Home Assistant/API token
leaks in docs and examples.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ALLOWLIST_FRAGMENTS = (
    "[REDACTED]",
    "<redacted>",
    "YOUR_HOME_ASSISTANT_LONG_LIVED_ACCESS_TOKEN",
    "YOUR_TOKEN",
    "your-token",
    "new-token",
    "old-token",
    "fallback-token",
    "example",
    "placeholder",
)

PATTERNS = [
    re.compile(r"Authorization:\s*Bearer\s+([^\s'\"`<>]+)", re.IGNORECASE),
    re.compile(r"\b(?:HA_TOKEN|HASS_TOKEN|GITHUB_TOKEN|API_KEY)\s*=\s*([^\s'\"`]+)", re.IGNORECASE),
    re.compile(r"\b(?:token|api[_-]?key|secret)\s*[:=]\s*['\"]([^'\"]{16,})['\"]", re.IGNORECASE),
]

SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".pyc",
    ".zip",
}


def tracked_files() -> list[Path]:
    output = subprocess.check_output(["git", "ls-files"], text=True)
    return [Path(line) for line in output.splitlines() if line.strip()]


def is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(fragment.lower() in lowered for fragment in ALLOWLIST_FRAGMENTS)


def main() -> int:
    findings: list[str] = []

    for path in tracked_files():
        if path.suffix.lower() in SKIP_SUFFIXES or not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for line_no, line in enumerate(text.splitlines(), start=1):
            for pattern in PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                value = match.group(1).strip()
                if is_placeholder(value):
                    continue
                if len(value) < 16 and not re.search(r"[A-Za-z0-9_-]{12,}", value):
                    continue
                findings.append(f"{path}:{line_no}: possible secret in: {line.strip()[:140]}")

    if findings:
        print("Potential secret leaks found in tracked files:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("No obvious secret leaks found in tracked files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
