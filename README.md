# nightshift-skills

**Skills for AI coding agents that work while you sleep — each one benchmarked with and without the skill.**

Drop a folder into Claude Code (or any agent that reads `SKILL.md`) and it gets better at the boring, high-stakes
parts of autonomous work: checking it is safe to run unattended, and reporting what it did without inflating it.

No installs, no API keys, no network: every script uses only the Python standard library.

---

## The skills

| Skill | What it does | Measured effect (see `evals/BENCHMARK.md`) |
|---|---|---|
| [**3am-safety**](skills/3am-safety) | Preflight before you leave an agent running overnight: secrets about to be committed, a stuck git lock, a disk about to fill, uncommitted work, detached HEAD, orphan processes, pushes that would publish. Clear **GO / GO WITH WARNINGS / NO-GO** in ~1 second. | Found a stale `git index.lock` the agent without the skill missed (it would have made every overnight commit fail): 11/11 vs 10/11 on two planted-problem repos. |
| [**honest-numbers**](skills/honest-numbers) | Checks a status report, PR description or investor update for claims it does not back up — `85%` of what?, "fully tested" with no test run, "10x faster" with no benchmark — and rewrites them so every number can be checked. | Corrected report left with **0** unbacked claims vs **4** without the skill; the script finds 10/10 planted claims and flags none of the honest lines. |

More are on the way. Every skill here ships with its benchmark, or it does not ship.

## Install (30 seconds)

```bash
git clone https://github.com/Andrea07072000/nightshift-skills.git
# for every project:
cp -r nightshift-skills/skills/3am-safety ~/.claude/skills/
# or only for one project:
cp -r nightshift-skills/skills/honest-numbers your-project/.claude/skills/
```

On Windows, copy the folders to `%USERPROFILE%\.claude\skills\`. Restart Claude Code and the skills are picked up
automatically: you do not need to call them by name — the description tells the agent when to use each one.

You can also run the scripts directly, no agent needed:

```bash
python skills/3am-safety/scripts/preflight.py path/to/repo
python skills/honest-numbers/scripts/check_report.py STATUS.md
```

## Why "benchmarked with and without"?

Anyone can write a `SKILL.md` that *looks* useful. The question that matters is: **does the agent do better with
it than without it?** For every skill here, two independent agents get the same realistic task — one with the
skill, one without — on fixtures with known, planted problems, and a script grades both. The numbers, including
where the skill did *not* help, are in each skill's `evals/BENCHMARK.md`.

That also keeps the skills honest about their limits: a strong model without a skill is already good at a lot of
this. The skills earn their place on consistency, on the checks models tend to skip, and on output you can verify.

## Repository layout

```
skills/<name>/SKILL.md          instructions + when to use (what the agent reads)
skills/<name>/scripts/          deterministic helpers (standard library only)
skills/<name>/evals/BENCHMARK.md  with/without comparison, raw numbers, limits
tests/test_<name>.py            tests for the scripts (pytest)
tools/check_skill.py            the publication gate every skill must pass
```

## Contributing

Ideas, bug reports and new skills are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). The one hard rule: a new
skill comes with a benchmark against the same task without it.

## Also from this author

[**S.T.A.R.**](https://github.com/Andrea07072000/S.T.A.R.-) — reproducible, tested building blocks for space and
flight software (time scales, leap seconds, verification).

## License

Apache-2.0. See [LICENSE](LICENSE).
