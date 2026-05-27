import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_float(v: Any, default: float = 0.0) -> float:
    try:
        if v in ("", None):
            return default
        return float(v)
    except Exception:
        return default


def read_ranked() -> List[Dict[str, Any]]:
    path = Path("Ranked_Opportunities.csv")
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def entry_limit(row: Dict[str, Any]) -> str:
    bid = to_float(row.get("option_bid"), 0.0)
    ask = to_float(row.get("option_ask"), 0.0)
    mid = to_float(row.get("option_mid"), 0.0)

    if bid > 0 and ask > 0 and mid > 0:
        # Aggressive but controlled: avoid paying full ask unless spread is very tight.
        spread_pct = to_float(row.get("option_spread_pct"), 9.99)
        if spread_pct <= 0.10:
            limit = min(ask, mid + (ask - mid) * 0.50)
        else:
            limit = mid
        return f"{limit:.2f}"

    if ask > 0:
        return f"{ask:.2f}"

    return "NOT_AVAILABLE"


def target_stop(row: Dict[str, Any]) -> Dict[str, str]:
    limit = entry_limit(row)
    if limit == "NOT_AVAILABLE":
        return {
            "entry_limit": limit,
            "target_1": "NOT_AVAILABLE",
            "target_2": "NOT_AVAILABLE",
            "stop": "NOT_AVAILABLE",
        }

    px = to_float(limit)
    return {
        "entry_limit": f"{px:.2f}",
        "target_1": f"{px * 1.35:.2f}",
        "target_2": f"{px * 1.75:.2f}",
        "stop": f"{px * 0.65:.2f}",
    }


def card(row: Dict[str, Any], rank: int) -> str:
    levels = target_stop(row)
    contract = row.get("contract") or "TICKER_LEVEL_ONLY_CONTRACT_RESOLUTION_REQUIRED"

    return f"""
## #{rank} {row.get('ticker')} — {row.get('signal')} — {row.get('final_status')}

- Direction: {row.get('direction')}
- Total score: {row.get('total_score')}
- Contract: {contract}
- Entry limit: {levels['entry_limit']}
- Target 1: {levels['target_1']}
- Target 2: {levels['target_2']}
- Stop: {levels['stop']}
- Bid / Ask / Mid: {row.get('option_bid')} / {row.get('option_ask')} / {row.get('option_mid')}
- Spread %: {row.get('option_spread_pct')}
- IV: {row.get('iv')}
- Surface vol: {row.get('surface_vol')}
- Historical vol: {row.get('historical_vol')}
- Delta / Gamma / Theta / Vega: {row.get('delta')} / {row.get('gamma')} / {row.get('theta')} / {row.get('vega')}
- Open interest: {row.get('open_interest')}
- Option volume: {row.get('option_volume')}
- Bucket: {row.get('bucket')}
- Hard gate: {row.get('hard_gate_pass')}

Failure condition:
- Cancel if NBBO, IV/Greeks, or OI becomes unavailable.
- Cancel if spread expands beyond scanner threshold.
- Cancel if contract cannot be resolved from SpiderRock row data.
""".strip()


def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    fields: List[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ranked = read_ranked()
    executable = [
        r for r in ranked
        if r.get("final_status") in ("FINAL_SIGNAL", "FINAL_REVIEW", "QUALIFIED")
    ]

    executable = executable[:20]

    md = [
        "# Final Signals",
        "",
        f"Generated UTC: {utc_now()}",
        "",
        "This report produces scanner candidates only. It does not place brokerage orders.",
        "",
    ]

    if not executable:
        md.extend([
            "## No executable signals",
            "",
            "No rows passed final hard-gate and scoring requirements.",
        ])
    else:
        for idx, row in enumerate(executable, start=1):
            md.append(card(row, idx))
            md.append("")

    Path("Final_Signals.md").write_text("\n".join(md), encoding="utf-8")
    write_csv("Final_Signals.csv", executable)

    summary = {
        "timestamp_utc": utc_now(),
        "ranked_rows": len(ranked),
        "final_report_rows": len(executable),
        "stop_condition": "PASS_PHASE5_EXECUTION_REPORT_COMPLETE",
    }

    with open("phase5_execution_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
