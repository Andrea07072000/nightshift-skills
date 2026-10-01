# Changelog

## 0.1.0 — 2026-10-01

- `3am-safety` 1.2.0: preflight before unattended runs (secrets, git lock, disk, uncommitted work, detached HEAD,
  orphan processes, remotes, missing `.gitignore`, single copy of the repo); `--secret-file` for private names.
- `honest-numbers` 1.1.0: finds unbacked claims in reports (percentages without denominator, status claims
  without evidence, absolute claims, vague or multiplier gains without a measurement).
- Publication gate `tools/check_skill.py` and CI on Linux, Windows and macOS.
