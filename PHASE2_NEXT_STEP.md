# Phase 2 All-62 Data Health

Purpose:
Scan all automatic candidate tickers and classify each as READY / PARTIAL / DEAD.

This is not final trade logic.

Input:
Full 62+ ticker universe, including gamma squeeze names.

Core output:
ticker_data_health.csv

Status logic:
- READY: core stock + option + IV/Greeks rows are live.
- PARTIAL: some data works, but not enough for automatic trade candidate.
- DEAD: no useful live rows.

Candidate permission:
- AUTO_CANDIDATE_ALLOWED
- WATCHLIST_PRIORITY_FIX_DATA
- WATCHLIST_FIX_DATA
- BLOCKED_DEAD_DATA

Stop condition:
PASS_ALL62_HEALTH_CLASSIFIED

Important:
If Phase 1 discovers a different query shape, update QUERY_SHAPE in sniper_scanner/spiderrock_phase2_data_health.py before running Phase 2.
