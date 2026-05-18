import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value not in (None, "") else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value not in (None, "") else default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass
class Settings:
    data_provider: str = "psxterminal"
    psxterminal_base_url: str = "https://psxterminal.com"
    psxterminal_market_type: str = "REG"
    psxterminal_quote_cache_ttl_seconds: int = 15
    psxterminal_kline_cache_ttl_seconds: int = 60 * 60 * 8
    psxterminal_max_rest_quote_symbols: int = 20
    psxterminal_rest_pause_seconds: float = 0.1
    psxterminal_use_tick_endpoint: bool = False
    capitalstake_base_url: str = "https://csapis.com"
    capitalstake_api_token: str = ""
    capitalstake_quote_cache_ttl_seconds: int = 15
    capitalstake_eod_cache_ttl_seconds: int = 60 * 60 * 8
    psx_dps_base_url: str = "https://dps.psx.com.pk"
    psx_dps_cache_ttl_seconds: int = 60 * 60 * 8
    watchlist: str = (
        "HBL,UBL,MCB,BAHL,MEBL,OGDC,PPL,POL,PSO,HUBC,"
        "LUCK,ENGRO,FFC,EFERT,SYS,AIRLINK,TRG,MLCF,DGKC,UNITY"
    )
    report_timezone: str = "Asia/Karachi"
    max_recommendations: int = 20
    max_analysis_symbols: int = 0
    risk_per_trade_pct: float = 1.0
    min_avg_volume: int = 500_000

    @property
    def symbols(self) -> list[str]:
        return [symbol.strip().upper() for symbol in self.watchlist.split(",") if symbol.strip()]


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        data_provider=os.getenv("DATA_PROVIDER", Settings.data_provider),
        psxterminal_base_url=os.getenv("PSXTERMINAL_BASE_URL", Settings.psxterminal_base_url),
        psxterminal_market_type=os.getenv("PSXTERMINAL_MARKET_TYPE", Settings.psxterminal_market_type),
        psxterminal_quote_cache_ttl_seconds=_env_int(
            "PSXTERMINAL_QUOTE_CACHE_TTL_SECONDS", Settings.psxterminal_quote_cache_ttl_seconds
        ),
        psxterminal_kline_cache_ttl_seconds=_env_int(
            "PSXTERMINAL_KLINE_CACHE_TTL_SECONDS", Settings.psxterminal_kline_cache_ttl_seconds
        ),
        psxterminal_max_rest_quote_symbols=_env_int(
            "PSXTERMINAL_MAX_REST_QUOTE_SYMBOLS", Settings.psxterminal_max_rest_quote_symbols
        ),
        psxterminal_rest_pause_seconds=_env_float(
            "PSXTERMINAL_REST_PAUSE_SECONDS", Settings.psxterminal_rest_pause_seconds
        ),
        psxterminal_use_tick_endpoint=_env_bool(
            "PSXTERMINAL_USE_TICK_ENDPOINT", Settings.psxterminal_use_tick_endpoint
        ),
        capitalstake_base_url=os.getenv("CAPITALSTAKE_BASE_URL", Settings.capitalstake_base_url),
        capitalstake_api_token=os.getenv("CAPITALSTAKE_API_TOKEN", Settings.capitalstake_api_token),
        capitalstake_quote_cache_ttl_seconds=_env_int(
            "CAPITALSTAKE_QUOTE_CACHE_TTL_SECONDS", Settings.capitalstake_quote_cache_ttl_seconds
        ),
        capitalstake_eod_cache_ttl_seconds=_env_int(
            "CAPITALSTAKE_EOD_CACHE_TTL_SECONDS", Settings.capitalstake_eod_cache_ttl_seconds
        ),
        psx_dps_base_url=os.getenv("PSX_DPS_BASE_URL", Settings.psx_dps_base_url),
        psx_dps_cache_ttl_seconds=_env_int("PSX_DPS_CACHE_TTL_SECONDS", Settings.psx_dps_cache_ttl_seconds),
        watchlist=os.getenv("WATCHLIST", Settings.watchlist),
        report_timezone=os.getenv("REPORT_TIMEZONE", Settings.report_timezone),
        max_recommendations=_env_int("MAX_RECOMMENDATIONS", Settings.max_recommendations),
        max_analysis_symbols=_env_int("MAX_ANALYSIS_SYMBOLS", Settings.max_analysis_symbols),
        risk_per_trade_pct=_env_float("RISK_PER_TRADE_PCT", Settings.risk_per_trade_pct),
        min_avg_volume=_env_int("MIN_AVG_VOLUME", Settings.min_avg_volume),
    )
