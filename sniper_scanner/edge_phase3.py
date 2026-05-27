#!/usr/bin/env python3
"""Phase 3 signal engine — EDGE subset (fast)."""
from __future__ import annotations

import sys
from pathlib import Path

_PKG = Path(__file__).resolve().parent
_ROOT = _PKG.parent
for p in (str(_ROOT), str(_PKG)):
    if p not in sys.path:
        sys.path.insert(0, p)

import phase3_signal_engine as phase3  # noqa: E402

EDGE_TICKERS = [
    "SPY", "QQQ", "IWM", "VIX",
    "NVDA", "TSLA", "AAPL", "AMD", "META",
    "CRWV", "RDDT", "CVNA", "UPST", "IONQ", "SOUN", "QBTS", "RGTI",
    "GME", "MARA", "RIOT", "HOOD", "SOFI", "RKLB", "DJT",
]

EDGE_MESSAGES = [
    "LiveSurfaceFixedTerm",
    "HistoricalVolatilities",
    "LiveImpliedQuoteAdj",
    "OptionPrintSet",
    "OptionNbboQuote",
    "StockBookQuote",
]

phase3.TICKERS = EDGE_TICKERS
phase3.MESSAGES = EDGE_MESSAGES

if __name__ == "__main__":
    phase3.main()
