#!/usr/bin/env python3
"""Regenerate the shields.io badge block in a repo's README.md.

Looks for a marker pair:

    <!-- BADGES:START -->
    ...
    <!-- BADGES:END -->

and replaces everything between them with a standard badge set for
OWNER_REPO (read from the OWNER_REPO env var, e.g. "CMDRPhaedra/Picker").
Does nothing if README.md is missing or has no marker pair.

shields.io's dynamic `github/...` badges call GitHub's API unauthenticated,
which 404s for private repos ("repo not found"). For private repos we instead
fetch the same data ourselves via `gh api` (authenticated with the Action's
own token) and bake it into static badges — refreshed on every run rather
than live, which is the best a private repo can do.
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

README_PATH = Path(sys.argv[1] if len(sys.argv) > 1 else "README.md")
REPO_ROOT = README_PATH.parent
START = "<!-- BADGES:START -->"
END = "<!-- BADGES:END -->"

LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt")


def static_badge(label: str, message: str, color: str) -> str:
    l = urllib.parse.quote(label, safe="")
    m = urllib.parse.quote(message, safe="")
    return f"![{label}](https://img.shields.io/badge/{l}-{m}-{color})"


def gh_api(path: str):
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def local_last_commit_date() -> str:
    out = subprocess.run(
        ["git", "log", "-1", "--format=%cd", "--date=short"],
        capture_output=True, text=True, cwd=REPO_ROOT, check=True,
    )
    return out.stdout.strip()


def format_size(size_kb: int) -> str:
    if size_kb < 1024:
        return f"{size_kb} KB"
    return f"{size_kb / 1024:.1f} MB"


def license_badge(owner_repo: str, private: bool, repo_info: dict) -> str:
    """Proprietary "All rights reserved" content has no SPDX id, so GitHub's
    dynamic license badge would just render blank — use a static badge for it
    instead. Anything else (MIT, GPL, CC, ...) uses the normal dynamic badge
    for public repos, or a static one baked from the API for private repos.
    """
    for name in LICENSE_NAMES:
        path = REPO_ROOT / name
        if path.exists() and "all rights reserved" in path.read_text().lower():
            return static_badge("license", "All rights reserved", "blue")
    if private:
        spdx = (repo_info.get("license") or {}).get("spdx_id")
        return static_badge("license", spdx or "none", "lightgrey")
    return f"![License](https://img.shields.io/github/license/{owner_repo})"


def uses_python() -> bool:
    if any(REPO_ROOT.rglob("*.py")):
        return True
    return any((REPO_ROOT / name).exists() for name in ("requirements.txt", "pyproject.toml"))


def build_block(owner_repo: str) -> str:
    repo_info = gh_api(f"repos/{owner_repo}")
    private = bool(repo_info.get("private"))

    badges = [license_badge(owner_repo, private, repo_info)]

    if private:
        languages = gh_api(f"repos/{owner_repo}/languages")
        top_language = max(languages, key=languages.get) if languages else None
        badges += [
            static_badge("last commit", local_last_commit_date(), "blue"),
            static_badge("repo size", format_size(repo_info.get("size", 0)), "blue"),
        ]
        if top_language:
            badges.append(static_badge("language", top_language, "blue"))
        badges.append(static_badge("issues", str(repo_info.get("open_issues_count", 0)), "blue"))
    else:
        badges += [
            f"![Last commit](https://img.shields.io/github/last-commit/{owner_repo})",
            f"![Repo size](https://img.shields.io/github/repo-size/{owner_repo})",
            f"![Top language](https://img.shields.io/github/languages/top/{owner_repo})",
            f"![Open issues](https://img.shields.io/github/issues/{owner_repo})",
        ]

    if uses_python():
        badges.append("![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)")

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
