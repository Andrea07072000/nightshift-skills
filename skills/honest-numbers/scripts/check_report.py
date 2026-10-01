#!/usr/bin/env python3
"""honest-numbers: find claims in a report that the report does not back up.

Read-only, standard library only. Works on Markdown or plain text.

    python check_report.py REPORT.md [--json]

Flags (each with line number and the exact text):
  PCT_NO_BASE     a percentage with no "x/y", "x of y" or "n=" nearby: 85% of what?
  ABSOLUTE        "100%", "always", "never fails", "zero bugs", "fully", "complete" without evidence nearby
  STATUS_NO_EVID  "verified", "tested", "production-ready", "done", "all tests pass" with no command, number,
                  commit, file or link on the same line or the next one
  VAGUE_GAIN      "much faster", "significantly better", "huge improvement" with no measured number
Exit codes: 0 nothing found · 1 findings · 2 could not read the file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List

BASE = re.compile(r"\b\d+\s*/\s*\d+\b|\b\d+\s+(?:of|su|out of|di)\s+\d+\b|\bn\s*=\s*\d+", re.I)
PCT = re.compile(r"(?<![\w.])(\d{1,3}(?:[.,]\d+)?)\s?%")
EVIDENCE = re.compile(r"`[^`]+`|\b[0-9a-f]{7,40}\b|https?://|\b\d+\s*(?:passed|failed|tests?|ms|s|cases?)\b|"
                      r"\b\w+\.(?:py|md|json|log|txt|csv|ts|js)\b|\b\d+\s*/\s*\d+\b", re.I)
STATUS = re.compile(r"\b(fully verified|verified|thoroughly tested|tested|production[- ]ready|battle[- ]tested|"
                    r"all tests pass(?:ed|ing)?|works perfectly|bug[- ]free|completed?|done)\b", re.I)
ABSOLUTE = re.compile(r"\b(100\s?%|always works|never fails|zero (?:bugs|errors|issues)|guaranteed|flawless|"
                      r"fully (?:secure|safe|working|automated))\b", re.I)
VAGUE = re.compile(r"\b(much (?:faster|better|more \w+)|significantly (?:faster|better|improved|\w+er)|"
                   r"huge(?:ly)? improve\w*|dramatically \w+|massive(?:ly)? \w+ (?:gain|improvement)|"
                   r"way (?:faster|better)|(?:dropped|fell|grew|rose|increased|decreased|improved|declined)"
                   r" (?:significantly|dramatically|sharply|substantially|a lot))\b", re.I)
#: "10x faster": a multiplier is a number, but without a before/after it is still an impression
MULTIPLIER = re.compile(r"\b\d+(?:[.,]\d+)?\s?[x×]\s+(?:faster|better|cheaper|more \w+|less \w+|fewer \w+)\b", re.I)
#: a measurement: a number with a unit, a before -> after, or a count of cases
MEASURED = re.compile(r"\d+(?:[.,]\d+)?\s?(?:ms|s|sec|seconds|min|minutes|h|hours|%|kb|mb|gb|users?|requests?|"
                      r"cases?|runs?|items?)\b|\d[\d,.]*\s*(?:->|→|to)\s*\d", re.I)
NUMBER = re.compile(r"\d")
TARGET = re.compile(r"\b(target|goal|objective|estimate|estimated|obiettivo|stima|stimat\w*|soglia|threshold)\b", re.I)


def check(text: str) -> List[Dict[str, object]]:
    lines = text.splitlines()
    out: List[Dict[str, object]] = []
    in_code = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        window = line                                            # the claim must carry its own evidence
        table_base = line.lstrip().startswith("|") and len(re.findall(r"(?<![\w.%])\d+(?![\w.%])", line)) >= 2
        declared = TARGET.search(line)                           # a target or a declared estimate is not a claim
        for m in PCT.finditer(line):
            if declared or re.search(r"[<>≤≥~]\s*$", line[:m.start()]):
                continue
            if m.group(0).replace(" ", "") == "100%" and ABSOLUTE.search(line):
                continue                                         # lo segnala ABSOLUTE
            if not BASE.search(window) and not table_base:
                out.append({"rule": "PCT_NO_BASE", "line": i + 1, "text": m.group(0),
                            "why": "a percentage with no numerator/denominator nearby: of what, measured how?"})
        for m in ABSOLUTE.finditer(line):
            if not (EVIDENCE.search(window) or BASE.search(window)):
                out.append({"rule": "ABSOLUTE", "line": i + 1, "text": m.group(0),
                            "why": "an absolute claim with no evidence next to it"})
        for m in STATUS.finditer(line):
            if m.group(0).isupper():
                continue                                         # VERIFIED, DONE... as labels in tables/enums
            if not (EVIDENCE.search(window) or BASE.search(window)):
                out.append({"rule": "STATUS_NO_EVID", "line": i + 1, "text": m.group(0),
                            "why": "a status claim with no command, count, commit, file or link to check it"})
        for m in MULTIPLIER.finditer(line):
            if not (MEASURED.search(window.replace(m.group(0), "")) or BASE.search(window)):
                out.append({"rule": "VAGUE_GAIN", "line": i + 1, "text": m.group(0),
                            "why": "a multiplier with no before/after measurement (from what, to what, measured how?)"})
        for m in VAGUE.finditer(line):
            if not (MEASURED.search(window) or BASE.search(window)):
                out.append({"rule": "VAGUE_GAIN", "line": i + 1, "text": m.group(0),
                            "why": "an improvement with no measured number (before, after, how)"})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="find unbacked claims in a report")
    ap.add_argument("report")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        text = Path(a.report).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"cannot read {a.report}: {exc}", file=sys.stderr)
        return 2
    found = check(text)
    if a.json:
        print(json.dumps(found, indent=1, ensure_ascii=False))
    else:
        print(f"honest-numbers: {len(found)} unbacked claim(s) in {a.report}")
        for f in found:
            print(f"  line {f['line']:>4}  {f['rule']:<15} {f['text']!r}: {f['why']}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
