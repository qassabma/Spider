import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SPIDERROCK_API_KEY")
BASE_URL = "https://mlink-live.nms.saturn.spiderrockconnect.com/rest/json"

# Phase 2 scans the full automatic candidate universe.
TICKERS = [
    "SPY", "SPX", "SPXW", "QQQ", "IWM", "VIX",
    "NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "NFLX", "AMD", "AVGO",
    "PLTR", "SMCI", "COIN", "MSTR", "ARM", "SNOW", "CRWD", "PANW", "SHOP", "RBLX",
    "IONQ", "BBAI", "SOUN", "QBTS", "AI", "TEM", "HIMS", "APP", "CRWV", "RGTI",
    "QUBT", "ASTS", "APLD",
    "SMH", "SOXL", "GLD", "SLV",
    "GME", "AMC", "CVNA", "UPST", "AFRM", "CAVA", "RDDT",
    "RH", "TNGX", "DJT", "PLUG", "MARA", "RIOT", "HOOD", "SOFI", "RKLB",
    "ACHR", "JOBY", "WULF", "WOLF", "CLSK", "EOSE", "ONDS",
    "ARKK", "KRE", "XBI", "LCID", "RIVN", "NIO",
]

# Phase 2 uses the working shapes discovered in Phase 1.
# If Phase 1 discovered a different shape, edit QUERY_SHAPE only once here.
QUERY_SHAPE = {
    "cmd": "getmsgs",
    "msgtype": "{message}",
    "ticker": "{ticker}",
}

HEALTH_MESSAGES = {
    "stock_quote_ok": "StockBookQuote",
    "stock_print_ok": "StockPrint",
    "stock_summary_ok": "StockMarketSummary",
    "surface_ok": "LiveSurfaceFixedTerm",
    "hv_ok": "HistoricalVolatilities",
    "option_summary_ok": "OptionMarketSummary",
    "option_nbbo_ok": "OptionNbboQuote",
    "iv_greeks_ok": "LiveImpliedQuoteAdj",
    "oi_ok": "OptionOpenInterest",
    "option_printset_ok": "OptionPrintSet",
}

GAMMA_PRIORITY = {
    "CRWV", "RDDT", "CVNA", "UPST", "AFRM", "IONQ", "SOUN", "QBTS", "RGTI",
    "QUBT", "ASTS", "APLD", "MARA", "RIOT", "HOOD", "SOFI", "RKLB",
    "ACHR", "WULF", "CLSK", "DJT", "GME", "AMC",
}

CORE_LIQUIDITY = {"SPY", "QQQ", "IWM", "NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "META", "AMD"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def hydrate(message: str, ticker: str) -> Dict[str, str]:
    params = {}
    for key, value in QUERY_SHAPE.items():
        params[key] = value.replace("{message}", message).replace("{ticker}", ticker)
    params["apikey"] = API_KEY
    return params


def classify_payload(payload: Any) -> Tuple[bool, int, str, Dict[str, Any]]:
    if isinstance(payload, list):
        non_query = 0
        headers = []
        query_result = {}
        for item in payload:
            if not isinstance(item, dict):
                continue
            mtyp = item.get("header", {}).get("mTyp")
            if mtyp:
                headers.append(mtyp)
            if mtyp == "QueryResult":
                query_result = item.get("message", {})
            elif mtyp:
                non_query += 1
        return non_query > 0, non_query, ",".join(sorted(set(headers))), query_result

    if isinstance(payload, dict):
        return bool(payload), 1 if payload else 0, "", {}

    return False, 0, "", {}


def test_message(ticker: str, message: str, outdir: Path) -> Dict[str, Any]:
    params = hydrate(message, ticker)
    public_params = {k: v for k, v in params.items() if k != "apikey"}
    started = utc_now()

    result = {
        "timestamp_utc": started,
        "ticker": ticker,
        "message": message,
        "http_status": "",
        "ok": False,
        "non_query_rows": 0,
        "headers": "",
        "query_result": {},
        "error": "",
        "params_without_key": public_params,
    }

    try:
        r = requests.get(BASE_URL, params=params, timeout=25)
        result["http_status"] = r.status_code
        r.raise_for_status()
        payload = r.json()
        ok, non_query_rows, headers, query_result = classify_payload(payload)
        result["ok"] = ok
        result["non_query_rows"] = non_query_rows
        result["headers"] = headers
        result["query_result"] = query_result

        raw_file = outdir / f"{ticker}__{message}.json"
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp_utc": started,
                "ticker": ticker,
                "message": message,
                "params_without_key": public_params,
                "payload_preview": payload[:3] if isinstance(payload, list) else payload,
                "classification": result,
            }, f, indent=2)

    except Exception as exc:
        result["error"] = str(exc)

    return result


