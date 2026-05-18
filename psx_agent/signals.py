import pandas as pd

from psx_agent.models import Action, Candle, Recommendation


def _frame(candles: list[Candle]) -> pd.DataFrame:
    frame = pd.DataFrame([candle.model_dump() for candle in candles])
    return frame.sort_values("date").reset_index(drop=True)


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, pd.NA)
    return (100 - (100 / (1 + rs))).fillna(50)


def _atr(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    previous_close = frame["close"].shift(1)
    ranges = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous_close).abs(),
            (frame["low"] - previous_close).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1).rolling(period).mean()


def recommend(symbol: str, candles: list[Candle], min_avg_volume: int) -> Recommendation | None:
    if len(candles) < 60:
        return None

    frame = _frame(candles)
    frame["sma20"] = frame["close"].rolling(20).mean()
    frame["sma50"] = frame["close"].rolling(50).mean()
    frame["rsi"] = _rsi(frame["close"])
    frame["atr"] = _atr(frame)
    frame["avg_volume20"] = frame["volume"].rolling(20).mean()
    latest = frame.iloc[-1]

    last_close = float(latest["close"])
    atr = float(latest["atr"]) if pd.notna(latest["atr"]) else max(last_close * 0.03, 0.01)
    avg_volume = float(latest["avg_volume20"]) if pd.notna(latest["avg_volume20"]) else 0
    rsi = float(latest["rsi"]) if pd.notna(latest["rsi"]) else 50
    sma20 = float(latest["sma20"]) if pd.notna(latest["sma20"]) else last_close
    sma50 = float(latest["sma50"]) if pd.notna(latest["sma50"]) else last_close

    reasons: list[str] = []
    score = 0.0

    if last_close > sma20 > sma50:
        score += 35
        reasons.append("Price is above 20-day and 50-day trend lines.")
    elif last_close > sma50:
        score += 20
        reasons.append("Price is holding above the 50-day trend line.")
    else:
        reasons.append("Price is below key trend lines.")

    if 45 <= rsi <= 68:
        score += 25
        reasons.append("Momentum is constructive without being overheated.")
    elif 68 < rsi <= 75:
        score += 12
        reasons.append("Momentum is strong but close to overheated.")
    else:
        reasons.append("Momentum is weak or extended.")

    if avg_volume >= min_avg_volume:
        score += 20
        reasons.append("Average volume passes the liquidity filter.")
    else:
        reasons.append("Average volume is below the liquidity filter.")

    recent_high = float(frame["high"].tail(20).max())
    breakout_distance = (recent_high - last_close) / last_close
    if 0 <= breakout_distance <= 0.04:
        score += 20
        reasons.append("Price is near a 20-day breakout area.")
    elif last_close >= recent_high:
        score += 18
        reasons.append("Price is already challenging the recent high.")
    else:
        reasons.append("Price is not close to a clean breakout area.")

    entry_low = last_close * 0.995
    entry_high = min(recent_high * 1.005, last_close + atr * 0.65)
    stop_loss = max(0.01, min(last_close - atr * 1.2, sma20 * 0.985))
    target_1 = entry_high + (entry_high - stop_loss) * 1.5
    target_2 = entry_high + (entry_high - stop_loss) * 2.4
    risk_reward = (target_1 - entry_high) / max(entry_high - stop_loss, 0.01)

    if score >= 72 and avg_volume >= min_avg_volume:
        action = Action.buy_watch
        confidence = "Medium"
    elif score >= 50:
        action = Action.wait
        confidence = "Low"
    else:
        action = Action.avoid
        confidence = "Low"

    return Recommendation(
        symbol=symbol,
        action=action,
        score=round(score, 1),
        last_close=round(last_close, 2),
        entry_low=round(entry_low, 2),
        entry_high=round(entry_high, 2),
        stop_loss=round(stop_loss, 2),
        target_1=round(target_1, 2),
        target_2=round(target_2, 2),
        risk_reward=round(risk_reward, 2),
        confidence=confidence,
        reasons=reasons,
        invalidation="Avoid or exit if price closes below stop-loss or liquidity dries up.",
    )
