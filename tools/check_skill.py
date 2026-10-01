#!/usr/bin/env python3
"""Publication gate for a skill in this repository. Every skill must pass it before it is merged.

    python tools/check_skill.py skills/<name>      # one skill
    python tools/check_skill.py --all              # every skill

Checks (each failure is printed with the reason; exit 1 if any skill fails):
  1. SKILL.md with frontmatter: name (= folder name), description (>= 80 chars), version, license
  2. license is an OSI-approved SPDX id
  3. evals/BENCHMARK.md exists and reports a with/without comparison (the point of this repository)
  4. a test file exists in tests/ for the skill
  5. no secrets, no absolute user paths, no private markers in any file of the skill
  6. scripts use only the Python standard library (so the skill runs anywhere without installing anything)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OSI = {"Apache-2.0", "MIT", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0"}
SECRET = re.compile(r"\bsk-[A-Za-z0-9_-]{20,}|\bgh[pousr]_[A-Za-z0-9]{30,}|\bAKIA[0-9A-Z]{16}\b|"
                    r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
PRIVATE = re.compile(r"[A-Za-z]:[\\/]Users[\\/]|/home/[a-z]+/", re.I)
#: extra private words (internal project or file names) live in an untracked file, never in the code
MARKERS_FILE = ROOT / ".private-markers"
EXTRA = [w.strip().lower() for w in (MARKERS_FILE.read_text(encoding="utf-8").splitlines()
                                     if MARKERS_FILE.exists() else []) if w.strip() and not w.startswith("#")]


def frontmatter(text: str) -> dict:
    m = re.match(r"﻿?---\s*\n(.*?)\n---", text, re.DOTALL)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k, sep, v = line.partition(":")
        if sep and not k.startswith((" ", "\t")):
            out[k.strip().lower()] = v.strip().strip("\"'")
    return out


def check(skill_dir: Path) -> list:
    problems = []
    md = skill_dir / "SKILL.md"
    if not md.is_file():
        return ["SKILL.md missing"]
    fm = frontmatter(md.read_text(encoding="utf-8"))
    if fm.get("name") != skill_dir.name:
        problems.append(f"frontmatter name {fm.get('name')!r} must equal the folder name {skill_dir.name!r}")
    if len(fm.get("description", "")) < 80:
        problems.append("description shorter than 80 characters: say what it does AND when to use it")
    if not fm.get("version"):
        problems.append("version missing")
    if fm.get("license") not in OSI:
        problems.append(f"license {fm.get('license')!r} is not an OSI-approved SPDX id")
    bench = skill_dir / "evals" / "BENCHMARK.md"
    if not bench.is_file():
        problems.append("evals/BENCHMARK.md missing: every skill here is measured with and without it")
    elif not re.search(r"without", bench.read_text(encoding="utf-8"), re.I):
        problems.append("evals/BENCHMARK.md does not report a comparison without the skill")
    if not (ROOT / "tests" / f"test_{skill_dir.name.replace('-', '_')}.py").is_file():
        problems.append(f"tests/test_{skill_dir.name.replace('-', '_')}.py missing")
    std = set(sys.stdlib_module_names)
    for f in skill_dir.rglob("*"):
        if not f.is_file() or f.suffix not in (".md", ".py", ".txt", ".json", ".toml", ".sh"):
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        if SECRET.search(text):
            problems.append(f"{f.relative_to(skill_dir)}: looks like a secret")
        if PRIVATE.search(text) or any(w in text.lower() for w in EXTRA):
            problems.append(f"{f.relative_to(skill_dir)}: contains a private path or marker")
        if f.suffix == ".py":
            for mod in re.findall(r"^\s*(?:from|import)\s+([a-zA-Z_]\w*)", text, re.M):
                if mod not in std and mod != "__future__":
                    problems.append(f"{f.relative_to(skill_dir)}: imports {mod!r} (standard library only)")
    return problems


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    dirs = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir()) if argv == ["--all"] else [Path(a) for a in argv]
    failed = 0
    for d in dirs:
        probs = check(d)
        print(f"{'PASS' if not probs else 'FAIL'}  {d.name}")
        for p in probs:
            print(f"      - {p}")
        failed += bool(probs)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
