#!/usr/bin/env python3
"""Extract inline <script> blocks from HTML files and run node --check."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path


class ScriptCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_script = False
        self._current: list[str] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "script":
            return
        attr_map = {key.lower(): value for key, value in attrs}
        script_type = (attr_map.get("type") or "text/javascript").lower()
        if attr_map.get("src"):
            return
        if script_type in {"text/javascript", "application/javascript", "module"}:
            self._in_script = True
            self._current = []

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self._current.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_script:
            script = "".join(self._current).strip()
            if script:
                self.scripts.append(script)
            self._in_script = False
            self._current = []


def check_html(path: Path) -> int:
    parser = ScriptCollector()
    parser.feed(path.read_text(encoding="utf-8"))

    if not parser.scripts:
        print(f"{path}: no inline JavaScript blocks found")
        return 0

    with tempfile.TemporaryDirectory() as tmpdir:
        for index, script in enumerate(parser.scripts, start=1):
            script_path = Path(tmpdir) / f"{path.stem}-script-{index}.js"
            script_path.write_text(script, encoding="utf-8")
            result = subprocess.run(["node", "--check", str(script_path)], text=True)
            if result.returncode != 0:
                print(f"{path}: script block {index} failed node --check")
                return result.returncode
            print(f"{path}: script block {index} passed node --check")

    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: check_html_scripts.py <html-file> [<html-file> ...]", file=sys.stderr)
        return 2

    exit_code = 0
    for raw_path in argv[1:]:
        path = Path(raw_path)
        if not path.exists():
            print(f"Missing HTML file: {path}", file=sys.stderr)
            exit_code = 1
            continue
        exit_code = max(exit_code, check_html(path))
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
