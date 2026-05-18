from abc import ABC, abstractmethod

from psx_agent.models import Candle


class MarketDataProvider(ABC):
    @abstractmethod
    def get_history(self, symbol: str, lookback_days: int = 120) -> list[Candle]:
        raise NotImplementedError

