# force-chart-analyzer

Real-time Elder Force Index — multi-symbol dashboard.
Metals, Forex, Crypto. Single HTML dashboard, dropdown per symbol.

## Supported Symbols (default)

| Symbol  | Source      | Type   |
|---------|-------------|--------|
| XAUUSD  | Twelve Data | Metal  |
| XAGUSD  | Twelve Data | Metal  |
| EURUSD  | Twelve Data | Forex  |
| GBPUSD  | Twelve Data | Forex  |
| USDJPY  | Twelve Data | Forex  |
| BTCUSDT | Binance WS  | Crypto |
| ETHUSDT | Binance WS  | Crypto |
| BNBUSDT | Binance WS  | Crypto |

Add any symbol to `SYMBOLS` in `.env` — routing is automatic.

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env → add TWELVE_DATA_API_KEY (free at twelvedata.com)
python main.py
# Open dashboard.html in browser, refresh to update
```

## Signal Legend

| Signal           | Meaning                         |
|------------------|---------------------------------|
| BULLISH_PRESSURE | Force rising, buyers in control |
| BEARISH_PRESSURE | Force falling, sellers control  |
| BULL_FADING      | Buying pressure weakening       |
| BEAR_FADING      | Selling pressure weakening      |

## Gemini Integration

Connect via **gemini.google.com/apps → GitHub → this repo**.

Ask Gemini:
- *"explain the force_slope function"*
- *"which symbols show BEARISH_PRESSURE?"*
- *"suggest improvements for the reconnect logic"*

## Run Tests

```bash
pytest tests/
```
