import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ranked = ROOT / "Ranked_Opportunities.csv"
summary4 = ROOT / "phase4_ranking_summary.json"
summary3 = ROOT / "phase3_signal_summary.json"

rows = list(csv.DictReader(ranked.open(encoding="utf-8"))) if ranked.is_file() else []
s4 = json.loads(summary4.read_text()) if summary4.is_file() else {}
s3 = json.loads(summary3.read_text()) if summary3.is_file() else {}

print("=== EDGE SCAN REVIEW ===")
print(f"Source: {ranked}")
print(f"Phase3 tickers scanned: {s3.get('ticker_count', '?')}")
print(f"Ranked rows: {len(rows)}")
print(f"Status counts: {dict(Counter(r.get('final_status','') for r in rows))}")

# Best unique tickers (highest score per ticker, any signal type)
by_ticker: dict[str, dict] = {}
for r in rows:
    t = r.get("ticker", "")
    score = float(r.get("total_score") or 0)
    if t not in by_ticker or score > float(by_ticker[t].get("total_score") or 0):
        by_ticker[t] = r

best = sorted(by_ticker.values(), key=lambda x: float(x.get("total_score") or 0), reverse=True)

print("\n=== TOP 15 TICKERS (best score any lane) ===")
for r in best[:15]:
    print(
        f"{r.get('ticker',''):6} score={float(r.get('total_score') or 0):5.1f} "
        f"status={r.get('final_status',''):8} lane={r.get('signal',''):12} "
        f"stock={r.get('stock_last',''):>8} iv={r.get('surface_iv',''):>6} "
        f"vol={r.get('stock_volume',''):>8} group={r.get('priority_group','')}"
    )

print("\n=== SETUP rows (actionable watchlist) ===")
setups = [r for r in rows if r.get("final_status") == "SETUP"]
setups.sort(key=lambda x: float(x.get("total_score") or 0), reverse=True)
if not setups:
    print("None — no SETUP tier this run.")
else:
    for r in setups[:20]:
        print(
            f"{r.get('ticker',''):6} {r.get('signal',''):12} score={float(r.get('total_score') or 0):5.1f} "
            f"dir={r.get('direction',''):5} cheap={r.get('cheap_premium_score','')} "
            f"gamma={r.get('gamma_score','')} liq={r.get('liquidity_score','')}"
        )

print("\n=== FINAL SIGNAL / REVIEW ===")
final = [r for r in rows if r.get("final_status") in ("FINAL_SIGNAL", "FINAL_REVIEW", "QUALIFIED")]
print(f"Count: {len(final)}")
if not final:
    print("No FINAL_SIGNAL or QUALIFIED rows — scanner produced WATCH/SETUP only.")

# Data quality flag: duplicate stock_last across many tickers
lasts = Counter(r.get("stock_last", "") for r in rows if r.get("stock_last"))
if lasts and lasts.most_common(1)[0][1] > len(rows) * 0.3:
    val, cnt = lasts.most_common(1)[0]
    print(f"\n=== DATA QUALITY WARNING ===")
    print(f"stock_last={val} appears on {cnt}/{len(rows)} rows — likely default-query bleed.")
    print("Phase 1 live_row_discovery winners should be wired for per-ticker shapes.")

print("\n=== LANE BREAKDOWN (unique tickers) ===")
lanes = defaultdict(set)
for r in rows:
    if r.get("final_status") in ("SETUP", "WATCH", "QUALIFIED", "FINAL_REVIEW", "FINAL_SIGNAL"):
        lanes[r.get("signal", "")].add(r.get("ticker", ""))
for lane, tickers in sorted(lanes.items(), key=lambda x: -len(x[1])):
    print(f"  {lane}: {len(tickers)} tickers — {', '.join(sorted(tickers)[:12])}{'...' if len(tickers)>12 else ''}")
