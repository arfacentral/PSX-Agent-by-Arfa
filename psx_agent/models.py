from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import date
from enum import Enum
from typing import Any


class Serializable:
    def model_dump(self) -> dict[str, Any]:
        def convert(value: Any) -> Any:
            if isinstance(value, Enum):
                return value.value
            if is_dataclass(value):
                return {item.name: convert(getattr(value, item.name)) for item in fields(value)}
            if isinstance(value, list):
                return [convert(item) for item in value]
            if isinstance(value, dict):
                return {key: convert(item) for key, item in value.items()}
            if isinstance(value, date):
                return value.isoformat()
            return value

        return convert(self)


@dataclass
class Candle(Serializable):
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class Quote(Serializable):
    symbol: str
    name: str | None = None
    sector: str | None = None
    date: str | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None
    change: float | None = None
    change_percent: float | None = None
    bid_price: float | None = None
    bid_volume: int | None = None
    ask_price: float | None = None
    ask_volume: int | None = None
    high52: float | None = None
    low52: float | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None
    dividend_yield: float | None = None
    year_change: float | None = None
    listed_in: str | None = None
    non_compliant: bool | None = None


class Action(str, Enum):
    buy_watch = "BUY WATCH"
    wait = "WAIT"
    avoid = "AVOID"


@dataclass
class Recommendation(Serializable):
    symbol: str
    action: Action
    score: float
    last_close: float
    entry_low: float
    entry_high: float
    stop_loss: float
    target_1: float
    target_2: float
    risk_reward: float
    confidence: str
    reasons: list[str]
    invalidation: str


@dataclass
class MorningReport(Serializable):
    as_of: str
    market_context: str
    quotes: list[Quote]
    recommendations: list[Recommendation]
    notes: list[str]
