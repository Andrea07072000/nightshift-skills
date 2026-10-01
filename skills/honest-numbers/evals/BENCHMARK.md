# honest-numbers — evaluation (skill-creator method)

Scenario: an investor update with 8 planted unbacked claims ("85% complete and fully tested", "10x faster and
much more reliable", "all tests pass and production-ready", "zero bugs", "never fails", "churn dropped
significantly") and 2 honest lines (a feature count with its changelog, users before/after with source and dates).
Two independent agents (the same model in both runs) got the same request; one had the skill. Graded by script. Date: 2026-10-01.

| Measure | with skill (v1.0) | without skill |
|---|---|---|
| unbacked claims left in the corrected update (measured by `check_report.py`) | **0** | 4 |
| assertions passed | **7/8** | 6/8 |
| true facts kept (1,240 -> 1,610 users, 14 features) | yes | yes |
| invented figures | none (+370 / +29.8% are computed from the original) | none |

Script recall on the original update:

| version | planted claims found | honest lines flagged |
|---|---|---|
| v1.0 | 7 / 10 | 0 |
| v1.1 | **10 / 10** | 0 |

v1.1 added multiplier claims ("10x faster"), trend claims ("dropped significantly") and stopped letting any
nearby digit count as a measurement — all three gaps were reported by the agent that used v1.0.

Honest reading: a strong model without the skill already rewrites most claims well; the skill's measurable gain
is the final report being clean when checked (0 vs 4 unbacked claims left). One scenario, one run per
configuration: the gain is indicative, not statistically established. The "invented figures" check is noisy
(it flags arithmetic derived from the original), so it was judged by reading the outputs.
