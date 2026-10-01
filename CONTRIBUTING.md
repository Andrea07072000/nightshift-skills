# Contributing

Thanks for helping. Bug reports, benchmark results from your own setup, and new skills are all useful.

## Reporting a problem

Open an issue with: the skill and its version, what you asked the agent, what happened, what you expected.
If a script misbehaves, the exact command and its output help the most.

## Proposing a new skill

A skill belongs here if it makes an agent measurably better at a recurring, real task. Before opening a pull
request:

1. **One folder per skill**: `skills/<name>/SKILL.md` with frontmatter `name` (= folder name), `description`
   (what it does **and** when to use it), `version`, `license` (OSI-approved).
2. **Scripts use only the Python standard library** and are read-only unless the skill's purpose requires
   writing (say so in the SKILL.md).
3. **Tests**: `tests/test_<name>.py` covering the scripts, including the cases that must *not* be flagged.
4. **Benchmark**: `skills/<name>/evals/BENCHMARK.md` comparing the same task done with and without the skill —
   fixtures, how it was graded, the raw numbers and where it did not help.
5. Run the gate and the tests:

   ```bash
   python tools/check_skill.py --all
   python -m pytest -q tests
   ```

## What will not be merged

Skills that run downloaded code (`curl ... | sh`), ask for broad permissions, contain secrets or personal
paths, or have no benchmark. "It feels better" is not a benchmark.
