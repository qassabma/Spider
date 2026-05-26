def detect_short_stocks(tickers):
    print("🔍 Detecting Short Stocks...")
    results = []
    for ticker in tickers:
        print(f"Analyzing {ticker} for short stocks...")
        results.append({"ticker": ticker, "status": "placeholder_scan"})
    return results