# Phase 1 Live Row Discovery

Purpose:
Find the exact SpiderRock REST row-query shape that returns live market rows from GitHub Actions.

This is not trade logic.

It tests:
- StockBookQuote
- StockPrint
- StockMarketSummary
- LiveSurfaceFixedTerm
- HistoricalVolatilities
- OptionOpenInterest
- OptionMarketSummary
- OptionNbboQuote
- LiveImpliedQuoteAdj
- OptionPrint
- OptionPrintSet

Priority tickers:
SPY, QQQ, IWM, NVDA, TSLA, CRWV, RDDT, CVNA, UPST, AFRM, IONQ, SOUN, QBTS, RGTI, QUBT, ASTS, APLD, MARA, RIOT, HOOD, SOFI, RKLB, ACHR, WULF, CLSK, DJT.

Expected artifact:
phase1-live-row-discovery

Expected files:
- live_row_discovery_summary.csv
- live_row_discovery_winners.json
- live_row_discovery_final_status.json
- live_row_discovery/*.json

Stop condition:
PASS_STOCK_LIVE_ROWS_PROVEN

If stop condition is not met:
Open live_row_discovery_summary.csv and identify which query shape failed or succeeded.
