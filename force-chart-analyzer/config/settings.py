from dotenv import load_dotenv
import os

load_dotenv()

TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "")
GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY", "")
FORCE_PERIOD        = int(os.getenv("FORCE_PERIOD", 13))
BUFFER_SIZE         = int(os.getenv("BUFFER_SIZE", 500))
CHART_REFRESH       = float(os.getenv("CHART_REFRESH", 2.0))
INTERVAL            = os.getenv("INTERVAL", "1min")
GEMINI_COOLDOWN     = float(os.getenv("GEMINI_COOLDOWN", 30.0))  # seconds per symbol

_raw = os.getenv("SYMBOLS", "XAUUSD,XAGUSD,EURUSD,GBPUSD,USDJPY,BTCUSDT,ETHUSDT,BNBUSDT")
SYMBOLS = [s.strip().upper() for s in _raw.split(",") if s.strip()]

BINANCE_SYMBOLS = {
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "MATICUSDT", "DOTUSDT", "AVAXUSDT",
}

def source_for(symbol: str) -> str:
    return "binance" if symbol.upper() in BINANCE_SYMBOLS else "twelvedata"
