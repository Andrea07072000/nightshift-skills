#!/usr/bin/env python3
"""3am-safety preflight: is it safe to leave an agent working unattended on this repository?

Read-only. Standard library only. Never prints a secret value (only file, line and the kind of secret).

    python preflight.py [REPO] [--json] [--min-free-gb 5] [--big-file-mb 50]

Exit codes: 0 GO · 1 GO WITH WARNINGS · 2 NO-GO · 3 could not run the checks.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SECRET_PATTERNS = [
    ("openai/openrouter-style key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("github token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("aws access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("google api key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("password assignment", re.compile(r"(?i)\b(password|passwd|secret|api_key|apikey|token)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]")),
]
SECRET_FILE_NAMES = re.compile(r"(^|/)(\.env(\..*)?|id_rsa|id_ed25519|.*\.pem|.*\.key|credentials(\.json)?|secrets?(\.\w+)?|.*api[_-]?keys?(\.\w+)?)$",
                               re.IGNORECASE)
TEXT_LIMIT = 1024 * 1024


def git(repo: Path, *args: str) -> Optional[str]:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=30,
                           encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def finding(level: str, check: str, message: str, **extra: Any) -> Dict[str, Any]:
    return {"level": level, "check": check, "message": message, **extra}


def check_git(repo: Path, big_mb: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    top = git(repo, "rev-parse", "--show-toplevel")
    if top is None:
        return [finding("WARN", "git", "not a git repository: no history to roll back to if something goes wrong")]
    root = Path(top.strip())
    if (root / ".git" / "index.lock").exists():
        out.append(finding("BLOCK", "git", "a git index.lock exists: another git process is running or crashed"))
    head = (git(repo, "symbolic-ref", "-q", "--short", "HEAD") or "").strip()
    if not head:
        out.append(finding("WARN", "git", "detached HEAD: commits made overnight will be hard to find"))
    status = git(repo, "status", "--porcelain=v1", "--untracked-files=all") or ""
    modified = [ln[3:] for ln in status.splitlines() if ln and not ln.startswith("??")]
    untracked = [ln[3:] for ln in status.splitlines() if ln.startswith("??")]
    if modified:
        out.append(finding("WARN", "git", f"{len(modified)} uncommitted change(s): commit or stash them so the unattended "
                                          "run starts from a known state", files=modified[:20]))
    if untracked:
        out.append(finding("WARN", "git", f"{len(untracked)} new file(s) never committed: work that exists only on disk "
                                          "is lost if the run deletes or overwrites it", files=untracked[:20]))
    ahead = git(repo, "rev-list", "--count", "@{u}..HEAD")
    if ahead and ahead.strip() != "0":
        out.append(finding("INFO", "git", f"{ahead.strip()} local commit(s) not pushed (backup risk if the disk fails)"))
    for f in untracked + modified:
        p = root / f.strip('"')
        try:
            size = p.stat().st_size if p.is_file() else 0
        except OSError:
            size = 0
        if size > big_mb * 1024 * 1024 and f in untracked:
            out.append(finding("WARN", "disk", f"large untracked file ({size // (1024 * 1024)} MB): an automatic "
                                               "commit would bloat the history", file=f))
    if not (root / ".gitignore").exists():
        out.append(finding("WARN", "git", "no .gitignore: caches and build output (__pycache__, node_modules, "
                                          ".pytest_cache) will end up in the run's commits"))
    if head in ("main", "master"):
        out.append(finding("INFO", "git", f"on '{head}': give the unattended run its own branch, so its commits can be "
                                          "reviewed or dropped as a whole"))
    remotes = (git(repo, "remote") or "").split()
    if remotes:
        out.append(finding("INFO", "publish", f"git remotes configured ({', '.join(remotes)}): an unattended push would "
                                              "publish; make sure the task does not push unless intended"))
    else:
        out.append(finding("INFO", "backup", "no remote: this repository exists in one copy only; make a backup "
                                             "(e.g. git bundle create ../backup.bundle --all) before a long run"))
    return out + check_secrets(root, untracked + modified)


EXTRA_SECRET_FILES: List[str] = []          # --secret-file NAME: private names you do not want written in code


def check_secrets(root: Path, files: List[str]) -> List[Dict[str, Any]]:
    """Only files git would pick up (modified or untracked and NOT ignored): ignored files cannot be committed."""
    out: List[Dict[str, Any]] = []
    for f in files:
        rel = f.strip('"')
        p = root / rel
        base = rel.replace("\\", "/").rsplit("/", 1)[-1]
        if SECRET_FILE_NAMES.search(rel.replace("\\", "/")) or base in EXTRA_SECRET_FILES:
            out.append(finding("BLOCK", "secrets", "a credentials file is not ignored by git and could be committed",
                               file=rel))
            continue
        if not p.is_file():
            continue
        try:
            if p.stat().st_size > TEXT_LIMIT:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for kind, rx in SECRET_PATTERNS:
                if rx.search(line):
                    out.append(finding("BLOCK", "secrets", f"possible {kind} in a file that is not committed yet "
                                                           "(value not shown)", file=rel, line=lineno))
                    break
    return out


def check_disk(repo: Path, min_free_gb: float) -> List[Dict[str, Any]]:
    try:
        u = shutil.disk_usage(repo)
    except OSError as exc:
        return [finding("WARN", "disk", f"cannot read free space: {exc}")]
    free_gb = u.free / 1024 ** 3
    if free_gb < min_free_gb or u.free / u.total < 0.05:
        return [finding("BLOCK", "disk", f"only {free_gb:.1f} GB free: a long run that writes logs or artifacts can "
                                         "fill the disk", free_gb=round(free_gb, 1))]
    return [finding("OK", "disk", f"{free_gb:.1f} GB free", free_gb=round(free_gb, 1))]


def check_processes() -> List[Dict[str, Any]]:
    """Long-lived interpreters left running (possible orphans of an earlier run). Informational only."""
    try:
        if os.name == "nt":
            r = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True, timeout=20)
            names = [ln.split('","')[0].strip('"').lower() for ln in r.stdout.splitlines() if ln]
        else:
            r = subprocess.run(["ps", "-eo", "comm"], capture_output=True, text=True, timeout=20)
            names = [ln.strip().lower() for ln in r.stdout.splitlines()[1:]]
    except (OSError, subprocess.SubprocessError):
        return [finding("INFO", "processes", "process list not available on this system")]
    interp = [n for n in names if re.match(r"^(python|pythonw|node|pytest)(\d|\.exe|$)", n)]
    if len(interp) >= 8:
        return [finding("WARN", "processes", f"{len(interp)} python/node processes are running: check for orphans of a "
                                              "previous run before starting another one", count=len(interp))]
    return [finding("OK", "processes", f"{len(interp)} python/node processes running", count=len(interp))]


def run(repo: Path, min_free_gb: float = 5.0, big_mb: int = 50) -> Dict[str, Any]:
    findings = check_git(repo, big_mb) + check_disk(repo, min_free_gb) + check_processes()
    levels = {f["level"] for f in findings}
    verdict = "NO-GO" if "BLOCK" in levels else ("GO WITH WARNINGS" if "WARN" in levels else "GO")
    return {"repo": str(repo.resolve()), "verdict": verdict, "findings": findings}


def render(r: Dict[str, Any]) -> str:
    icon = {"BLOCK": "[BLOCK]", "WARN": "[WARN] ", "INFO": "[info] ", "OK": "[ok]   "}
    lines = [f"3am-safety preflight: {r['verdict']}  ({r['repo']})"]
    for f in sorted(r["findings"], key=lambda f: ["BLOCK", "WARN", "INFO", "OK"].index(f["level"])):
        where = f" — {f['file']}" + (f":{f['line']}" if f.get("line") else "") if f.get("file") else ""
        lines.append(f"  {icon[f['level']]} {f['check']}: {f['message']}{where}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min-free-gb", type=float, default=5.0)
    ap.add_argument("--big-file-mb", type=int, default=50)
    ap.add_argument("--secret-file", action="append", default=[],
                    help="extra file name to treat as a credentials file (repeatable)")
    a = ap.parse_args(argv)
    EXTRA_SECRET_FILES[:] = a.secret_file
    try:
        r = run(Path(a.repo), a.min_free_gb, a.big_file_mb)
    except Exception as exc:  # noqa: BLE001 - a broken preflight must say so, not pretend GO
        print(f"3am-safety preflight could not run: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3
    print(json.dumps(r, indent=1) if a.json else render(r))
    return {"GO": 0, "GO WITH WARNINGS": 1, "NO-GO": 2}[r["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
