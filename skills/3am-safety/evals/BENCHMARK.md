# 3am-safety — evaluation (skill-creator method)

Two realistic scenarios, run by independent agents (the same model in both runs) on fresh copies of repositories with known,
planted problems. Graded by a script (objective assertions, no eyeballing). Date: 2026-10-01.

| Scenario | Planted problems | v1.0 with skill | without skill | v1.1 with skill |
|---|---|---|---|---|
| overnight refactor | API key in an untracked file, `.env` not ignored, stale `index.lock`, uncommitted edit | **6/6** | 5/6 (missed the stale `index.lock`, which would make every commit of the night fail) | **9/9** |
| six-hour job (Italian prompt) | detached HEAD, uncommitted edit, never-committed notes file | 5/5 | 5/5 | **8/8** |

Every run: no secret value printed, repository left unmodified.

Honest reading:
- The skill's measurable gain on these scenarios is real but small: a strong model without the skill already
  finds most problems. What the skill adds is **consistency** (the same checklist every time, in ~1 s, with an
  exit code usable by automation) and the checks a model tends to skip (the stale git lock).
- v1.1 took its new advice (dedicated branch, explicit staging, backup, `.gitignore`, weak tests) from what the
  **baseline without the skill** did better in v1.0.
- The three assertions added in v1.1 (branch / staging / backup) passed for every run in v1.0 too: they are
  not discriminating (too loose) and are reported, not counted as a gain.
- Time: with skill 34–45 s, without 44–52 s (one run each: not a significant difference).
