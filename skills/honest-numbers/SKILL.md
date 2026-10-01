---
name: honest-numbers
description: Check a status report, PR description, release note, changelog, investor update or "here's what I did" summary for claims it does not back up — percentages with no denominator, "verified" or "production-ready" with no evidence, "all tests pass" with no command output, "much faster" with no measurement — and rewrite them so every number can be checked. Use it before sending or publishing any progress report, whenever an AI agent summarizes its own work, when someone asks "is this report accurate?", and especially when a report sounds too good.
version: 1.1.0
license: Apache-2.0
---

# honest-numbers

Reports written at the end of a long task drift toward the comfortable version: "85% complete", "fully
tested", "much faster". Each of those is a claim, and a reader can only trust it if the report says how it was
measured. This skill finds the unbacked claims and fixes them, so the report can survive someone checking it.

## 1. Find the unbacked claims

```bash
python <this-skill-dir>/scripts/check_report.py REPORT.md          # human summary
python <this-skill-dir>/scripts/check_report.py REPORT.md --json   # for automation
```

Read-only, standard library only. Exit code `1` means it found something, `0` means nothing obvious.

| Flag | What it catches | Why it matters |
|---|---|---|
| `PCT_NO_BASE` | `85%` with no `17/20`, `17 of 20` or `n=20` nearby | a percentage without a denominator cannot be checked or compared |
| `ABSOLUTE` | "100%", "never fails", "zero bugs", "guaranteed" | absolute claims are almost never measured; one counterexample breaks them |
| `STATUS_NO_EVID` | "verified", "tested", "done", "all tests pass" | with no command, count, commit or file, the reader has to take it on faith |
| `VAGUE_GAIN` | "much faster", "significantly better" | an improvement with no before/after number is an impression |

The script is a first pass: it catches the patterns, not the judgment. Read the report yourself too.

## 2. Fix each claim — do not delete the information, attach the evidence

| Instead of | Write |
|---|---|
| "85% complete" | "17 of 20 checklist items done (85%); missing: X, Y, Z" |
| "fully tested" | "`pytest` 142 passed, 0 failed (commit a1b2c3d); not covered: the export path" |
| "much faster" | "p50 latency 420 ms → 95 ms on the 1,000-request benchmark (same machine)" |
| "verified" | "verified by re-running `make e2e` on a clean clone; log in `artifacts/e2e.log`" |
| "zero bugs" | "no failing tests and no open issues labelled bug as of 2026-10-01" |

If the evidence does not exist, the honest fix is to say so: "not measured", "not tested on Windows",
"estimate". A report that says "unknown" in the right places is more useful than one that is confidently wrong.

## 3. Say what failed

A report with no failures in it is either for a trivial task or incomplete. Keep a short "what did not work /
what is still open" section. Failures are information: they tell the reader where to look and stop the next
person from repeating them.

## When not to use it

Marketing copy, fiction, or text where numbers are deliberately rhetorical. This skill is for reports that
someone will act on.
