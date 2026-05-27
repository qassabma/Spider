"""Single source of truth for scan ticker universes."""
from __future__ import annotations

from pathlib import Path

# Macro / sector ETFs excluded from the Phase-2 "all-62" equity universe.
MACRO_EXCLUDE = {
    "SPX", "SPXW", "VIX", "GLD", "SLV", "SMH", "SOXL", "ARKK", "KRE", "XBI",
}

TICKERS_FILE = Path(__file__).resolve().parent.parent / "tickers.txt"


def load_tickers_file() -> list[str]:
    if not TICKERS_FILE.is_file():
        return []
    out: list[str] = []
    seen: set[str] = set()
    for line in TICKERS_FILE.read_text(encoding="utf-8").splitlines():
        sym = line.strip().upper()
        if sym and sym not in seen:
            seen.add(sym)
            out.append(sym)
    return out


FULL_UNIVERSE = load_tickers_file()

# 62-name equity universe: full list minus macro/sector wrappers.
ALL62_TICKERS = [t for t in FULL_UNIVERSE if t not in MACRO_EXCLUDE]

# Edge scan uses the full 62-name universe.
EDGE_TICKERS = ALL62_TICKERS

EDGE_MESSAGES = [
    "LiveSurfaceFixedTerm",
    "HistoricalVolatilities",
    "LiveImpliedQuoteAdj",
    "OptionPrintSet",
    "OptionNbboQuote",
    "StockBookQuote",
]
