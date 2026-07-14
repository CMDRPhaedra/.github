#!/usr/bin/env python3
"""Regenerate the shields.io badge block in a repo's README.md.

Looks for a marker pair:

    <!-- BADGES:START -->
    ...
    <!-- BADGES:END -->

and replaces everything between them with a standard badge set for
OWNER_REPO (read from the OWNER_REPO env var, e.g. "CMDRPhaedra/Picker").
Does nothing if README.md is missing or has no marker pair.
"""
import os
import re
import sys
from pathlib import Path

README_PATH = Path(sys.argv[1] if len(sys.argv) > 1 else "README.md")
START = "<!-- BADGES:START -->"
END = "<!-- BADGES:END -->"


def build_block(owner_repo: str) -> str:
    badges = [
        f"![License](https://img.shields.io/github/license/{owner_repo})",
        f"![Last commit](https://img.shields.io/github/last-commit/{owner_repo})",
        f"![Repo size](https://img.shields.io/github/repo-size/{owner_repo})",
        f"![Top language](https://img.shields.io/github/languages/top/{owner_repo})",
        f"![Open issues](https://img.shields.io/github/issues/{owner_repo})",
    ]
    return "\n".join(badges)


def main() -> None:
    owner_repo = os.environ["OWNER_REPO"]

    if not README_PATH.exists():
        print(f"{README_PATH} not found — skipping.")
        return

    text = README_PATH.read_text()
    if START not in text or END not in text:
        print(f"No {START}/{END} markers in {README_PATH} — skipping.")
        return

    block = build_block(owner_repo)
    new_text = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        f"{START}\n{block}\n{END}",
        text,
        flags=re.S,
    )

    if new_text == text:
        print("Badges already up to date.")
        return

    README_PATH.write_text(new_text)
    print("Badge block updated.")


if __name__ == "__main__":
    main()
