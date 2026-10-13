import asyncio
import logging
import threading
import time
from typing import Optional

import plotly.graph_objects as go

from config.settings import (
    CHART_REFRESH, SYMBOLS, source_for,
    TWELVE_DATA_API_KEY, GEMINI_API_KEY,
)
from .sources.base import DataBuffer
from .sources.binance_source import BinanceSource
from .sources.twelvedata_source import TwelveDataMultiSource
from .force_indicators import (
    candles_to_df, elder_force_index, signal, market_snapshot,
)
from .chart_engine import build_chart
from .dashboard import build_dashboard
from .gemini_analyst import GeminiAnalyst, Judgment

logger = logging.getLogger(__name__)


class Analyzer:
    def __init__(self) -> None:
        self._charts:    dict[str, go.Figure]          = {}
        self._signals:   dict[str, str]                 = {}
        self._judgments: dict[str, Optional[Judgment]]  = {}
        self._lock       = threading.Lock()
        self._analyst    = GeminiAnalyst() if GEMINI_API_KEY else None

        self._binance_symbols = [s for s in SYMBOLS if source_for(s) == "binance"]
        self._td_symbols      = [s for s in SYMBOLS if source_for(s) == "twelvedata"]

        if not GEMINI_API_KEY:
            logger.warning("[Analyzer] GEMINI_API_KEY missing — judgments disabled")

    def _on_update(self, buf: DataBuffer) -> None:
        closed = buf.closed_candles()
        if len(closed) < 30:
            return

        df   = candles_to_df(closed)
        snap = market_snapshot(df)
        sig  = snap["force_signal"]
        force = elder_force_index(df)
        fig  = build_chart(buf.symbol, df, force, sig)

        judgment = None
        if self._analyst:
            judgment = self._analyst.analyze(
                symbol = buf.symbol,
                snap   = snap,
            )
            if judgment:
                # rebuild chart with judgment levels
                fig = build_chart(buf.symbol, df, force, sig, judgment)

        with self._lock:
            self._charts[buf.symbol]    = fig
            self._signals[buf.symbol]   = sig
            self._judgments[buf.symbol] = judgment

    def _render_loop(self) -> None:
        while True:
            time.sleep(CHART_REFRESH)
            with self._lock:
                charts    = dict(self._charts)
                signals   = dict(self._signals)
                judgments = dict(self._judgments)
            if charts:
                html = build_dashboard(charts, signals, judgments)
                with open("dashboard.html", "w", encoding="utf-8") as f:
                    f.write(html)

    async def _run_async(self) -> None:
        tasks = []
        for sym in self._binance_symbols:
            src = BinanceSource(sym, self._on_update)
            tasks.append(asyncio.create_task(src.run()))

        if self._td_symbols:
            if not TWELVE_DATA_API_KEY:
                logger.error("[TwelveData] key missing")
            else:
                td = TwelveDataMultiSource(self._td_symbols, self._on_update)
                tasks.append(asyncio.create_task(td.run()))

        await asyncio.gather(*tasks)

    def run(self) -> None:
        t = threading.Thread(target=self._render_loop, daemon=True)
        t.start()
        print(f"[Analyzer] Symbols  : {SYMBOLS}")
        print(f"[Analyzer] Gemini   : {'enabled ✓' if self._analyst else 'disabled (no key)'}")
        print(f"[Analyzer] Dashboard → dashboard.html")
        asyncio.run(self._run_async())
