import numpy as np
import pandas as pd

from config.settings import FORCE_PERIOD
from .sources.base import Candle


def candles_to_df(candles: list[Candle]) -> pd.DataFrame:
    rows = [{
        "open_time": c.open_time,
        "open":      c.open,
        "high":      c.high,
        "low":       c.low,
        "close":     c.close,
        "volume":    c.volume,
    } for c in candles]
    return pd.DataFrame(rows).set_index("open_time")


# ── Elder Force Index ─────────────────────────────────────────────────────────

def elder_force_index(df: pd.DataFrame, period: int = FORCE_PERIOD) -> pd.Series:
    raw = df["volume"] * df["close"].diff()
    if df["volume"].sum() == 0:
        raw = df["close"].diff()
    return raw.ewm(span=period, adjust=False).mean().rename("force_index")


def force_slope(series: pd.Series, lookback: int = 5) -> float:
    if len(series) < lookback:
        return 0.0
    y = series.iloc[-lookback:].values.astype(float)
    x = np.arange(lookback)
    return float(np.polyfit(x, y, 1)[0])


def signal(series: pd.Series) -> str:
    if len(series) < 2:
        return "LOADING"
    last  = series.iloc[-1]
    slope = force_slope(series)
    if last > 0 and slope > 0:   return "BULLISH_PRESSURE"
    if last < 0 and slope < 0:   return "BEARISH_PRESSURE"
    if last > 0 and slope < 0:   return "BULL_FADING"
    return "BEAR_FADING"


# ── RSI ───────────────────────────────────────────────────────────────────────

def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = df["close"].diff()
    gain  = delta.clip(lower=0).ewm(com=period - 1, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(com=period - 1, adjust=False).mean()
    rs    = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).rename("rsi")


# ── MACD ──────────────────────────────────────────────────────────────────────

def macd(df: pd.DataFrame,
         fast: int = 12, slow: int = 26, signal_period: int = 9
         ) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast   = df["close"].ewm(span=fast,   adjust=False).mean()
    ema_slow   = df["close"].ewm(span=slow,   adjust=False).mean()
    macd_line  = (ema_fast - ema_slow).rename("macd")
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean().rename("macd_signal")
    histogram  = (macd_line - signal_line).rename("macd_hist")
    return macd_line, signal_line, histogram


# ── Bollinger Bands ───────────────────────────────────────────────────────────

def bollinger(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0
              ) -> tuple[pd.Series, pd.Series, pd.Series]:
    mid   = df["close"].rolling(period).mean().rename("bb_mid")
    std   = df["close"].rolling(period).std()
    upper = (mid + std_dev * std).rename("bb_upper")
    lower = (mid - std_dev * std).rename("bb_lower")
    return upper, mid, lower


# ── ATR (Average True Range) ──────────────────────────────────────────────────

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - close).abs(),
        (low  - close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(com=period - 1, adjust=False).mean().rename("atr")


# ── Support / Resistance ──────────────────────────────────────────────────────

def support_resistance(df: pd.DataFrame, lookback: int = 50) -> dict[str, float]:
    """
    Pivot-based S/R using the last `lookback` candles.
    Returns nearest support below and resistance above current price.
    """
    if len(df) < lookback:
        lookback = len(df)

    chunk  = df.iloc[-lookback:]
    price  = float(df["close"].iloc[-1])

    highs  = chunk["high"].values
    lows   = chunk["low"].values

    # local pivot highs (resistance candidates)
    r_levels = []
    for i in range(1, len(highs) - 1):
        if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
            r_levels.append(highs[i])

    # local pivot lows (support candidates)
    s_levels = []
    for i in range(1, len(lows) - 1):
        if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
            s_levels.append(lows[i])

    resistance = min((r for r in r_levels if r > price), default=float(chunk["high"].max()))
    support    = max((s for s in s_levels if s < price), default=float(chunk["low"].min()))

    return {"support": round(support, 6), "resistance": round(resistance, 6)}


# ── Full market snapshot ──────────────────────────────────────────────────────

def market_snapshot(df: pd.DataFrame) -> dict:
    """One call — returns everything the analyst needs."""
    force   = elder_force_index(df)
    rsi_val = rsi(df)
    macd_l, macd_s, macd_h = macd(df)
    bb_u, bb_m, bb_l       = bollinger(df)
    atr_val = atr(df)
    sr      = support_resistance(df)

    price       = float(df["close"].iloc[-1])
    atr_current = float(atr_val.iloc[-1])

    return {
        # price
        "price":       round(price, 6),
        "price_open":  round(float(df["open"].iloc[-1]),  6),
        "price_high":  round(float(df["high"].iloc[-1]),  6),
        "price_low":   round(float(df["low"].iloc[-1]),   6),

        # force
        "force_index":  round(float(force.iloc[-1]),  8),
        "force_signal": signal(force),
        "force_slope":  round(force_slope(force),     8),

        # rsi
        "rsi":          round(float(rsi_val.iloc[-1]), 2),

        # macd
        "macd":         round(float(macd_l.iloc[-1]), 8),
        "macd_signal":  round(float(macd_s.iloc[-1]), 8),
        "macd_hist":    round(float(macd_h.iloc[-1]), 8),

        # bollinger
        "bb_upper":     round(float(bb_u.iloc[-1]), 6),
        "bb_mid":       round(float(bb_m.iloc[-1]), 6),
        "bb_lower":     round(float(bb_l.iloc[-1]), 6),
        "bb_width":     round(float((bb_u - bb_l).iloc[-1] / bb_m.iloc[-1]), 6),

        # atr
        "atr":          round(atr_current, 6),

        # support / resistance
        "support":      sr["support"],
        "resistance":   sr["resistance"],

        # derived levels
        "sl_buy":       round(price - 1.5 * atr_current, 6),
        "tp1_buy":      round(price + 1.0 * atr_current, 6),
        "tp2_buy":      round(price + 2.5 * atr_current, 6),
        "sl_sell":      round(price + 1.5 * atr_current, 6),
        "tp1_sell":     round(price - 1.0 * atr_current, 6),
        "tp2_sell":     round(price - 2.5 * atr_current, 6),

        # candle count
        "candles":      len(df),
    }


SIGNAL_COLOR = {
    "BULLISH_PRESSURE": "#26a69a",
    "BEARISH_PRESSURE": "#ef5350",
    "BULL_FADING":      "#ffd54f",
    "BEAR_FADING":      "#ff8a65",
    "LOADING":          "#888888",
}
