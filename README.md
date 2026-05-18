# PSX Agent by Arfa

An open, shareable starter agent for Pakistan Stock Exchange traders. It can use the PSX Terminal public API for live ticker data, fundamentals, historical candles, transparent technical signals, and a beginner-friendly watchlist with suggested action zones.

> Important: this project is decision support, not financial advice. DPS website terms still matter: use the data responsibly, avoid aggressive automated retrieval, and do not redistribute raw market data unless you have permission.

## What It Does

- Runs a daily pre-open analysis before PSX opens.
- Scores stocks using transparent indicators: trend, momentum, volume, volatility, and liquidity.
- Produces action ideas:
  - `BUY WATCH`: possible long setup.
  - `WAIT`: setup is unclear.
  - `AVOID`: risk or signal quality is poor.
- Gives beginner-friendly price levels:
  - suggested entry zone
  - stop-loss
  - first target
  - second target
  - invalidation reason
- Ships with a GUI that can be used locally by anyone you share the repo with.
- Uses `DATA_PROVIDER=psxterminal` by default, with Capital Stake, PSX DPS, demo, and CSV fallback providers available.
- Shows all fetched PSX Terminal tickers in the GUI, with ranked recommendations in a sortable table.

## Suggested Architecture

```text
Data Provider -> Signal Engine -> Risk Engine -> Recommendation Report
                         |                 |
                         v                 v
                    FastAPI Backend     Streamlit GUI
                         |
                         v
                  Daily Scheduler
```

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m psx_agent.seed_demo_data
uvicorn psx_agent.api:app --reload
```

In a second terminal:

```powershell
streamlit run gui/app.py
```

## Deployment

For sharing with family, see [DEPLOYMENT.md](DEPLOYMENT.md).

The simplest option is Streamlit Community Cloud using `app.py` as the main file.

## Daily Automation

Run the pre-open report manually:

```powershell
python -m psx_agent.jobs.preopen_report
```

Run the built-in scheduler:

```powershell
python -m psx_agent.scheduler
```

For production, schedule that command for roughly 8:45 AM Pakistan Standard Time on trading days. The agent is intentionally provider-neutral, so you can connect:

- a licensed PSX data feed
- an authorized vendor API
- your broker's market data export
- a manually downloaded CSV for personal use

## Configuration

Copy `.env.example` to `.env`.

```env
DATA_PROVIDER=psxterminal
PSXTERMINAL_BASE_URL=https://psxterminal.com
PSXTERMINAL_MARKET_TYPE=REG
PSXTERMINAL_QUOTE_CACHE_TTL_SECONDS=15
PSXTERMINAL_KLINE_CACHE_TTL_SECONDS=28800
PSXTERMINAL_MAX_REST_QUOTE_SYMBOLS=20
PSXTERMINAL_REST_PAUSE_SECONDS=0.1
PSXTERMINAL_USE_TICK_ENDPOINT=false
CAPITALSTAKE_BASE_URL=https://csapis.com
CAPITALSTAKE_API_TOKEN=your_token_here
CAPITALSTAKE_QUOTE_CACHE_TTL_SECONDS=15
CAPITALSTAKE_EOD_CACHE_TTL_SECONDS=28800
PSX_DPS_BASE_URL=https://dps.psx.com.pk
PSX_DPS_CACHE_TTL_SECONDS=28800
WATCHLIST=HBL,UBL,MCB,BAHL,MEBL,OGDC,PPL,POL,PSO,HUBC,LUCK,ENGRO,FFC,EFERT,SYS,AIRLINK,TRG,MLCF,DGKC,UNITY
REPORT_TIMEZONE=Asia/Karachi
MAX_RECOMMENDATIONS=20
MAX_ANALYSIS_SYMBOLS=0
RISK_PER_TRADE_PCT=1.0
```

## Provider Notes

`DATA_PROVIDER=psxterminal` uses PSX Terminal public endpoints:

- `GET https://psxterminal.com/api/symbols` for all symbols.
- `GET https://psxterminal.com/api/ticks/REG/{SYMBOL}` for live ticker data.
- `GET https://psxterminal.com/api/fundamentals/{SYMBOL}` for fundamentals and valuation data.
- `GET https://psxterminal.com/api/klines/{SYMBOL}/1d` for daily OHLCV history.
- `wss://psxterminal.com/` is the documented WebSocket endpoint for real-time streaming.

The current documented API does not expose one guaranteed all-symbol quote snapshot endpoint. The provider therefore tries the older `/api/market-data?market=REG` endpoint first, then falls back to `/api/symbols` plus per-symbol tick requests with caching and pacing.

`DATA_PROVIDER=capitalstake` uses Capital Stake REST API:

- `GET https://csapis.com/3.0/market/quotes` for all real-time stock quotes.
- `GET https://csapis.com/3.0/market/stocks` for stock universe metadata.
- `GET https://csapis.com/3.0/market/eod` for historical OHLCV used by the recommendation engine.

All Capital Stake endpoints require:

```text
Authorization: Bearer YOUR_API_TOKEN
```

Set `WATCHLIST=ALL` to show all stocks and analyze the most liquid names. `MAX_ANALYSIS_SYMBOLS` controls how many stocks receive deeper historical analysis per refresh.

`DATA_PROVIDER=psx_dps` reads end-of-day series from:

```text
https://dps.psx.com.pk/timeseries/eod/{SYMBOL}
```

The current DPS response includes timestamp, close price, volume, and open price. Because that response does not include high/low, the provider derives high/low from open and close. That keeps the recommendation engine running, but it is less precise than true OHLC data.

`DATA_PROVIDER=demo` uses generated demo data. `DATA_PROVIDER=csv` reads personal CSV files from `data/{SYMBOL}.csv`.

Useful starting points:

- PSX Data Portal: https://dps.psx.com.pk/
- PSX historical page: https://dps.psx.com.pk/historical

The provider boundary is deliberately small:

```python
provider.get_history(symbol: str, lookback_days: int) -> list[Candle]
```

## Automation Ideas

- Pre-open brief by email, Slack, WhatsApp, or Telegram.
- Intraday alert when price enters the suggested entry zone.
- Risk guard that blocks ideas with poor liquidity or wide spreads.
- Portfolio-aware sizing using account balance and risk-per-trade.
- News and corporate announcement filter before recommending trades.
- Market regime check using KSE-100/KSE-30 trend before single-stock ideas.
- Explainability log so every recommendation can be audited later.

## Responsible Use

The app should show reasoning and risk every time. Avoid black-box "best stock" claims. A useful trading assistant says:

- what changed
- what level matters
- what would prove the idea wrong
- how much downside is being accepted