def classify_ticker(row: Dict[str, Any]) -> str:
    hard_core = [
        row["stock_quote_ok"],
        row["stock_print_ok"],
        row["stock_summary_ok"],
    ]
    option_core = [
        row["option_nbbo_ok"],
        row["option_summary_ok"],
        row["iv_greeks_ok"],
    ]

    if all(hard_core) and all(option_core):
        return "READY"

    if any(hard_core) or any(option_core) or row["surface_ok"] or row["hv_ok"] or row["oi_ok"]:
        return "PARTIAL"

    return "DEAD"


def main() -> None:
    if not API_KEY:
        raise RuntimeError("SPIDERROCK_API_KEY missing")

    outdir = Path("phase2_raw_health")
    outdir.mkdir(exist_ok=True)

    health_rows: List[Dict[str, Any]] = []
    raw_results: List[Dict[str, Any]] = []

    for ticker in TICKERS:
        checks = {}
        counts = {}
        errors = {}

        for col, message in HEALTH_MESSAGES.items():
            res = test_message(ticker, message, outdir)
            raw_results.append(res)
            checks[col] = bool(res["ok"])
            counts[col.replace("_ok", "_rows")] = res["non_query_rows"]
            if res["error"]:
                errors[message] = res["error"]

        row = {
            "timestamp_utc": utc_now(),
            "ticker": ticker,
            "bucket": "GAMMA_PRIORITY" if ticker in GAMMA_PRIORITY else ("CORE_LIQUIDITY" if ticker in CORE_LIQUIDITY else "GENERAL"),
            **checks,
            **counts,
            "ready_score": sum(1 for v in checks.values() if v),
            "status": "",
            "candidate_permission": "",
            "errors_json": json.dumps(errors, sort_keys=True),
        }

        row["status"] = classify_ticker(row)

        if row["status"] == "READY":
            row["candidate_permission"] = "AUTO_CANDIDATE_ALLOWED"
        elif row["status"] == "PARTIAL" and ticker in GAMMA_PRIORITY:
            row["candidate_permission"] = "WATCHLIST_PRIORITY_FIX_DATA"
        elif row["status"] == "PARTIAL":
            row["candidate_permission"] = "WATCHLIST_FIX_DATA"
        else:
            row["candidate_permission"] = "BLOCKED_DEAD_DATA"

        health_rows.append(row)

    fields = list(health_rows[0].keys())
    with open("ticker_data_health.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(health_rows)

    with open("phase2_raw_results.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, indent=2)

    summary = {
        "timestamp_utc": utc_now(),
        "ticker_count": len(TICKERS),
        "ready_count": sum(1 for r in health_rows if r["status"] == "READY"),
        "partial_count": sum(1 for r in health_rows if r["status"] == "PARTIAL"),
        "dead_count": sum(1 for r in health_rows if r["status"] == "DEAD"),
        "gamma_priority_ready": [r["ticker"] for r in health_rows if r["bucket"] == "GAMMA_PRIORITY" and r["status"] == "READY"],
        "gamma_priority_partial": [r["ticker"] for r in health_rows if r["bucket"] == "GAMMA_PRIORITY" and r["status"] == "PARTIAL"],
        "stop_condition": "PASS_ALL62_HEALTH_CLASSIFIED",
    }

    with open("phase2_health_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
