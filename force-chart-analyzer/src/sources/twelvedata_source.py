import json
import logging
import time
from typing import Callable

import websockets

from config.settings import TWELVE_DATA_API_KEY
from .base import BaseSource, Candle, DataBuffer

logger = logging.getLogger(__name__)

TD_WS_URL = "wss://ws.twelvedata.com/v1/quotes/price"


class TwelveDataMultiSource:
    def __init__(self, symbols: list[str], on_update: Callable[[DataBuffer], None]):
        self.symbols    = symbols
        self.on_update  = on_update
        self.buffers    = {s: DataBuffer(symbol=s) for s in symbols}
        self._ot_track: dict[str, int] = {}

    def _subscribe_msg(self) -> str:
        return json.dumps({
            "action": "subscribe",
            "params": {
                "symbols": ",".join(self.symbols),
                "apikey":  TWELVE_DATA_API_KEY,
            }
        })

    async def run(self) -> None:
        logger.info(f"[TwelveData] connecting → {self.symbols}")
        async for ws in websockets.connect(TD_WS_URL, ping_interval=30):
            try:
                await ws.send(self._subscribe_msg())
                async for raw in ws:
                    msg = json.loads(raw)
                    if msg.get("event") != "price":
                        continue

                    sym = msg.get("symbol", "")
                    if sym not in self.buffers:
                        continue

                    price  = float(msg.get("price", 0))
                    ts_ms  = int(msg.get("timestamp", time.time())) * 1000
                    bucket = (ts_ms // 60_000) * 60_000
                    prev   = self._ot_track.get(sym)
                    closed = prev is not None and bucket != prev

                    buf    = self.buffers[sym]
                    candle = Candle(
                        open_time = bucket,
                        open      = price,
                        high      = price,
                        low       = price,
                        close     = price,
                        volume    = 0.0,
                        closed    = closed,
                        symbol    = sym,
                    )

                    if buf.candles and buf.candles[-1].open_time == bucket:
                        p             = buf.candles[-1]
                        candle.open   = p.open
                        candle.high   = max(p.high, price)
                        candle.low    = min(p.low,  price)
                        candle.volume = p.volume

                    self._ot_track[sym] = bucket
                    buf.push(candle)
                    self.on_update(buf)

            except websockets.ConnectionClosed:
                logger.warning("[TwelveData] disconnected — retry")
                continue
