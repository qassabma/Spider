#!/usr/bin/env python3
"""Fast EDGE scan: focused tickers + surface/flow messages only (~2-5 min)."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Indices + gamma-priority names only — not the full 72-ticker harvest.
EDGE_TICKERS = [
    "SPY", "QQQ", "IWM", "VIX",
    "NVDA", "TSLA", "AAPL", "AMD", "META",
    "CRWV", "RDDT", "CVNA", "UPST", "IONQ", "SOUN", "QBTS", "RGTI",
    "GME", "MARA", "RIOT", "HOOD", "SOFI", "RKLB", "DJT",
]

# Surface + implied + flow — edge discovery messages, not full 11-type harvest.
EDGE_MESSAGES = [
    "LiveSurfaceFixedTerm",
    "HistoricalVolatilities",
    "LiveImpliedQuoteAdj",
    "OptionPrintSet",
    "OptionNbboQuote",
    "StockBookQuote",
]

STEPS = [
    ("EDGE_PHASE3", [sys.executable, "-u", "sniper_scanner/edge_phase3.py"]),
    ("EDGE_PHASE4", [sys.executable, "-u", "sniper_scanner/phase4_rank_opportunities.py"]),
    ("EDGE_PHASE5", [sys.executable, "-u", "sniper_scanner/phase5_execution_report.py"]),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_step(name: str, cmd: list[str]) -> dict:
    print(f"=== {name} ===", flush=True)
    proc = subprocess.run(cmd, text=True)
    return {"name": name, "cmd": cmd, "returncode": proc.returncode}


def main() -> int:
    print(
        json.dumps(
            {
                "mode": "EDGE_FAST",
                "tickers": len(EDGE_TICKERS),
                "messages": len(EDGE_MESSAGES),
                "api_calls": len(EDGE_TICKERS) * len(EDGE_MESSAGES),
                "note": "Focused edge scan — not full 792-call harvest",
            },
            indent=2,
        ),
        flush=True,
    )

    results = []
    failed = False
    for name, cmd in STEPS:
        result = run_step(name, cmd)
        results.append(result)
        if result["returncode"] != 0:
            failed = True
            break

    summary = {
        "timestamp_utc": utc_now(),
        "mode": "EDGE_FAST",
        "tickers": EDGE_TICKERS,
        "messages": EDGE_MESSAGES,
        "steps": results,
        "stop_condition": "PASS_EDGE_SCAN_COMPLETE" if not failed else "STOP_EDGE_SCAN_FAILED",
    }
    Path("edge_scan_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
