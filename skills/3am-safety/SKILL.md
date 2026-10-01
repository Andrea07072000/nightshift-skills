---
name: 3am-safety
description: Preflight check before leaving an AI agent (or any long job) running unattended on a repository — overnight runs, multi-hour autonomous sessions, scheduled jobs, loops, "work on your own for a few hours". Finds what would explode at 3 AM with nobody watching: uncommitted work, secrets about to be committed, a stuck git lock, a disk about to fill up, huge files headed for the history, orphan processes, and pushes that would publish. Use it whenever someone is about to start an unattended or long-running task, asks "is it safe to leave this running", schedules a recurring job, or hands over autonomy for hours — even if they do not say "safety".
version: 1.2.0
license: Apache-2.0
---

# 3am-safety

An unattended run fails differently from an attended one: nobody notices the first wrong step, so it
compounds for hours. Most of those failures are visible *before* the run starts. This skill checks them in
seconds and turns them into a clear GO / GO WITH WARNINGS / NO-GO.

## Run the preflight

```bash
python <this-skill-dir>/scripts/preflight.py <repo-path>          # human summary
python <this-skill-dir>/scripts/preflight.py <repo-path> --json   # for automation
```

Add `--secret-file NAME` (repeatable) for credentials files with a private name of your own.

It is read-only, uses only the Python standard library, and never prints a secret value (only the file,
the line and the kind of secret). Exit codes: `0` GO, `1` GO WITH WARNINGS, `2` NO-GO, `3` the checks could not
run (treat as NO-GO: a broken check is not a passed check).

| Check | Why it matters at 3 AM |
|---|---|
| uncommitted changes | the run cannot be rolled back to a known state |
| credentials file or secret in a file git would commit | an automatic commit or push leaks it |
| `index.lock` | every git step of the run will fail |
| detached HEAD | overnight commits become hard to find |
| large untracked files | an automatic `git add -A` bloats the history permanently |
| low disk space | logs and artifacts fill the disk; everything after that fails |
| many python/node processes | orphans of an earlier run compete for files and ports |
| remotes configured | an unattended `git push` publishes; decide in advance whether it is allowed |

## Then decide

- **NO-GO**: fix every `[BLOCK]` before starting. Do not "start anyway and see": the point is that nobody will
  be there to see. Move secrets out of the repository (or into `.gitignore`), remove the stale lock only after
  checking no git process is running, free disk space.
- **GO WITH WARNINGS**: either fix the warnings or state explicitly, in the plan for the run, why each one is
  acceptable (for example "uncommitted changes are the work in progress; first step is a WIP commit").
- **GO**: still write down the boundaries of the run before starting.

## Boundaries every unattended run should state up front

Write these in the task description or the plan, so the agent (and the person reading the log tomorrow) knows
them:

1. **Stop condition**: a time limit or a number of iterations, never "until done".
2. **Its own branch**: the run commits on a dedicated branch (`git switch -c night-<date>`), never on `main`, so
   tomorrow its work can be reviewed, kept or dropped as a whole.
3. **Explicit staging**: commit the files the task is about by name; never `git add -A` / `git add .`, which sweeps
   up notes, caches, secrets and other people's work in progress.
4. **No irreversible steps without a gate**: no `git push --force`, no `git clean`, no deleting data, no
   publishing, no spending money, no sending messages.
5. **Commit cadence**: small commits at checkpoints, so a failure loses minutes, not hours.
6. **A backup exists**: a remote or a `git bundle` taken before the run.
7. **Where the log goes**, and that the log must report failures as failures.
8. **Process hygiene**: background processes started by the run are stopped at the end (check for orphans).
9. **Tests that can fail**: if the "verification" is one trivial test, running it for hours proves nothing;
   strengthen it first or say so.

## What it does not do

It does not sandbox anything and does not judge whether the task itself is a good idea. It catches the
predictable, mechanical ways an unattended run goes wrong. Combine it with your normal review of what the
run will actually do.
