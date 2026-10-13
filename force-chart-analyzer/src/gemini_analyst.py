import json
import logging
import time
from dataclasses import dataclass
from typing import Optional

import requests

from config.settings import GEMINI_API_KEY, GEMINI_COOLDOWN

logger = logging.getLogger(__name__)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key={key}"
)


@dataclass
class Judgment:
    symbol:     str
    action:     str       # BUY | SELL | NEUTRAL
    confidence: str       # HIGH | MEDIUM | LOW
    reason:     str
    entry:      float = 0.0
    sl:         float = 0.0
    tp1:        float = 0.0
    tp2:        float = 0.0
    rr_ratio:   str   = ""
    timestamp:  float = 0.0

    def color(self) -> str:
        return {
            "BUY":     "#26a69a",
            "SELL":    "#ef5350",
            "NEUTRAL": "#ffd54f",
        }.get(self.action, "#888888")


def _build_prompt(symbol: str, snap: dict) -> str:
    return f"""You are an algorithmic trading system making ONE decision right now.

SYMBOL: {symbol}
TIMEFRAME: 1 minute (scalping)

LIVE DATA:
  Price now : {snap['price']}
  High      : {snap['price_high']}
  Low       : {snap['price_low']}
  ATR(14)   : {snap['atr']}
  Support   : {snap['support']}
  Resistance: {snap['resistance']}

INDICATORS:
  RSI(14)   : {snap['rsi']}
  MACD hist : {snap['macd_hist']} (positive=bullish momentum, negative=bearish)
  MACD line : {snap['macd']}
  MACD sig  : {snap['macd_signal']}
  BB upper  : {snap['bb_upper']}
  BB lower  : {snap['bb_lower']}
  BB width  : {snap['bb_width']}
  Force idx : {snap['force_index']} ({snap['force_signal']})
  Force slp : {snap['force_slope']}

DECISION RULES — follow strictly:
1. Look at ALL indicators together, not one by one.
2. If majority signals agree on direction → take that trade NOW.
3. If signals conflict → NEUTRAL, do not trade.
4. action must be exactly one of: BUY, SELL, or NEUTRAL.
5. For BUY: entry = current price, SL = below support or 1.5x ATR below, TP1 = 1x ATR above, TP2 = 2.5x ATR above.
6. For SELL: entry = current price, SL = above resistance or 1.5x ATR above, TP1 = 1x ATR below, TP2 = 2.5x ATR below.
7. For NEUTRAL: set entry=0, sl=0, tp1=0, tp2=0.
8. reason must explain WHY this exact action — name which indicators aligned.

Respond ONLY in this JSON, no markdown, no extra text:
{{
  "action": "BUY" or "SELL" or "NEUTRAL",
  "confidence": "HIGH" or "MEDIUM" or "LOW",
  "entry": <number>,
  "sl": <number>,
  "tp1": <number>,
  "tp2": <number>,
  "rr_ratio": "<string like 1:2.0>",
  "reason": "<one sentence, max 120 chars, name the indicators>"
}}"""


class GeminiAnalyst:
    def __init__(self) -> None:
        self._cache:    dict[str, Judgment] = {}
        self._last_req: dict[str, float]    = {}
        self._cooldown  = GEMINI_COOLDOWN

    def analyze(self, symbol: str, snap: dict) -> Optional[Judgment]:
        now = time.time()

        if now - self._last_req.get(symbol, 0) < self._cooldown:
            return self._cache.get(symbol)

        if snap.get("candles", 0) < 30:
            return self._cache.get(symbol)

        try:
            url  = GEMINI_URL.format(key=GEMINI_API_KEY)
            body = {
                "contents": [{"parts": [{"text": _build_prompt(symbol, snap)}]}],
                "generationConfig": {
                    "temperature":     0.0,   # deterministic
                    "maxOutputTokens": 200,
                },
            }
            resp = requests.post(url, json=body, timeout=15)
            resp.raise_for_status()

            raw  = resp.json()
            text = raw["candidates"][0]["content"]["parts"][0]["text"].strip()
            text = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text)

            action = str(data.get("action", "NEUTRAL")).upper()
            if action not in ("BUY", "SELL", "NEUTRAL"):
                action = "NEUTRAL"

            j = Judgment(
                symbol     = symbol,
                action     = action,
                confidence = str(data.get("confidence", "LOW")).upper(),
                entry      = float(data.get("entry",    0.0)),
                sl         = float(data.get("sl",       0.0)),
                tp1        = float(data.get("tp1",      0.0)),
                tp2        = float(data.get("tp2",      0.0)),
                rr_ratio   = str(data.get("rr_ratio",  "")),
                reason     = str(data.get("reason",    "")),
                timestamp  = now,
            )

            self._cache[symbol]    = j
            self._last_req[symbol] = now

            logger.info(
                f"[Gemini] {symbol} → {j.action} ({j.confidence}) "
                f"entry={j.entry} sl={j.sl} tp1={j.tp1} tp2={j.tp2}"
            )
            return j

        except Exception as e:
            logger.warning(f"[Gemini] {symbol} failed: {e}")
            return self._cache.get(symbol)
