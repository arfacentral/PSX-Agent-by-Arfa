import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from psx_agent.models import Candle
from psx_agent.providers.base import MarketDataProvider


class PsxDpsProvider(MarketDataProvider):
    """Reads end-of-day series from the public PSX DPS website.

    DPS currently returns rows as:
    [unix_timestamp, close, volume, open]

    The endpoint does not expose daily high/low in this response, so this
    provider conservatively derives high/low from open and close.
    """

    def __init__(
        self,
        base_url: str = "https://dps.psx.com.pk",
        cache_dir: str = "data/cache/psx_dps",
        cache_ttl_seconds: int = 60 * 60 * 8,
        request_pause_seconds: float = 0.6,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.cache_dir = Path(cache_dir)
        self.cache_ttl_seconds = cache_ttl_seconds
        self.request_pause_seconds = request_pause_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json,text/plain,*/*",
                "User-Agent": "psx-morning-signal-agent/0.1 personal-use research",
            }
        )

    def get_history(self, symbol: str, lookback_days: int = 120) -> list[Candle]:
        symbol = symbol.upper().strip()
        payload = self._load_payload(symbol)
        rows = payload.get("data", [])
        candles = [self._row_to_candle(symbol, row) for row in rows if self._valid_row(row)]
        candles = sorted(candles, key=lambda candle: candle.date)
        return candles[-lookback_days:]

    def _load_payload(self, symbol: str) -> dict[str, Any]:
        cache_path = self.cache_dir / f"{symbol}.json"
        if self._cache_is_fresh(cache_path):
            return json.loads(cache_path.read_text(encoding="utf-8"))

        time.sleep(self.request_pause_seconds)
        response = self.session.get(f"{self.base_url}/timeseries/eod/{symbol}", timeout=20)
        response.raise_for_status()
        payload = response.json()

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    def _cache_is_fresh(self, cache_path: Path) -> bool:
        if not cache_path.exists():
            return False
        age = time.time() - cache_path.stat().st_mtime
        return age < self.cache_ttl_seconds

    def _valid_row(self, row: Any) -> bool:
        return isinstance(row, list) and len(row) >= 4

    def _row_to_candle(self, symbol: str, row: list[Any]) -> Candle:
        timestamp, close, volume, open_price = row[:4]
        day = datetime.fromtimestamp(int(timestamp), tz=UTC).date()
        open_float = float(open_price)
        close_float = float(close)
        high = max(open_float, close_float)
        low = min(open_float, close_float)

        return Candle(
            symbol=symbol,
            date=day,
            open=round(open_float, 2),
            high=round(high, 2),
            low=round(low, 2),
            close=round(close_float, 2),
            volume=int(volume),
        )
