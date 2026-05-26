import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SNIPER_SPIDER_API_KEY")

# Placeholder imports for signal modules
from signals.cheap_calls import detect_cheap_calls
from signals.cheap_puts import detect_cheap_puts
from signals.short_stocks import detect_short_stocks
from signals.airpockets import detect_airpockets

def run():
    # Verify and print masked API key
    if not API_KEY:
        print("❌ API key not found! Exiting.")
        return
    print(f"👑 Sniper Scanner Starting - API loaded: {API_KEY[:4]}...")

    # Load tickers dynamically from tickers.txt
    try:
        with open("tickers.txt", "r") as file:
            tickers = [line.strip() for line in file.readlines()]
            print(f"✅ Loaded tickers: {tickers}")
    except FileNotFoundError:
        print("❌ tickers.txt not found! Exiting.")
        return

    # Run signal workflows with loaded tickers
    cheap_calls = detect_cheap_calls(tickers)
    cheap_puts = detect_cheap_puts(tickers)
    short_stocks = detect_short_stocks(tickers)
    airpockets = detect_airpockets(tickers)

    # Save results to reports
    save_to_report("Cheap_Calls.csv", cheap_calls)
    save_to_report("Cheap_Puts.csv", cheap_puts)
    save_to_report("Short_Stocks.csv", short_stocks)
    save_to_report("Airpockets.csv", airpockets)

    print("✅ All scans complete! Reports saved.")

def save_to_report(filename, data):
    import csv
    print(f"Saving {filename}...")
    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["ticker", "status"])
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ {filename} saved successfully!")

if __name__ == "__main__":
    run()