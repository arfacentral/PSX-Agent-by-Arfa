from psx_agent.config import get_settings
from psx_agent.providers.base import MarketDataProvider
from psx_agent.providers.capitalstake import CapitalStakeProvider
from psx_agent.providers.csv_provider import CsvProvider
from psx_agent.providers.demo import DemoProvider
from psx_agent.providers.psx_dps import PsxDpsProvider
from psx_agent.providers.psx_terminal import PsxTerminalProvider


def get_provider() -> MarketDataProvider:
    settings = get_settings()
    if settings.data_provider == "psxterminal":
        return PsxTerminalProvider(
            base_url=settings.psxterminal_base_url,
            market_type=settings.psxterminal_market_type,
            quote_cache_ttl_seconds=settings.psxterminal_quote_cache_ttl_seconds,
            kline_cache_ttl_seconds=settings.psxterminal_kline_cache_ttl_seconds,
            max_rest_quote_symbols=settings.psxterminal_max_rest_quote_symbols,
            rest_pause_seconds=settings.psxterminal_rest_pause_seconds,
            use_tick_endpoint=settings.psxterminal_use_tick_endpoint,
        )
    if settings.data_provider == "capitalstake":
        return CapitalStakeProvider(
            api_token=settings.capitalstake_api_token,
            base_url=settings.capitalstake_base_url,
            quote_cache_ttl_seconds=settings.capitalstake_quote_cache_ttl_seconds,
            eod_cache_ttl_seconds=settings.capitalstake_eod_cache_ttl_seconds,
        )
    if settings.data_provider == "csv":
        return CsvProvider()
    if settings.data_provider == "psx_dps":
        return PsxDpsProvider(
            base_url=settings.psx_dps_base_url,
            cache_ttl_seconds=settings.psx_dps_cache_ttl_seconds,
        )
    return DemoProvider()
