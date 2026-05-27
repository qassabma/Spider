#!/usr/bin/env python3
"""Phase 3 signal engine — EDGE subset (fast)."""
from __future__ import annotations

import sniper_scanner.phase3_signal_engine as phase3

# Override full harvest lists before main().
phase3.TICKERS = [
    "SPY", "QQQ", "IWM", "VIX",
    "NVDA", "TSLA", "AAPL", "AMD", "META",
    "CRWV", "RDDT", "CVNA", "UPST", "IONQ", "SOUN", "QBTS", "RGTI",
    "GME", "MARA", "RIOT", "HOOD", "SOFI", "RKLB", "DJT",
]
phase3.MESSAGES = [
    "LiveSurfaceFixedTerm",
    "HistoricalVolatilities",
    "LiveImpliedQuoteAdj",
    "OptionPrintSet",
    "OptionNbboQuote",
    "StockBookQuote",
]

if __name__ == "__main__":
    phase3.main()
