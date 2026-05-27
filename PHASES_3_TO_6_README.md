# SpiderRock Phases 3–6

This bundle continues after:

- Phase 1: live row discovery
- Phase 2: all-ticker data health

## Phase 3 — Real Signal Engine

File:
- `sniper_scanner/phase3_signal_engine.py`

Workflow:
- `.github/workflows/phase3-real-signal-engine.yml`

Outputs:
- `Raw_Live_Metrics.csv`
- `Cheap_Calls.csv`
- `Cheap_Puts.csv`
- `Short_Stocks.csv`
- `Airpockets.csv`
- `phase3_signal_summary.json`

Stop condition:
- `PASS_PHASE3_REAL_SIGNAL_ENGINE_COMPLETE`

No random data is used.

## Phase 4 — Ranking

File:
- `sniper_scanner/phase4_rank_opportunities.py`

Workflow:
- `.github/workflows/phase4-rank-opportunities.yml`

Output:
- `Ranked_Opportunities.csv`

Status levels:
- `BLOCKED_HARD_GATE`
- `NOISE`
- `WATCH`
- `SETUP`
- `QUALIFIED`
- `FINAL_REVIEW`
- `FINAL_SIGNAL`

Massive opportunity override:
- Gamma-priority names get a boost only if hard gates pass.
- A row cannot become final if NBBO/IV hard gates fail.

## Phase 5 — Execution Report

File:
- `sniper_scanner/phase5_execution_report.py`

Workflow:
- `.github/workflows/phase5-execution-report.yml`

Outputs:
- `Final_Signals.md`
- `Final_Signals.csv`

Each report card includes:
- ticker
- signal
- direction
- contract
- entry limit
- targets
- stop
- bid/ask/mid
- IV/surface/HV
- Greeks
- OI
- option volume
- failure conditions

## Phase 6 — Full Pipeline (optional)

File:
- `sniper_scanner/phase6_full_pipeline.py`

Workflow:
- `.github/workflows/phase6-full-automation.yml`

Runs only when you start it manually (`workflow_dispatch`). No schedules, no push triggers.
Chains Phase 3 → 4 → 5 in one run if you choose to use it.

Output artifact:
- `phase6-full-automation`

## Operator control

Phases 1–6 workflows do not run on a schedule or on git push.
Each phase is your responsibility: run the scripts locally or trigger one workflow at a time in GitHub Actions after you have the inputs ready.

## Hard rule

This bundle generates scanner candidates and execution reports. It does not place brokerage orders.
