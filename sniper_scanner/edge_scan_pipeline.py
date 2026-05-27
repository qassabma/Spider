#!/usr/bin/env python3
"""Fast EDGE scan: 62-ticker universe + surface/flow messages."""
from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = Path(__file__).resolve().parent
for p in (str(ROOT), str(PKG)):
    if p not in sys.path:
        sys.path.insert(0, p)

from ticker_universe import ALL62_TICKERS, EDGE_MESSAGES, EDGE_TICKERS  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    os.chdir(ROOT)

    key = os.getenv("SPIDERROCK_API_KEY", "")
    if not key:
        print("ERROR: SPIDERROCK_API_KEY is not set in environment", file=sys.stderr, flush=True)
        return 1
    print(f"SPIDERROCK_API_KEY present (length={len(key)})", flush=True)

    print(
        json.dumps(
            {
                "mode": "EDGE_FAST",
                "ticker_universe": "ALL62",
                "tickers": len(EDGE_TICKERS),
                "messages": len(EDGE_MESSAGES),
                "api_calls": len(EDGE_TICKERS) * len(EDGE_MESSAGES),
                "cwd": str(Path.cwd()),
                "note": "62-name equity universe from tickers.txt (excludes macro/sector wrappers)",
            },
            indent=2,
        ),
        flush=True,
    )

    import phase3_signal_engine as phase3  # noqa: E402
    import phase4_rank_opportunities as phase4  # noqa: E402
    import phase5_execution_report as phase5  # noqa: E402

    phase3.TICKERS = list(EDGE_TICKERS)
    phase3.MESSAGES = list(EDGE_MESSAGES)

    steps = [
        ("EDGE_PHASE3", phase3.main),
        ("EDGE_PHASE4", phase4.main),
        ("EDGE_PHASE5", phase5.main),
    ]

    results: list[dict] = []
    failed = False

    for name, fn in steps:
        print(f"=== {name} ===", flush=True)
        try:
            fn()
            results.append({"name": name, "returncode": 0})
        except Exception as exc:
            failed = True
            traceback.print_exc()
            results.append({"name": name, "returncode": 1, "error": str(exc)})
            break

    summary = {
        "timestamp_utc": utc_now(),
        "mode": "EDGE_FAST",
        "ticker_universe": "ALL62",
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
