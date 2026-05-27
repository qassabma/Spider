import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

INPUT_FILES = ["Cheap_Calls.csv", "Cheap_Puts.csv", "Short_Stocks.csv", "Airpockets.csv"]

GAMMA_PRIORITY = {
    "CRWV", "RDDT", "CVNA", "UPST", "AFRM", "IONQ", "SOUN", "QBTS", "RGTI",
    "QUBT", "ASTS", "APLD", "MARA", "RIOT", "HOOD", "SOFI", "RKLB",
    "ACHR", "WULF", "CLSK", "DJT", "GME", "AMC",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_float(v: Any, default: float = 0.0) -> float:
    try:
        if v in ("", None):
            return default
        return float(v)
    except Exception:
        return default


def to_bool(v: Any) -> bool:
    return str(v).lower() in ("true", "1", "yes")


def read_csv(path: str) -> List[Dict[str, Any]]:
    if not Path(path).exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compute_total(row: Dict[str, Any]) -> Dict[str, Any]:
    liquidity = to_float(row.get("liquidity_score"))
    cheap = to_float(row.get("cheap_premium_score"))
    gamma = to_float(row.get("gamma_score"))
    quality = to_float(row.get("data_quality_score"))
    base = to_float(row.get("signal_score"))

    squeeze_boost = 0.0
    if row.get("ticker") in GAMMA_PRIORITY:
        if gamma >= 70:
            squeeze_boost += 8
        elif gamma >= 50:
            squeeze_boost += 5

    massive_opportunity_boost = 0.0
    if liquidity >= 75 and gamma >= 75 and quality >= 75:
        massive_opportunity_boost += 7
    if cheap >= 80 and liquidity >= 70:
        massive_opportunity_boost += 5

    total = min(100.0, base + squeeze_boost + massive_opportunity_boost)
    hard_gate = to_bool(row.get("hard_gate_pass"))

    if not hard_gate:
        final_status = "BLOCKED_HARD_GATE"
    elif total >= 98:
        final_status = "FINAL_SIGNAL"
    elif total >= 95:
        final_status = "FINAL_REVIEW"
    elif total >= 85:
        final_status = "QUALIFIED"
    elif total >= 70:
        final_status = "SETUP"
    elif total >= 35:
        final_status = "WATCH"
    else:
        final_status = "NOISE"

    row["squeeze_boost"] = round(squeeze_boost, 2)
    row["massive_opportunity_boost"] = round(massive_opportunity_boost, 2)
    row["total_score"] = round(total, 2)
    row["final_status"] = final_status
    return row


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
    rows: List[Dict[str, Any]] = []
    for file in INPUT_FILES:
        for row in read_csv(file):
            row["source_file"] = file
            rows.append(compute_total(row))

    rows.sort(key=lambda r: to_float(r.get("total_score")), reverse=True)
    write_csv("Ranked_Opportunities.csv", rows)

    summary = {
        "timestamp_utc": utc_now(),
        "row_count": len(rows),
        "final_signal_count": sum(1 for r in rows if r.get("final_status") == "FINAL_SIGNAL"),
        "final_review_count": sum(1 for r in rows if r.get("final_status") == "FINAL_REVIEW"),
        "qualified_count": sum(1 for r in rows if r.get("final_status") == "QUALIFIED"),
        "setup_count": sum(1 for r in rows if r.get("final_status") == "SETUP"),
        "watch_count": sum(1 for r in rows if r.get("final_status") == "WATCH"),
        "blocked_count": sum(1 for r in rows if r.get("final_status") == "BLOCKED_HARD_GATE"),
        "stop_condition": "PASS_PHASE4_RANKING_COMPLETE",
    }

    with open("phase4_ranking_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
