"""SpiderRock message inventory (58 mTyp) and 18 REST endpoint query shapes."""
from __future__ import annotations

import math

# Verified from SPIDERROCK_MESSAGE_INVENTORY.csv (58 unique mTyp).
ALL58_MESSAGES: list[str] = [
    "AggregateCount",
    "AggregateNumeric",
    "AggregateString",
    "BucketRange",
    "EquityCorpActionRecordV5",
    "GlobalRates",
    "HistoricalVolatilities",
    "LiveAtmVol",
    "LiveImpliedQuote",
    "LiveImpliedQuoteAdj",
    "LiveImpliedQuoteDisp",
    "LiveSurfaceAtm",
    "LiveSurfaceCurve",
    "LiveSurfaceFixedGrid",
    "LiveSurfaceFixedTerm",
    "MLinkAdmin",
    "MLinkCount",
    "MLinkDataAck",
    "MLinkHeartbeat",
    "MLinkLogon",
    "MLinkSignalReady",
    "MLinkStream",
    "MLinkStreamAck",
    "MLinkStreamCheckPt",
    "MLinkSubscribe",
    "MLinkSubscribeAck",
    "MLinkSubscribeCheckPt",
    "MLinkTheoModel",
    "MsgExpiryKey",
    "MsgOptionKey",
    "MsgTickerKey",
    "OddLotBookQuote",
    "OpraPrintType",
    "OptExpiryDefinition",
    "OptionAtmMinuteBarSet",
    "OptionCloseMark",
    "OptionCorpActionRecordAdjV5",
    "OptionCorpActionRecordV5",
    "OptionMarketSummary",
    "OptionNbboQuote",
    "OptionOpenInterest",
    "OptionOpenMark",
    "OptionPrint",
    "OptionPrintSet",
    "OptionRiskFactor",
    "PostAck",
    "RootDefinition",
    "StockBeta",
    "StockBookQuote",
    "StockCloseMark",
    "StockMarketSummary",
    "StockMinuteBar",
    "StockOpenMark",
    "StockPrint",
    "TickerDefinition",
    "TickerItemDef",
    "UserApiKey",
    "UserMetaData",
]

# Tradeable subset (terminal_monitor_usable=YES in inventory).
TERMINAL15_MESSAGES: list[str] = [
    "HistoricalVolatilities",
    "LiveImpliedQuoteAdj",
    "LiveSurfaceAtm",
    "LiveSurfaceCurve",
    "LiveSurfaceFixedGrid",
    "LiveSurfaceFixedTerm",
    "OptionMarketSummary",
    "OptionNbboQuote",
    "OptionOpenInterest",
    "OptionPrint",
    "OptionPrintSet",
    "StockBookQuote",
    "StockMarketSummary",
    "StockMinuteBar",
    "StockPrint",
]

# 18 endpoint shapes — all use proven getmsgs+msgtype (phase3 default).
# Extra params are harmless query modifiers on the same REST path.
ENDPOINT_SHAPES: list[dict[str, str]] = [
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "limit": "50"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "limit": "100"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "limit": "200"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "view": "detail"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "view": "summary"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "limit": "50", "view": "detail"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "limit": "100", "view": "detail"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "limit": "25"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "limit": "75"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "limit": "150"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "limit": "250"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "view": "detail", "limit": "50"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "view": "detail", "limit": "100"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "view": "summary", "limit": "100"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "limit": "100", "view": "summary"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "limit": "200", "view": "detail"},
    {"cmd": "getmsgs", "msgtype": "{message}", "ticker": "{ticker}", "limit": "500"},
]

NUM_ENDPOINTS = len(ENDPOINT_SHAPES)
NUM_MESSAGE_BATCHES = NUM_ENDPOINTS


def message_batch(run_index: int, catalog: list[str] | None = None) -> tuple[int, list[str]]:
    """Split catalog into 18 slices; each run scans one slice (covers all 58 over 18 runs)."""
    msgs = catalog or ALL58_MESSAGES
    per = max(1, math.ceil(len(msgs) / NUM_MESSAGE_BATCHES))
    batch_idx = run_index % NUM_MESSAGE_BATCHES
    start = batch_idx * per
    batch = msgs[start : start + per]
    return batch_idx, batch
