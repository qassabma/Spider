import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SPIDERROCK_API_KEY")
BASE_URL = "https://mlink-live.nms.saturn.spiderrockconnect.com/rest/json"

TEST_TICKERS = [
    "SPY",
    "QQQ",
    "IWM",
    "NVDA",
    "TSLA",
    "CRWV",
    "RDDT",
    "CVNA",
    "UPST",
    "AFRM",
    "IONQ",
    "SOUN",
    "QBTS",
    "RGTI",
    "QUBT",
    "ASTS",
    "APLD",
    "MARA",
    "RIOT",
    "HOOD",
    "SOFI",
    "RKLB",
    "ACHR",
    "WULF",
    "CLSK",
    "DJT",
]

TEST_MESSAGES = [
    "StockBookQuote",
    "StockPrint",
    "StockMarketSummary",
    "LiveSurfaceFixedTerm",
    "HistoricalVolatilities",
    "OptionOpenInterest",
    "OptionMarketSummary",
    "OptionNbboQuote",
    "LiveImpliedQuoteAdj",
    "OptionPrint",
    "OptionPrintSet",
]

# These are discovery shapes, not trade logic.
# The first passing shape becomes the production row-query pattern.
QUERY_SHAPES = [
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}"},
    {"cmd": "getmsgs", "msgName": "{message}", "ticker": "{ticker}"},
    {"cmd": "getmsgs", "msg": "{message}", "ticker": "{ticker}"},
    {"cmd": "getmsgs", "mTyp": "{message}", "ticker": "{ticker}"},
    {"cmd": "select", "msgtype": "{message}", "ticker": "{ticker}"},
    {"cmd": "select", "msgName": "{message}", "ticker": "{ticker}"},
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_name(value: str) -> str:
    return "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in value)


def hydrate(shape: Dict[str, str], message: str, ticker: str) -> Dict[str, str]:
    params = {}
    for key, value in shape.items():
        params[key] = value.replace("{message}", message).replace("{ticker}", ticker)
    params["apikey"] = API_KEY
    return params


def classify_payload(payload: Any) -> Dict[str, Any]:
    if isinstance(payload, list):
        headers = []
        non_query_rows = 0
        query_result = None

        for item in payload:
            if not isinstance(item, dict):
                continue
            mtyp = item.get("header", {}).get("mTyp")
            if mtyp:
                headers.append(mtyp)
            if mtyp == "QueryResult":
                query_result = item.get("message", {})
            elif mtyp:
                non_query_rows += 1

        return {
            "json_type": "list",
            "row_count_total": len(payload),
            "non_query_rows": non_query_rows,
            "headers": ",".join(sorted(set(headers))),
            "query_result": query_result or {},
        }

    if isinstance(payload, dict):
        return {
            "json_type": "dict",
            "row_count_total": 1,
            "non_query_rows": 1 if payload else 0,
            "headers": "",
            "query_result": {},
        }

    return {
        "json_type": type(payload).__name__,
        "row_count_total": 0,
        "non_query_rows": 0,
        "headers": "",
        "query_result": {},
    }


def main() -> None:
    if not API_KEY:
        raise RuntimeError("SPIDERROCK_API_KEY missing")

    outdir = Path("live_row_discovery")
    outdir.mkdir(exist_ok=True)

    summary_rows: List[Dict[str, Any]] = []
    winners: Dict[str, Dict[str, Any]] = {}

    for message in TEST_MESSAGES:
        for ticker in TEST_TICKERS:
            if message in winners:
                break

            for idx, shape in enumerate(QUERY_SHAPES, start=1):
                params = hydrate(shape, message, ticker)
                public_params = {k: v for k, v in params.items() if k != "apikey"}

                started = utc_now()
                status = "UNKNOWN"
                error = ""
                response_text = ""
                http_status = None
                payload_info: Dict[str, Any] = {}

                try:
                    r = requests.get(BASE_URL, params=params, timeout=30)
                    http_status = r.status_code
                    response_text = r.text
                    r.raise_for_status()
                    payload = r.json()
                    payload_info = classify_payload(payload)

                    if payload_info.get("non_query_rows", 0) > 0:
                        status = "LIVE_ROWS_FOUND"
                        winners[message] = {
                            "message": message,
                            "ticker": ticker,
                            "shape_index": idx,
                            "params_without_key": public_params,
                            "payload_info": payload_info,
                        }
                    else:
                        status = "NO_LIVE_ROWS"

                except Exception as exc:
                    status = "ERROR"
                    error = str(exc)

                raw_path = outdir / f"{safe_name(message)}__{safe_name(ticker)}__shape_{idx}.json"
                with open(raw_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "timestamp_utc": started,
                            "message": message,
                            "ticker": ticker,
                            "shape_index": idx,
                            "params_without_key": public_params,
                            "http_status": http_status,
                            "status": status,
                            "error": error,
                            "payload_info": payload_info,
                            "response_preview": response_text[:2000],
                        },
                        f,
                        indent=2,
                    )

                summary_rows.append(
                    {
                        "timestamp_utc": started,
                        "message": message,
                        "ticker": ticker,
                        "shape_index": idx,
                        "cmd": public_params.get("cmd", ""),
                        "message_param": public_params.get("msgtype")
                        or public_params.get("msgName")
                        or public_params.get("msg")
                        or public_params.get("mTyp")
                        or "",
                        "http_status": http_status,
                        "status": status,
                        "non_query_rows": payload_info.get("non_query_rows", ""),
                        "row_count_total": payload_info.get("row_count_total", ""),
                        "headers": payload_info.get("headers", ""),
                        "error": error,
                        "raw_file": str(raw_path),
                    }
                )

                if status == "LIVE_ROWS_FOUND":
                    break

    with open("live_row_discovery_summary.csv", "w", newline="", encoding="utf-8") as f:
        fields = [
            "timestamp_utc",
            "message",
            "ticker",
            "shape_index",
            "cmd",
            "message_param",
            "http_status",
            "status",
            "non_query_rows",
            "row_count_total",
            "headers",
            "error",
            "raw_file",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary_rows)

    with open("live_row_discovery_winners.json", "w", encoding="utf-8") as f:
        json.dump(winners, f, indent=2)

    required_first_gate = ["StockBookQuote", "StockPrint", "StockMarketSummary"]
    first_gate_pass = all(m in winners for m in required_first_gate)

    final_status = {
        "timestamp_utc": utc_now(),
        "tested_messages": TEST_MESSAGES,
        "tested_tickers": TEST_TICKERS,
        "winner_count": len(winners),
        "winners": winners,
        "first_gate_required": required_first_gate,
        "first_gate_pass": first_gate_pass,
        "stop_condition": "PASS_STOCK_LIVE_ROWS_PROVEN" if first_gate_pass else "STOP_DISCOVERY_REVIEW_REQUIRED",
    }

    with open("live_row_discovery_final_status.json", "w", encoding="utf-8") as f:
        json.dump(final_status, f, indent=2)

    print(json.dumps(final_status, indent=2))

    if not first_gate_pass:
        raise RuntimeError("STOP_DISCOVERY_REVIEW_REQUIRED: stock live rows not fully proven")


if __name__ == "__main__":
    main()
