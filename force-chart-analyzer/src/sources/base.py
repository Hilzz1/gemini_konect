from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from config.settings import BUFFER_SIZE


@dataclass
class Candle:
    open_time: int
    open:      float
    high:      float
    low:       float
    close:     float
    volume:    float
    closed:    bool
    symbol:    str = ""


@dataclass
class DataBuffer:
    symbol:  str = ""
    maxlen:  int = BUFFER_SIZE
    candles: deque = field(default_factory=lambda: deque(maxlen=BUFFER_SIZE))

    def push(self, candle: Candle) -> None:
        if self.candles and self.candles[-1].open_time == candle.open_time:
            self.candles[-1] = candle
        else:
            self.candles.append(candle)

    def closed_candles(self) -> list[Candle]:
        return [c for c in self.candles if c.closed]


class BaseSource(ABC):
    def __init__(self, symbol: str, on_update: Callable[[DataBuffer], None]):
        self.symbol    = symbol
        self.buffer    = DataBuffer(symbol=symbol)
        self.on_update = on_update

    @abstractmethod
    async def run(self) -> None: ...
