from pathlib import Path

import pandas as pd

from psx_agent.models import Candle
from psx_agent.providers.base import MarketDataProvider


class CsvProvider(MarketDataProvider):
    """Reads personal-use OHLCV files from data/{SYMBOL}.csv."""

    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = Path(data_dir)

    def get_history(self, symbol: str, lookback_days: int = 120) -> list[Candle]:
        path = self.data_dir / f"{symbol.upper()}.csv"
        if not path.exists():
            return []

        frame = pd.read_csv(path)
        frame.columns = [column.strip().lower() for column in frame.columns]
        frame = frame.tail(lookback_days)

        return [
            Candle(
                symbol=symbol.upper(),
                date=pd.to_datetime(row["date"]).date(),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=int(row["volume"]),
            )
            for _, row in frame.iterrows()
        ]

