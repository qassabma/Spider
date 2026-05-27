#!/usr/bin/env python3
"""Rotating SpiderRock scan: 1 endpoint × message batch × ALL62 tickers per 5-min run."""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
PKG = Path(__file__).resolve().parent
for p in (str(ROOT), str(PKG)):
    if p not in sys.path:
        sys.path.insert(0, p)

from spiderrock_catalog import (  # noqa: E402
    ALL58_MESSAGES,
    ENDPOINT_SHAPES,
    NUM_ENDPOINTS,
    TERMINAL15_MESSAGES,
    message_batch,
)
from ticker_universe import ALL62_TICKERS  # noqa: E402

BASE_URL = "https://mlink-live.nms.saturn.spiderrockconnect.com/rest/json"
MAX_WORKERS = int(os.getenv("ROTATING_SCAN_WORKERS", "8"))
REQUEST_TIMEOUT = float(os.getenv("ROTATING_SCAN_TIMEOUT", "25"))
REQUEST_DELAY = float(os.getenv("ROTATING_SCAN_DELAY", "0.05"))
SCAN_RUNS_DIR = ROOT / "scan_runs"
COUNTER_FILE = SCAN_RUNS_DIR / ".run_counter"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_index() -> int:
    env = os.getenv("GITHUB_RUN_NUMBER")
    if env and env.isdigit():
        return int(env)
    if COUNTER_FILE.is_file():
        try:
            return int(COUNTER_FILE.read_text(encoding="utf-8").strip())
        except ValueError:
            pass
    return 0


def bump_counter(current: int) -> None:
    SCAN_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    COUNTER_FILE.write_text(str(current + 1), encoding="utf-8")


def hydrate(shape: dict[str, str], message: str, ticker: str, api_key: str) -> dict[str, str]:
    params: dict[str, str] = {"apikey": api_key}
    for key, value in shape.items():
        params[key] = value.replace("{message}", message).replace("{ticker}", ticker)
    return params


def classify_payload(payload: Any, message: str) -> dict[str, Any]:
    if isinstance(payload, list):
        row_count = 0
        mtyps: list[str] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            header = item.get("header") or {}
            mtyp = header.get("mTyp")
            if mtyp:
                mtyps.append(str(mtyp))
            if mtyp == "QueryResult":
                continue
            if mtyp == message or (mtyp and mtyp != "QueryResult"):
                msg = item.get("message")
                if isinstance(msg, list):
                    row_count += len(msg)
                elif msg is not None:
                    row_count += 1
        return {"live_rows": row_count, "mtyps": mtyps[:5]}
    if isinstance(payload, dict):
        err = payload.get("error") or payload.get("message")
        return {"live_rows": 0, "error": str(err)[:200] if err else "unexpected dict"}
    return {"live_rows": 0, "error": "unexpected payload type"}


def query_one(
    shape: dict[str, str],
    message: str,
    ticker: str,
    api_key: str,
) -> dict[str, Any]:
    if REQUEST_DELAY > 0:
        time.sleep(REQUEST_DELAY)
    params = hydrate(shape, message, ticker, api_key)
    t0 = time.perf_counter()
    try:
        resp = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        if resp.status_code != 200:
            return {
                "ticker": ticker,
                "message": message,
                "http_status": resp.status_code,
                "http_ok": False,
                "live_rows": 0,
                "elapsed_ms": elapsed_ms,
                "error": resp.text[:120],
            }
        payload = resp.json()
        info = classify_payload(payload, message)
        return {
            "ticker": ticker,
            "message": message,
            "http_status": resp.status_code,
            "http_ok": True,
            "elapsed_ms": elapsed_ms,
            **info,
        }
    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "ticker": ticker,
            "message": message,
            "http_ok": False,
            "live_rows": 0,
            "elapsed_ms": elapsed_ms,
            "error": str(exc)[:200],
        }


