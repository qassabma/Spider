# **Spider Sniper Scanner** 🕸️🎯

## **Overview**
Welcome to the **Spider Sniper Scanner**, a Python-powered framework for detecting **unparalleled market opportunities** using institutional-grade data. This scanner is designed for **kings** of the markets, identifying cheap options, high-potential short plays, and airpocket opportunities with unparalleled precision. 👑

---

## **Features**
### 🔍 **Signal Types**
1. **Cheap Calls**:
   - Identifies **bullish reversals** where implied volatility (IV) is **underpriced**.
   - Targets opportunities based on **flow dominance** and **Gamma ROI**.

2. **Cheap Puts**:
   - Detects **bearish setups** caused by **retail greed mispricing**.
   - Verifies signals through put-side IV skew dominance and institutional flow trends.

3. **Short Stock Candidates**:
   - Recognizes stocks in **distribution phases** based on VWAP failures and support break setups.
   - Prioritizes signals based on ask-side institutional dominance.

4. **Airpocket Candidates**:
   - Pinpoints stocks vulnerable to **downward collapses** due to demand exhaustion.
   - Validated using volume bursts, bid-flow analysis, and institutional volume shifts.

---

## **Key Spider Endpoints**
- **Volatility Screening**:
  - `LiveSurfaceFixedTerm`, `HistoricalVolatilities`
- **Flow Analysis**:
  - `OptionPrintSet`
- **Greeks and Pricing**:
  - `LiveImpliedQuoteAdj`, `OptionNbboQuote`
- **Volume Signals**:
  - `StockMarketSummary`, `StockPrint`, `StockMinuteBar`

---

## **Signal Workflow**
1. **Ticker Initialization**: Scan tickers for IV compression (≤ 0.8) and IV-HV spreads (≥ 5%).
2. **Contract Screening**: Filter options by bid/ask spreads (≤ 40%) and pricing edge (≥ 5%).
3. **Convex ROI Scoring**: Compute Gamma ROI for directional setups.
4. **Flow Confirmation**: Validate ask-side flow dominance (≥ 60%) and IV alignment.
5. **Shorts + Airpocket Analysis**: Analyze VWAP divergence, volume bursts, and flow collapses.

---

## **Output Example**
```csv
TICKER, STRIKE/SPOT, SIGNAL_TYPE, FLOW_EDGE, ROI_SCORE, LABEL
AAPL, 120C, Cheap_Call, 72%, 1.8, CONFIRMED
TSLA, 85P, Cheap_Put, 68%, 1.9, CONFIRMED
NVDA, --, Short_Stock, 63%, --, READY
META, --, Airpocket, 59%, --, CAUTION
```

---

## **Installation and Setup**
1. Clone the repository:
   ```bash
   git clone https://github.com/qassabma/Spider.git
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your **API Key**:
   - Add your API key to an `.env` file:
     ```
     SPIDER_API_KEY=your_api_key_here
     ```

4. Run the scanner:
   ```bash
   python sniper_scanner.py
   ```

---

## **Contributions**
Feel free to fork this repo and submit pull requests. 💥 Your input is always welcome to make this **Sniper Scanner** even sharper.

---

## **License**
This project is licensed under the **MIT License**.

---

### 👑 "Rule the Markets Like a King."
This GitHub repository is built for brilliance. Start sniping opportunities and leveraging Spider's power now! 🚀