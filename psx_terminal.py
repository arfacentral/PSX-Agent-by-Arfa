import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from psx_agent.models import Candle, Quote
from psx_agent.providers.base import MarketDataProvider


class PsxTerminalProvider(MarketDataProvider):
    """Provider for the public PSX Terminal REST API."""

    def __init__(
        self,
        base_url: str = "https://psxterminal.com",
        market_type: str = "REG",
        cache_dir: str = "data/cache/psx_terminal",
        quote_cache_ttl_seconds: int = 15,
        kline_cache_ttl_seconds: int = 60 * 60 * 8,
        max_rest_quote_symbols: int = 500,
        rest_pause_seconds: float = 0.65,
        quote_workers: int = 6,
        use_tick_endpoint: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.market_type = market_type.upper()
        self.cache_dir = Path(cache_dir)
        self.quote_cache_ttl_seconds = quote_cache_ttl_seconds
        self.kline_cache_ttl_seconds = kline_cache_ttl_seconds
        self.max_rest_quote_symbols = max_rest_quote_symbols
        self.rest_pause_seconds = rest_pause_seconds
        self.quote_workers = max(1, quote_workers)
        self.use_tick_endpoint = use_tick_endpoint
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update(
            {
                "Accept": "application/json,text/plain,*/*",
                "User-Agent": "psx-morning-signal-agent/0.3",
            }
        )

    def get_history(self, symbol: str, lookback_days: int = 120) -> list[Candle]:
        symbol = symbol.upper().strip()
        payload = self._cached_get(
            cache_key=f"klines_{symbol}_1d_{lookback_days}",
            ttl_seconds=self.kline_cache_ttl_seconds,
            path=f"/api/klines/{symbol}/1d",
            params={"limit": str(min(max(lookback_days, 60), 500))},
        )
        rows = payload.get("data", [])
        candles = [self._kline_to_candle(symbol, row) for row in rows if self._valid_kline(row)]
        candles = sorted(candles, key=lambda candle: candle.date)
        return candles[-lookback_days:]

    def get_quotes(self, symbols: list[str] | None = None) -> list[Quote]:
        # Compatibility with the older endpoint mentioned in community posts.
        market_data = self._try_market_data_endpoint()
        if market_data:
            return market_data

        selected_symbols = symbols or self.list_symbols()
        selected_symbols = [symbol.upper().strip() for symbol in selected_symbols if symbol.strip()]
        selected_symbols = selected_symbols[: self.max_rest_quote_symbols]
        if self.quote_workers <= 1 or len(selected_symbols) <= 1:
            quotes: list[Quote] = []
            for symbol in selected_symbols:
                try:
                    quotes.append(self.get_quote(symbol))
                except Exception:
                    quotes.append(Quote(symbol=symbol))
                time.sleep(self.rest_pause_seconds)
            return quotes

        quotes_by_symbol: dict[str, Quote] = {}
        worker_count = min(self.quote_workers, len(selected_symbols))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {executor.submit(self.get_quote, symbol): symbol for symbol in selected_symbols}
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    quotes_by_symbol[symbol] = future.result()
                except Exception:
                    quotes_by_symbol[symbol] = Quote(symbol=symbol)
        return [quotes_by_symbol.get(symbol, Quote(symbol=symbol)) for symbol in selected_symbols]

    def get_quote(self, symbol: str) -> Quote:
        symbol = symbol.upper().strip()
        if self.use_tick_endpoint:
            try:
                payload = self._cached_get(
                    cache_key=f"tick_{self.market_type}_{symbol}",
                    ttl_seconds=self.quote_cache_ttl_seconds,
                    path=f"/api/ticks/{self.market_type}/{symbol}",
                )
                return self._tick_to_quote(payload.get("data", {}))
            except Exception:
                pass

        try:
            fundamentals = self.get_fundamentals(symbol)
            quote = self._fundamentals_to_quote(fundamentals)
        except Exception:
            payload = self._cached_get(
                cache_key=f"klines_quote_{symbol}",
                ttl_seconds=self.quote_cache_ttl_seconds,
                path=f"/api/klines/{symbol}/1d",
                params={"limit": "1"},
            )
            rows = payload.get("data", [])
            quote = self._kline_to_quote(symbol, rows[-1]) if rows else Quote(symbol=symbol)
        return quote

    def list_symbols(self) -> list[str]:
        payload = self._cached_get("symbols", 60 * 60, "/api/symbols")
        return sorted({str(symbol).upper() for symbol in payload.get("data", [])})

    def get_fundamentals(self, symbol: str) -> dict[str, Any]:
        symbol = symbol.upper().strip()
        payload = self._cached_get(
            cache_key=f"fundamentals_{symbol}",
            ttl_seconds=60 * 60 * 8,
            path=f"/api/fundamentals/{symbol}",
        )
        return payload.get("data", {})

    def _try_market_data_endpoint(self) -> list[Quote]:
        try:
            payload = self._cached_get(
                cache_key=f"market_data_{self.market_type}",
                ttl_seconds=self.quote_cache_ttl_seconds,
                path="/api/market-data",
                params={"market": self.market_type},
                raise_on_api_error=False,
            )
        except Exception:
            return []

        rows = payload.get("data", [])
        if not payload.get("success") or not isinstance(rows, list):
            return []
        return [self._tick_to_quote(row) for row in rows if isinstance(row, dict)]

    def _cached_get(
        self,
        cache_key: str,
        ttl_seconds: int,
        path: str,
        params: dict[str, str] | None = None,
        raise_on_api_error: bool = True,
    ) -> dict[str, Any]:
        cache_path = self.cache_dir / f"{cache_key}.json"
        if self._cache_is_fresh(cache_path, ttl_seconds):
            return json.loads(cache_path.read_text(encoding="utf-8"))

        response = self.session.get(f"{self.base_url}{path}", params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if raise_on_api_error and payload.get("success") is False:
            raise RuntimeError(payload.get("error") or "PSX Terminal API returned an error")

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    def _cache_is_fresh(self, cache_path: Path, ttl_seconds: int) -> bool:
        if not cache_path.exists():
            return False
        return (time.time() - cache_path.stat().st_mtime) < ttl_seconds

    def _tick_to_quote(self, row: dict[str, Any]) -> Quote:
        symbol = str(row.get("symbol") or row.get("s") or "").upper()
        return Quote(
            symbol=symbol,
            date=self._timestamp_to_text(row.get("timestamp") or row.get("t")),
            open=None,
            high=self._float_or_none(row.get("high") or row.get("h")),
            low=self._float_or_none(row.get("low") or row.get("l")),
            close=self._float_or_none(row.get("price") or row.get("c")),
            volume=self._int_or_none(row.get("volume") or row.get("v")),
            change=self._float_or_none(row.get("change") or row.get("ch")),
            change_percent=self._float_or_none(row.get("changePercent") or row.get("pch")),
            bid_price=self._float_or_none(row.get("bid") or row.get("bp")),
            bid_volume=self._int_or_none(row.get("bidVol") or row.get("bv")),
            ask_price=self._float_or_none(row.get("ask") or row.get("ap")),
            ask_volume=self._int_or_none(row.get("askVol") or row.get("av")),
        )

    def _fundamentals_to_quote(self, row: dict[str, Any]) -> Quote:
        return Quote(
            symbol=str(row.get("symbol") or "").upper(),
            sector=str(row.get("sector")) if row.get("sector") is not None else None,
            date=row.get("timestamp"),
            close=self._float_or_none(row.get("price")),
            volume=self._int_or_none(row.get("volume30Avg")),
            change_percent=self._float_or_none(row.get("changePercent")),
            market_cap=self._compact_number(row.get("marketCap")),
            pe_ratio=self._float_or_none(row.get("peRatio")),
            dividend_yield=self._float_or_none(row.get("dividendYield")),
            year_change=self._float_or_none(row.get("yearChange")),
            listed_in=row.get("listedIn"),
            non_compliant=row.get("isNonCompliant"),
        )

    def _kline_to_quote(self, symbol: str, row: dict[str, Any]) -> Quote:
        return Quote(
            symbol=symbol,
            date=self._timestamp_to_text(row.get("timestamp")),
            open=self._float_or_none(row.get("open")),
            high=self._float_or_none(row.get("high")),
            low=self._float_or_none(row.get("low")),
            close=self._float_or_none(row.get("close")),
            volume=self._int_or_none(row.get("volume")),
        )

    def _valid_kline(self, row: Any) -> bool:
        return isinstance(row, dict) and {"timestamp", "open", "high", "low", "close", "volume"} <= set(row)

    def _kline_to_candle(self, symbol: str, row: dict[str, Any]) -> Candle:
        return Candle(
            symbol=symbol,
            date=datetime.fromtimestamp(int(row["timestamp"]) / 1000, tz=UTC).date(),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=int(row["volume"] or 0),
        )

    def _timestamp_to_text(self, value: Any) -> str | None:
        if value in (None, ""):
            return None
        timestamp = int(value)
        if timestamp > 10_000_000_000:
            timestamp = timestamp // 1000
        return datetime.fromtimestamp(timestamp, tz=UTC).isoformat()

    def _float_or_none(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        return float(value)

    def _int_or_none(self, value: Any) -> int | None:
        if value in (None, ""):
            return None
        return int(float(value))

    def _compact_number(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).replace(",", "").strip().upper()
        multiplier = 1.0
        if text.endswith("B"):
            multiplier = 1_000_000_000
            text = text[:-1]
        elif text.endswith("M"):
            multiplier = 1_000_000
            text = text[:-1]
        elif text.endswith("K"):
            multiplier = 1_000
            text = text[:-1]
        return float(text) * multiplier
