from datetime import date, timedelta
from random import Random

from psx_agent.models import Candle
from psx_agent.providers.base import MarketDataProvider


class DemoProvider(MarketDataProvider):
    """Deterministic demo data so the agent works without a market-data license."""

    def get_history(self, symbol: str, lookback_days: int = 120) -> list[Candle]:
        rng = Random(symbol)
        base = rng.uniform(35, 450)
        trend = rng.uniform(-0.15, 0.32)
        volatility = rng.uniform(0.01, 0.035)
        today = date.today()
        candles: list[Candle] = []
        close = base

        for idx in range(lookback_days):
            day = today - timedelta(days=lookback_days - idx)
            if day.weekday() > 4:
                continue

            drift = trend / 252
            shock = rng.gauss(drift, volatility)
            open_price = close * (1 + rng.gauss(0, volatility / 2))
            close = max(1, close * (1 + shock))
            high = max(open_price, close) * (1 + abs(rng.gauss(0, volatility / 2)))
            low = min(open_price, close) * (1 - abs(rng.gauss(0, volatility / 2)))
            volume = int(rng.uniform(300_000, 6_000_000))

            candles.append(
                Candle(
                    symbol=symbol,
                    date=day,
                    open=round(open_price, 2),
                    high=round(high, 2),
                    low=round(low, 2),
                    close=round(close, 2),
                    volume=volume,
                )
            )

        return candles

