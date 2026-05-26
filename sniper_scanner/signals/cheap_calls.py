import random

def detect_cheap_calls(tickers):
    print("🔍 Detecting Cheap Calls...")
    results = []

    for ticker in tickers:
        print(f"Analyzing {ticker} for cheap calls...")

        # Example logic using placeholder market data (replace with actual API calls)
        iv = random.uniform(0.1, 0.5)  # Simulated Implied Volatility
        spread = random.uniform(0.01, 0.1)  # Simulated Bid-Ask Spread
        volume = random.randint(50000, 200000)  # Simulated Volume

        # Filtering logic
        if iv < 0.25 and spread < 0.05 and volume > 100000:
            results.append({"ticker": ticker, "status": "cheap_call_pass"})
            print(f"✅ {ticker} PASSED: IV={iv:.2f}, Spread={spread:.2f}, Volume={volume}")
        else:
            results.append({"ticker": ticker, "status": "cheap_call_fail"})
            print(f"❌ {ticker} FAILED: IV={iv:.2f}, Spread={spread:.2f}, Volume={volume}")

    return results