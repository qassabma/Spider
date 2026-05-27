import csv
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SPIDERROCK_API_KEY")
BASE_URL = "https://mlink-live.nms.saturn.spiderrockconnect.com/rest/json"

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

GAMMA_PRIORITY = {
    "CRWV", "RDDT", "CVNA", "UPST", "AFRM", "IONQ", "SOUN", "QBTS", "RGTI",
    "QUBT", "ASTS", "APLD", "MARA", "RIOT", "HOOD", "SOFI", "RKLB",
    "ACHR", "WULF", "CLSK", "DJT", "GME", "AMC",
}

CRASH_PRIORITY = {"ARKK", "KRE", "XBI", "LCID", "RIVN", "NIO", "CVNA", "PLUG", "WOLF"}

MESSAGES = [
    "StockBookQuote",
    "StockPrint",
    "StockMarketSummary",
    "OptionNbboQuote",
    "OptionMarketSummary",
    "OptionPrint",
    "OptionPrintSet",
    "LiveImpliedQuoteAdj",
    "LiveSurfaceFixedTerm",
    "HistoricalVolatilities",
    "OptionOpenInterest",
]

DEFAULT_QUERY_SHAPE = {
    "cmd": "getmsgs",
    "msgtype": "{message}",
    "ticker": "{ticker}",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_name(value: str) -> str:
    return "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in value)


def to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        if isinstance(value, str):
            value = value.replace(",", "").replace("%", "").strip()
        return float(value)
    except Exception:
        return None


def flatten(obj: Any, prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            out.update(flatten(v, key))
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:10]):
            key = f"{prefix}.{i}" if prefix else str(i)
            out.update(flatten(v, key))
    else:
        out[prefix] = obj
    return out


def find_number(flat: Dict[str, Any], aliases: Iterable[str]) -> Optional[float]:
    alias_lowers = [a.lower() for a in aliases]
    items = list(flat.items())

    for key, value in items:
        k = key.lower().split(".")[-1]
        if k in alias_lowers:
            val = to_float(value)
            if val is not None:
                return val

    for key, value in items:
        kl = key.lower()
        for alias in alias_lowers:
            if kl.endswith(alias) or alias in kl:
                val = to_float(value)
                if val is not None:
                    return val
    return None


def find_text(flat: Dict[str, Any], aliases: Iterable[str]) -> str:
    alias_lowers = [a.lower() for a in aliases]
    for key, value in flat.items():
        k = key.lower().split(".")[-1]
        if k in alias_lowers and value is not None:
            return str(value)
    for key, value in flat.items():
        kl = key.lower()
        for alias in alias_lowers:
            if kl.endswith(alias) or alias in kl:
                return "" if value is None else str(value)
    return ""