def main() -> int:
    os.chdir(ROOT)
    api_key = os.getenv("SPIDERROCK_API_KEY", "")
    if not api_key:
        print("ERROR: SPIDERROCK_API_KEY is not set", file=sys.stderr, flush=True)
        return 1

    idx = run_index()
    endpoint_idx = idx % NUM_ENDPOINTS
    shape = ENDPOINT_SHAPES[endpoint_idx]
    tickers = list(ALL62_TICKERS)

    catalog_name = os.getenv("ROTATING_SCAN_CATALOG", "all58").lower()
    catalog = TERMINAL15_MESSAGES if catalog_name == "terminal15" else ALL58_MESSAGES
    batch_idx, messages = message_batch(idx, catalog)

    tasks = [(shape, msg, tkr) for msg in messages for tkr in tickers]
    total_calls = len(tasks)

    print(
        json.dumps(
            {
                "mode": "ROTATING_SCAN",
                "run_index": idx,
                "endpoint_index": endpoint_idx,
                "message_batch_index": batch_idx,
                "endpoint_shape": {k: v for k, v in shape.items() if k != "apikey"},
                "messages_this_run": messages,
                "catalog": catalog_name,
                "catalog_size": len(catalog),
                "tickers": len(tickers),
                "api_calls": total_calls,
                "workers": MAX_WORKERS,
                "coverage_note": f"18 runs cover all {len(catalog)} messages × {NUM_ENDPOINTS} endpoints",
                "timestamp_utc": utc_now(),
            },
            indent=2,
        ),
        flush=True,
    )

    started = time.perf_counter()
    results: list[dict[str, Any]] = []
    http_ok = 0
    live_hits = 0
    http_errors = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(query_one, s, m, t, api_key): (m, t)
            for s, m, t in tasks
        }
        done = 0
        for fut in as_completed(futures):
            row = fut.result()
            results.append(row)
            if row.get("http_ok"):
                http_ok += 1
                if row.get("live_rows", 0) > 0:
                    live_hits += 1
            else:
                http_errors += 1
            done += 1
            if done % 100 == 0 or done == total_calls:
                print(
                    f"progress {done}/{total_calls} http_ok={http_ok} live_hits={live_hits} http_errors={http_errors}",
                    flush=True,
                )

    elapsed_s = round(time.perf_counter() - started, 1)

    by_ticker: dict[str, int] = {}
    by_message: dict[str, int] = {}
    for r in results:
        rows = int(r.get("live_rows") or 0)
        if rows > 0:
            by_ticker[r["ticker"]] = by_ticker.get(r["ticker"], 0) + rows
            by_message[r["message"]] = by_message.get(r["message"], 0) + rows

    top_tickers = sorted(by_ticker.items(), key=lambda x: -x[1])[:10]
    top_messages = sorted(by_message.items(), key=lambda x: -x[1])[:10]

    sample_errors: list[dict[str, str]] = []
    for r in results:
        if not r.get("http_ok") and r.get("error"):
            sample_errors.append(
                {"ticker": r["ticker"], "message": r["message"], "error": r["error"][:80]}
            )
            if len(sample_errors) >= 5:
                break

    summary = {
        "timestamp_utc": utc_now(),
        "mode": "ROTATING_SCAN",
        "run_index": idx,
        "next_run_index": idx + 1,
        "endpoint_index": endpoint_idx,
        "next_endpoint_index": (idx + 1) % NUM_ENDPOINTS,
        "message_batch_index": batch_idx,
        "next_message_batch_index": (idx + 1) % NUM_ENDPOINTS,
        "messages_this_run": messages,
        "endpoint_shape": shape,
        "tickers_scanned": len(tickers),
        "messages_scanned": len(messages),
        "api_calls": total_calls,
        "http_ok": http_ok,
        "live_hits": live_hits,
        "http_errors": http_errors,
        "elapsed_seconds": elapsed_s,
        "top_live_tickers": [{"ticker": t, "rows": n} for t, n in top_tickers],
        "top_live_messages": [{"message": m, "rows": n} for m, n in top_messages],
        "sample_errors": sample_errors,
        "status": "OK" if http_ok > 0 else "DEGRADED",
    }

    SCAN_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = SCAN_RUNS_DIR / f"run_{stamp}_ep{endpoint_idx}_mb{batch_idx}.json"
    latest_path = SCAN_RUNS_DIR / "latest_summary.json"
    root_summary = ROOT / "rotating_scan_summary.json"

    run_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    latest_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    root_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    bump_counter(idx)

    print(json.dumps(summary, indent=2), flush=True)
    print(f"Wrote {run_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
