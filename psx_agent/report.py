from datetime import datetime
from zoneinfo import ZoneInfo

from psx_agent.config import get_settings
from psx_agent.models import Action, MorningReport, Quote, Recommendation
from psx_agent.providers.factory import get_provider
from psx_agent.signals import recommend


def build_morning_report() -> MorningReport:
    settings = get_settings()
    provider = get_provider()
    quotes: list[Quote] = []
    recommendations = []
    skipped: list[str] = []
    notes = [
        "Use position sizing before placing any order.",
        "This is not financial advice; verify levels against your broker terminal before trading.",
        "Fast mode uses PSX Terminal fundamentals/live price fields only; historical candle confirmation is off.",
    ]

    try:
        if hasattr(provider, "get_quotes"):
            quote_symbols = None if settings.symbols == ["ALL"] else settings.symbols
            quotes = provider.get_quotes(quote_symbols)  # type: ignore[attr-defined]
    except Exception as exc:
        notes.append(f"Live quote table could not be loaded ({exc}).")

    quick_recommendations = [_recommend_from_quote(quote, settings.min_avg_volume) for quote in quotes if quote.close]
    quick_by_symbol = {item.symbol: item for item in quick_recommendations}
    analysis_symbols = _analysis_symbols(settings.symbols, quotes, settings.max_analysis_symbols)

    for symbol in analysis_symbols:
        try:
            candles = provider.get_history(symbol)
            idea = recommend(symbol, candles, settings.min_avg_volume)
        except Exception as exc:
            skipped.append(f"{symbol}: {exc}")
            continue
        if idea:
            quick_by_symbol[symbol] = idea

    if skipped:
        notes.append(f"Historical candle confirmation skipped for {len(skipped)} symbol(s).")

    recommendations = list(quick_by_symbol.values())
    recommendations.sort(key=lambda item: item.score, reverse=True)
    buy_watch = [item for item in recommendations if item.action == Action.buy_watch]
    other = [item for item in recommendations if item.action != Action.buy_watch]
    selected = (buy_watch + other)[: settings.max_recommendations]

    now = datetime.now(ZoneInfo(settings.report_timezone)).strftime("%Y-%m-%d %H:%M %Z")
    context = "Selective risk-on" if buy_watch else "Cautious: no high-quality long setups found"

    return MorningReport(
        as_of=now,
        market_context=context,
        quotes=quotes,
        recommendations=selected,
        notes=notes,
    )


def _analysis_symbols(configured_symbols: list[str], quotes: list[Quote], limit: int) -> list[str]:
    if configured_symbols == ["ALL"]:
        liquid_quotes = sorted(quotes, key=lambda quote: quote.volume or 0, reverse=True)
        return [quote.symbol for quote in liquid_quotes[:limit]]
    return configured_symbols[:limit]


def _recommend_from_quote(quote: Quote, min_avg_volume: int) -> Recommendation:
    close = quote.close or 0
    high = quote.high
    low = quote.low
    volume = quote.volume or 0
    change_percent = quote.change_percent or 0
    year_change = quote.year_change or 0
    pe_ratio = quote.pe_ratio
    dividend_yield = quote.dividend_yield

    score = 0.0
    reasons = []
    if volume >= min_avg_volume:
        score += 30
        reasons.append("Live volume passes the liquidity filter.")
    else:
        reasons.append("Live volume is below the liquidity filter.")

    if change_percent > 0:
        score += min(30, 12 + change_percent * 4)
        reasons.append("Price is positive on the live session.")
    elif -1 <= change_percent < 0:
        score += 8
        reasons.append("Price is slightly negative on the live session.")
    elif change_percent < -3:
        reasons.append("Price is sharply negative on the live session.")
    elif change_percent < 0:
        reasons.append("Price is negative on the live session.")
    else:
        score += 8
        reasons.append("Price is flat on the live session.")

    has_range = high is not None and low is not None and high > low
    if has_range:
        day_range = max(high - low, close * 0.01, 0.01)
        close_position = (close - low) / day_range
        if close_position >= 0.7:
            score += 25
            reasons.append("Price is near the upper part of the available range.")
        elif close_position >= 0.45:
            score += 12
            reasons.append("Price is holding the middle of the available range.")
        else:
            reasons.append("Price is weak inside the available range.")
    else:
        day_range = max(close * max(abs(change_percent) / 100, 0.015), 0.01)
        reasons.append("No intraday range was provided; scoring uses price change, volume, and fundamentals.")

    if pe_ratio is not None and 0 < pe_ratio <= 12:
        score += 10
        reasons.append("P/E is in a reasonable screening range.")

    if dividend_yield is not None and dividend_yield >= 5:
        score += 10
        reasons.append("Dividend yield passes the income screen.")

    if year_change > 20:
        score += 8
        reasons.append("One-year trend is positive.")
    elif year_change < -20:
        reasons.append("One-year trend is weak.")

    if quote.bid_price and quote.ask_price and quote.ask_price > quote.bid_price:
        spread_pct = ((quote.ask_price - quote.bid_price) / close) * 100 if close else 100
        if spread_pct <= 1:
            score += 15
            reasons.append("Bid/ask spread looks tradeable.")
        else:
            reasons.append("Bid/ask spread is wide.")

    stop_loss = max(0.01, close - (day_range * 0.8))
    entry_low = close * 0.995
    entry_high = close * 1.005
    target_1 = entry_high + ((entry_high - stop_loss) * 1.5)
    target_2 = entry_high + ((entry_high - stop_loss) * 2.4)
    risk_reward = (target_1 - entry_high) / max(entry_high - stop_loss, 0.01)

    if score >= 70 and change_percent >= 0:
        action = Action.buy_watch
        confidence = "Screening only"
    elif score >= 45:
        action = Action.wait
        confidence = "Screening only"
    else:
        action = Action.avoid
        confidence = "Screening only"

    return Recommendation(
        symbol=quote.symbol,
        action=action,
        score=round(min(score, 100), 1),
        last_close=round(close, 2),
        entry_low=round(entry_low, 2),
        entry_high=round(entry_high, 2),
        stop_loss=round(stop_loss, 2),
        target_1=round(target_1, 2),
        target_2=round(target_2, 2),
        risk_reward=round(risk_reward, 2),
        confidence=confidence,
        reasons=reasons,
        invalidation="Treat as a screening idea only; confirm price, spread, and volume in a broker terminal before trading.",
    )
