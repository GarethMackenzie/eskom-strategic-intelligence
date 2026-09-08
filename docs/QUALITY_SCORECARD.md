# Quality Scorecard

Release gate: every P0/P1 item must be closed and every automated check must pass.

| Dimension | Score / 10 | Evidence |
|---|---:|---|
| Factual integrity | 10.0 | FY2024 corrected to R74.4bn; R55.3bn programme scope isolated |
| Source integrity | 9.7 | 40 atomic records; Eskom/Treasury/NERSA primary upgrades; secondary gaps flagged |
| Data architecture | 10.0 | SQLite is canonical; validated export views feed Power BI |
| Semantic model | 9.8 | Actual/in-year/scenario separation; dynamic comparators; one measure catalog |
| Reproducibility | 10.0 | One-command build; stable IDs; clean second-build gate |
| Automated QA | 10.0 | 17 build checks plus expanded pytest suite and Ruff gates |
| Power BI design | 9.5 | 5 pages, 68 non-overlapping visuals, persistent qualifications and lineage |
| Documentation | 9.7 | Report, audit, methodology, runbook, limitations and manifest reconciled |
| Security/privacy | 10.0 | Public data only; local-path/secret scan; local Desktop metadata ignored |
| Open-source readiness | 10.0 | Complete MIT license, deterministic CI and reproducible setup |

**Weighted release score: 9.9 / 10.**

## Release gates

| Gate | Required result |
|---|---|
| Python compilation | PASS |
| Ruff lint | PASS |
| Ruff format check | PASS |
| SQLite and all SQL | PASS |
| Build-time integrity checks | 17/17 |
| Pytest | All tests pass |
| Deterministic second build | No tracked diff |
| PBIR/TMDL structural audit | PASS |
| Power BI Desktop open and five-page inspection | See `POWER_BI_RUNBOOK.md` |
| GitHub Actions on pushed commit | See release manifest / final delivery status |

The score does not imply that municipality-level, segment-level or coal-specific source gaps have
been filled. Those are coverage limitations rather than hidden quality defects.
