# Holy Grail Options Scanner (SpiderRock API Integration)

## Overview
The **Holy Grail Options Scanner** is a Python-based utility designed to identify **high ROI (100%–500%) opportunities** in the options market using **institutional-grade SpiderRock precomputed data**. This tool dynamically scans and ranks cheap puts and calls by analyzing:
- **Implied Volatility Compression**
- **Theta Decay and Liquidity Filtering**
- **Skew and Term Structure**

Leverage this scanner if you're seeking to identify asymmetric trade setups that maximize returns while minimizing risks.

---

## Key Features
- **SpiderRock API Integration**:
  Accesses 18 precomputed SpiderRock endpoints for real-time options insights.
- **Dynamic Signal Scoring**:
  Ranks contracts using configurable triggers based on your preferences.
- **Customizable Alerts**:
  Tweak frequency and conditions to control signal tightness or throughput.
- **Exportable Results**:
  Outputs signals in **CSV format** for review or trading workflows.

---

## Signal Logic
The scanner dynamically ranks options based on the following key criteria:
- **Premium Range**: $0.20 ≤ `ask` ≤ $1.00 for affordable options.
- **IV Compression**: `iv_mid` < 60% of historical IV (`iv_hist`) to prioritize undervalued contracts.
- **Liquidity**: Open Interest ≥ 500 and Bid/Ask Spread ≤ $0.20 to ensure tradeability.
- **Theta Decay**: Excludes contracts bleeding over 5% premium/day due to time decay.
- **Delta Range**: Targets close-to-ATM and near-OTM strikes (Delta 0.4–0.7) for moves with leverage.
- **Skew Filtering**: Favors positive or flat skew for higher upside potential.

All logic is configurable in the `CONFIG` block within the script.

---

## Quickstart

### Prerequisites
1. **Python 3.7 or higher installed**.
2. **SpiderRock API Access**:
   - Obtain your API access and token from SpiderRock.
3. Add your **SpiderRock API Token** to the script:
   - Update this placeholder or use an environment variable:
     ```python
     API_TOKEN = os.getenv("SPIDERROCK_API_TOKEN")
     ```

---

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/holy-grail-scanner.git
   cd holy-grail-scanner# Spider
GitHub Action 🕷️🕷️
