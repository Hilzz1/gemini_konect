import json
import logging

import websockets

from config.settings import INTERVAL
from .base import BaseSource, Candle

logger = logging.getLogger(__name__)


class BinanceSource(BaseSource):
    def _ws_url(self) -> str:
        sym = self.symbol.lower()
        tf  = INTERVAL.replace("min", "m").replace("hour", "h")
        return f"wss://stream.binance.com:9443/ws/{sym}@kline_{tf}"

    async def run(self) -> None:
        url = self._ws_url()
        logger.info(f"[Binance] connecting → {self.symbol}")
        async for ws in websockets.connect(url, ping_interval=20):
            try:
                async for raw in ws:
                    msg = json.loads(raw)
                    k   = msg["k"]
                    self.buffer.push(Candle(
                        open_time = k["t"],
                        open      = float(k["o"]),
                        high      = float(k["h"]),
                        low       = float(k["l"]),
                        close     = float(k["c"]),
                        volume    = float(k["v"]),
                        closed    = k["x"],
                        symbol    = self.symbol,
                    ))
                    self.on_update(self.buffer)
            except websockets.ConnectionClosed:
                logger.warning(f"[Binance] {self.symbol} disconnected — retry")
                continue
