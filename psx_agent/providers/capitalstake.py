import json
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from psx_agent.models import Candle, Quote
from psx_agent.providers.base import MarketDataProvider


class CapitalStakeProvider(MarketDataProvider):
    """Capital Stake REST API provider.

    Docs used:
    - GET /3.0/market/quotes for real-time all-stock quotes
    - GET /3.0/market/stocks for the stock universe
    - GET /3.0/market/eod for historical OHLCV
    """

    def __init__(
        self,
        api_token: str,
        base_url: str = "https://csapis.com",
        cache_dir: str = "data/cache/capitalstake",
        quote_cache_ttl_seconds: int = 15,
        eod_cache_ttl_seconds: int = 60 * 60 * 8,
    ) -> None:
        self.api_token = api_token.strip()
        self.base_url = base_url.rstrip("/")
        self.cache_dir = Path(cache_dir)
        self.quote_cache_ttl_seconds = quote_cache_ttl_seconds
        self.eod_cache_ttl_seconds = eod_cache_ttl_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_token}",
                "User-Agent": "psx-morning-signal-agent/0.2",
            }
        )

    def get_history(self, symbol: str, lookback_days: int = 120) -> list[Candle]:
        self._require_token()
        symbol = symbol.upper().strip()
        today = date.today()
        start = today - timedelta(days=max(lookback_days * 2, 220))
        payload = self._cached_request(
            cache_key=f"eod_{symbol}_{start.isoformat()}_{today.isoformat()}",
            ttl_seconds=self.eod_cache_ttl_seconds,
            path="/3.0/market/eod",
            params={"symbol": symbol, "from": start.isoformat(), "to": today.isoformat()},
        )
        rows = payload.get("data", [])
        candles = [self._row_to_candle(symbol, row) for row in rows if self._valid_eod_row(row)]
        candles = sorted(candles, key=lambda candle: candle.date)
        return candles[-lookback_days:]

    def get_quotes(self, symbols: list[str] | None = None) -> list[Quote]:
        self._require_token()
        params = None
        cache_key = "quotes_all"
        if symbols:
            cleaned = sorted({symbol.upper().strip() for symbol in symbols if symbol.strip()})
            params = {"symbol": ",".join(cleaned)}
            cache_key = f"quotes_{'_'.join(cleaned)}"

        payload = self._cached_request(
            cache_key=cache_key,
            ttl_seconds=self.quote_cache_ttl_seconds,
            path="/3.0/market/quotes",
            params=params,
        )
        rows = payload.get("data", [])
        return [self._row_to_quote(row) for row in rows if isinstance(row, dict) and row.get("symbol")]

    def list_symbols(self) -> list[str]:
        quotes = self.get_quotes()
        symbols = [quote.symbol for quote in quotes if quote.symbol]
        return sorted(set(symbols))

    def _cached_request(
        self,
        cache_key: str,
        ttl_seconds: int,
        path: str,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        cache_path = self.cache_dir / f"{cache_key}.json"
        if self._cache_is_fresh(cache_path, ttl_seconds):
            return json.loads(cache_path.read_text(encoding="utf-8"))

        response = self.session.get(f"{self.base_url}{path}", params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "ok":
            message = payload.get("message") or "Capital Stake API returned an error"
            raise RuntimeError(message)

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    def _cache_is_fresh(self, cache_path: Path, ttl_seconds: int) -> bool:
        if not cache_path.exists():
            return False
        return (time.time() - cache_path.stat().st_mtime) < ttl_seconds

    def _require_token(self) -> None:
        if not self.api_token:
            raise RuntimeError("CAPITALSTAKE_API_TOKEN is missing. Add it to .env, then restart the agent.")

    def _valid_eod_row(self, row: Any) -> bool:
        return isinstance(row, dict) and {"time", "open", "high", "low", "close", "volume"} <= set(row)

    def _row_to_candle(self, symbol: str, row: dict[str, Any]) -> Candle:
        return Candle(
            symbol=symbol,
            date=datetime.fromtimestamp(int(row["time"]), tz=UTC).date(),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=int(row["volume"] or 0),
        )

    def _row_to_quote(self, row: dict[str, Any]) -> Quote:
        return Quote(
            symbol=str(row.get("symbol", "")).upper(),
            name=row.get("name"),
            sector=row.get("sector"),
            date=row.get("date"),
            open=self._float_or_none(row.get("open")),
            high=self._float_or_none(row.get("high")),
            low=self._float_or_none(row.get("low")),
            close=self._float_or_none(row.get("close")),
            volume=self._int_or_none(row.get("volume")),
            change=self._float_or_none(row.get("change")),
            change_percent=self._float_or_none(row.get("change_percent")),
            bid_price=self._float_or_none(row.get("bid_price")),
            bid_volume=self._int_or_none(row.get("bid_volume")),
            ask_price=self._float_or_none(row.get("ask_price")),
            ask_volume=self._int_or_none(row.get("ask_volume")),
            high52=self._float_or_none(row.get("high52")),
            low52=self._float_or_none(row.get("low52")),
            market_cap=self._float_or_none(row.get("market_cap")),
        )

    def _float_or_none(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        return float(value)

    def _int_or_none(self, value: Any) -> int | None:
        if value in (None, ""):
            return None
        return int(value)