class SpiderRockLiveClient:
    def __init__(self):
        if not API_KEY:
            raise RuntimeError("SPIDERROCK_API_KEY missing")
        self.api_key = API_KEY
        self.winners = self._load_phase1_winners()

    def _load_phase1_winners(self) -> Dict[str, Any]:
        path = Path("live_row_discovery_winners.json")
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def params_for(self, message: str, ticker: str) -> Dict[str, str]:
        if message in self.winners:
            params = dict(self.winners[message].get("params_without_key", {}))
            for k, v in list(params.items()):
                if isinstance(v, str):
                    if v.upper() in TICKERS:
                        params[k] = ticker
                    else:
                        params[k] = v.replace("{ticker}", ticker).replace("{message}", message)
            if "ticker" in params:
                params["ticker"] = ticker
            params["apikey"] = self.api_key
            return params

        params = {}
        for k, v in DEFAULT_QUERY_SHAPE.items():
            params[k] = v.replace("{message}", message).replace("{ticker}", ticker)
        params["apikey"] = self.api_key
        return params

    def query(self, message: str, ticker: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        params = self.params_for(message, ticker)
        public_params = {k: v for k, v in params.items() if k != "apikey"}
        result_meta: Dict[str, Any] = {
            "timestamp_utc": utc_now(),
            "ticker": ticker,
            "message": message,
            "params_without_key": public_params,
            "http_status": "",
            "error": "",
            "row_count": 0,
            "query_result": {},
        }

        try:
            r = requests.get(BASE_URL, params=params, timeout=25)
            result_meta["http_status"] = r.status_code
            r.raise_for_status()
            payload = r.json()

            rows: List[Dict[str, Any]] = []
            if isinstance(payload, list):
                for item in payload:
                    if not isinstance(item, dict):
                        continue
                    mtyp = item.get("header", {}).get("mTyp")
                    if mtyp == "QueryResult":
                        result_meta["query_result"] = item.get("message", {})
                    elif mtyp == message:
                        rows.append(item.get("message", {}))
                    elif mtyp and mtyp != "QueryResult":
                        rows.append(item.get("message", {}))
            elif isinstance(payload, dict):
                rows = [payload]

            result_meta["row_count"] = len(rows)
            preview_path = Path("phase3_raw_live") / f"{safe_name(ticker)}__{safe_name(message)}.json"
            preview_path.parent.mkdir(exist_ok=True)
            preview_path.write_text(json.dumps({
                "meta": result_meta,
                "row_preview": rows[:5],
            }, indent=2), encoding="utf-8")

            return rows, result_meta

        except Exception as exc:
            result_meta["error"] = str(exc)
            return [], result_meta


def first_flat(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {}
    return flatten(rows[0])


def derive_metrics(ticker: str, data: Dict[str, List[Dict[str, Any]]], metas: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    stock_quote = first_flat(data.get("StockBookQuote", []))
    stock_print = first_flat(data.get("StockPrint", []))
    stock_summary = first_flat(data.get("StockMarketSummary", []))
    option_nbbo = first_flat(data.get("OptionNbboQuote", []))
    option_summary = first_flat(data.get("OptionMarketSummary", []))
    option_print = first_flat(data.get("OptionPrint", []))
    option_printset = first_flat(data.get("OptionPrintSet", []))
    implied = first_flat(data.get("LiveImpliedQuoteAdj", []))
    surface = first_flat(data.get("LiveSurfaceFixedTerm", []))
    hv = first_flat(data.get("HistoricalVolatilities", []))
    oi = first_flat(data.get("OptionOpenInterest", []))

    stock_bid = find_number(stock_quote, ["bid", "bidPrc", "bidPrice", "bidPrice1", "bestBid"])
    stock_ask = find_number(stock_quote, ["ask", "askPrc", "askPrice", "askPrice1", "bestAsk"])
    stock_last = (
        find_number(stock_print, ["last", "lastPrc", "printPrc", "prtPrice", "price", "pLoc"])
        or find_number(stock_summary, ["last", "lastPrc", "close", "mark", "price"])
    )
    stock_volume = find_number(stock_summary, ["volume", "dayVolume", "cumVolume", "shares", "totVolume"])

    option_bid = find_number(option_nbbo, ["bid", "bidPrc", "bidPrice", "bidPrice1", "bestBid"])
    option_ask = find_number(option_nbbo, ["ask", "askPrc", "askPrice", "askPrice1", "bestAsk"])
    option_last = (
        find_number(option_print, ["last", "lastPrc", "printPrc", "prtPrice", "price"])
        or find_number(option_printset, ["last", "lastPrc", "printPrc", "prtPrice", "price"])
        or find_number(option_summary, ["last", "lastPrc", "mark", "price"])
    )
    option_volume = (
        find_number(option_summary, ["volume", "dayVolume", "cumVolume", "printVolume", "prtVolume"])
        or find_number(option_printset, ["volume", "prtVolume", "cumVolume"])
    )
    open_interest = find_number(oi, ["openInt", "openInterest", "oi"])

    iv = find_number(implied, ["iv", "iVol", "impliedVol", "vol", "years", "sVol", "surfaceVol"])
    delta = find_number(implied, ["delta"])
    gamma = find_number(implied, ["gamma"])
    theta = find_number(implied, ["theta"])
    vega = find_number(implied, ["vega"])

    surface_vol = find_number(surface, ["atmVol", "vol", "iVol", "surfaceVol", "fixedTermVol"])
    hist_vol = find_number(hv, ["hv", "histVol", "realizedVol", "vol", "hv20", "hv30", "hv60"])

    contract = (
        find_text(option_nbbo, ["okey", "optionKey", "symbol", "contract"])
        or find_text(implied, ["okey", "optionKey", "symbol", "contract"])
        or find_text(option_summary, ["okey", "optionKey", "symbol", "contract"])
    )

    stock_mid = None
    if stock_bid is not None and stock_ask is not None and stock_ask >= stock_bid:
        stock_mid = (stock_bid + stock_ask) / 2.0

    option_mid = None
    option_spread_pct = None
    if option_bid is not None and option_ask is not None and option_ask >= option_bid:
        option_mid = (option_bid + option_ask) / 2.0
        if option_mid and option_mid > 0:
            option_spread_pct = (option_ask - option_bid) / option_mid

    iv_vs_hv = None
    if iv is not None and hist_vol not in (None, 0):
        iv_vs_hv = iv / hist_vol

    iv_vs_surface = None
    if iv is not None and surface_vol not in (None, 0):
        iv_vs_surface = iv / surface_vol

    msg_ok = {f"{m}_rows": len(data.get(m, [])) for m in MESSAGES}

    return {
        "timestamp_utc": utc_now(),
        "ticker": ticker,
        "bucket": "GAMMA_PRIORITY" if ticker in GAMMA_PRIORITY else ("CRASH_PRIORITY" if ticker in CRASH_PRIORITY else "GENERAL"),
        "contract": contract,
        "stock_bid": stock_bid,
        "stock_ask": stock_ask,
        "stock_mid": stock_mid,
        "stock_last": stock_last,
        "stock_volume": stock_volume,
        "option_bid": option_bid,
        "option_ask": option_ask,
        "option_mid": option_mid,
        "option_spread_pct": option_spread_pct,
        "option_last": option_last,
        "option_volume": option_volume,
        "open_interest": open_interest,
        "iv": iv,
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega,
        "surface_vol": surface_vol,
        "historical_vol": hist_vol,
        "iv_vs_hv": iv_vs_hv,
        "iv_vs_surface": iv_vs_surface,
        **msg_ok,
    }


def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def liquidity_score(m: Dict[str, Any]) -> float:
    score = 0.0
    spread = m.get("option_spread_pct")
    oi = m.get("open_interest")
    vol = m.get("option_volume")

    if m.get("StockBookQuote_rows", 0) > 0:
        score += 15
    if m.get("OptionNbboQuote_rows", 0) > 0:
        score += 25
    if spread is not None:
        if spread <= 0.10:
            score += 25
        elif spread <= 0.20:
            score += 15
        elif spread <= 0.35 and m["bucket"] == "GAMMA_PRIORITY":
            score += 8
    if oi is not None:
        if oi >= 1000:
            score += 20
        elif oi >= 100:
            score += 12
    if vol is not None:
        if vol >= 1000:
            score += 15
        elif vol >= 100:
            score += 8

    return clamp(score)


def cheap_premium_score(m: Dict[str, Any]) -> float:
    score = 0.0
    if m.get("LiveImpliedQuoteAdj_rows", 0) > 0:
        score += 25
    if m.get("LiveSurfaceFixedTerm_rows", 0) > 0:
        score += 20
    if m.get("HistoricalVolatilities_rows", 0) > 0:
        score += 15

    iv_vs_surface = m.get("iv_vs_surface")
    iv_vs_hv = m.get("iv_vs_hv")

    if iv_vs_surface is not None:
        if iv_vs_surface <= 0.90:
            score += 25
        elif iv_vs_surface <= 1.05:
            score += 15
    if iv_vs_hv is not None:
        if iv_vs_hv <= 0.95:
            score += 15
        elif iv_vs_hv <= 1.15:
            score += 8

    return clamp(score)


def gamma_score(m: Dict[str, Any]) -> float:
    score = 0.0
    gamma = m.get("gamma")
    vega = m.get("vega")

    if m["bucket"] == "GAMMA_PRIORITY":
        score += 30
    if gamma is not None:
        score += clamp(abs(gamma) * 1000, 0, 35)
    if vega is not None and m.get("option_mid"):
        score += clamp((abs(vega) / max(float(m["option_mid"]), 0.01)) * 20, 0, 20)
    if m.get("OptionPrintSet_rows", 0) > 0:
        score += 15

    return clamp(score)


def data_quality_score(m: Dict[str, Any]) -> float:
    required = [
        "StockBookQuote_rows",
        "StockPrint_rows",
        "StockMarketSummary_rows",
        "OptionNbboQuote_rows",
        "OptionMarketSummary_rows",
        "LiveImpliedQuoteAdj_rows",
        "LiveSurfaceFixedTerm_rows",
        "HistoricalVolatilities_rows",
        "OptionOpenInterest_rows",
    ]
    ok = sum(1 for key in required if m.get(key, 0) > 0)
    return clamp((ok / len(required)) * 100)


def hard_gate_pass(m: Dict[str, Any]) -> bool:
    if m.get("StockBookQuote_rows", 0) <= 0:
        return False
    if m.get("OptionNbboQuote_rows", 0) <= 0:
        return False
    if m.get("LiveImpliedQuoteAdj_rows", 0) <= 0:
        return False
    if m.get("option_bid") is None or m.get("option_ask") is None:
        return False

    spread = m.get("option_spread_pct")
    if spread is None:
        return False

    max_spread = 0.35 if m["bucket"] == "GAMMA_PRIORITY" else 0.20
    if spread > max_spread:
        return False

    oi = m.get("open_interest")
    if oi is not None and oi < 50 and m["bucket"] != "GAMMA_PRIORITY":
        return False

    return True


def signal_row(m: Dict[str, Any], signal: str) -> Dict[str, Any]:
    lq = liquidity_score(m)
    cheap = cheap_premium_score(m)
    gam = gamma_score(m)
    dq = data_quality_score(m)

    if signal == "Cheap_Calls":
        directional_bonus = 10 if m["bucket"] == "GAMMA_PRIORITY" else 0
        score = 0.30 * lq + 0.30 * cheap + 0.25 * gam + 0.15 * dq + directional_bonus
        direction = "CALL"
    elif signal == "Cheap_Puts":
        directional_bonus = 15 if m["ticker"] in CRASH_PRIORITY else 0
        score = 0.35 * lq + 0.35 * cheap + 0.10 * gam + 0.20 * dq + directional_bonus
        direction = "PUT"
    elif signal == "Short_Stocks":
        directional_bonus = 20 if m["ticker"] in CRASH_PRIORITY else 0
        score = 0.30 * lq + 0.10 * cheap + 0.05 * gam + 0.35 * dq + directional_bonus
        direction = "SHORT/PUT"
    elif signal == "Airpockets":
        directional_bonus = 15 if m["ticker"] in CRASH_PRIORITY or m["bucket"] == "GAMMA_PRIORITY" else 0
        score = 0.25 * lq + 0.10 * cheap + 0.35 * gam + 0.20 * dq + directional_bonus
        direction = "PUT/FLUSH"
    else:
        score = 0.0
        direction = ""

    gate = hard_gate_pass(m)

    if not gate:
        status = "NO_TRADE_HARD_GATE_FAIL"
    elif score >= 90:
        status = "QUALIFIED"
    elif score >= 75:
        status = "SETUP"
    elif score >= 55:
        status = "WATCH"
    else:
        status = "NOISE"

    row = dict(m)
    row.update({
        "signal": signal,
        "direction": direction,
        "liquidity_score": round(lq, 2),
        "cheap_premium_score": round(cheap, 2),
        "gamma_score": round(gam, 2),
        "data_quality_score": round(dq, 2),
        "signal_score": round(clamp(score), 2),
        "hard_gate_pass": gate,
        "status": status,
    })
    return row


def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    fields: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fields:
                fields.append(key)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    client = SpiderRockLiveClient()
    raw_meta: List[Dict[str, Any]] = []
    metrics_rows: List[Dict[str, Any]] = []

    for ticker in TICKERS:
        per_message: Dict[str, List[Dict[str, Any]]] = {}
        metas: Dict[str, Dict[str, Any]] = {}

        for message in MESSAGES:
            rows, meta = client.query(message, ticker)
            per_message[message] = rows
            metas[message] = meta
            raw_meta.append(meta)
            time.sleep(0.05)

        metrics_rows.append(derive_metrics(ticker, per_message, metas))

    write_csv("Raw_Live_Metrics.csv", metrics_rows)
    write_csv("phase3_query_meta.csv", raw_meta)

    outputs = {
        "Cheap_Calls.csv": [signal_row(m, "Cheap_Calls") for m in metrics_rows],
        "Cheap_Puts.csv": [signal_row(m, "Cheap_Puts") for m in metrics_rows],
        "Short_Stocks.csv": [signal_row(m, "Short_Stocks") for m in metrics_rows],
        "Airpockets.csv": [signal_row(m, "Airpockets") for m in metrics_rows],
    }

    for filename, rows in outputs.items():
        write_csv(filename, rows)

    all_signal_rows = [row for rows in outputs.values() for row in rows]
    summary = {
        "timestamp_utc": utc_now(),
        "ticker_count": len(TICKERS),
        "raw_metric_rows": len(metrics_rows),
        "qualified_count": sum(1 for r in all_signal_rows if r["status"] == "QUALIFIED"),
        "setup_count": sum(1 for r in all_signal_rows if r["status"] == "SETUP"),
        "watch_count": sum(1 for r in all_signal_rows if r["status"] == "WATCH"),
        "hard_gate_pass_count": sum(1 for r in all_signal_rows if r["hard_gate_pass"]),
        "stop_condition": "PASS_PHASE3_REAL_SIGNAL_ENGINE_COMPLETE",
    }

    with open("phase3_signal_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
