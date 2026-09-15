from backend.app.constants import (
    TREND_BASE_WEIGHT, MOMENTUM_BASE_WEIGHT, VOLATILITY_BASE_WEIGHT,
    ADX_WEAK_THRESHOLD, ADX_STRONG_THRESHOLD,
    ADX_WEAK_TREND_MULTIPLIER, ADX_STRONG_TREND_MULTIPLIER,
    ADX_STRONG_BOLLINGER_DAMPEN,
    BUY_THRESHOLD, SELL_THRESHOLD,
    CHOP_CHOPPY_THRESHOLD,
)
def aggregate_scores(
    rsi_score: float,
    macd_score: float,
    stochastic_score: float,
    ema_score: float,
    bollinger_score: float,
    trend_strength: str,
    cci_score: float = 0.0,
    williams_r_score: float = 0.0,
    mfi_score: float = 0.0,
    obv_score: float = 0.0,
    aroon_score: float = 0.0,
    roc_score: float = 0.0,
    trix_score: float = 0.0,
    cmf_score: float = 0.0,
    stoch_rsi_score: float = 0.0,
    chop_regime: str = "unknown"
) -> dict:
    trend_scores = [macd_score, ema_score, obv_score, aroon_score, cmf_score]
    momentum_scores = [rsi_score, stochastic_score, cci_score, williams_r_score, mfi_score, roc_score, trix_score, stoch_rsi_score]
    volatility_scores = [bollinger_score]
    trend_base_weight = TREND_BASE_WEIGHT
    momentum_base_weight = MOMENTUM_BASE_WEIGHT
    volatility_base_weight = VOLATILITY_BASE_WEIGHT
    if trend_strength == "weak":
        trend_weight = trend_base_weight * ADX_WEAK_TREND_MULTIPLIER
        removed = trend_base_weight - trend_weight
        momentum_weight = momentum_base_weight + removed
        volatility_weight = volatility_base_weight
    elif trend_strength == "strong":
        trend_weight = min(trend_base_weight * ADX_STRONG_TREND_MULTIPLIER, 0.6)
        total_base = trend_base_weight + momentum_base_weight + volatility_base_weight
        excess = trend_weight - trend_base_weight
        remaining = momentum_base_weight + volatility_base_weight
        momentum_weight = momentum_base_weight - (excess * momentum_base_weight / remaining)
        volatility_weight = volatility_base_weight - (excess * volatility_base_weight / remaining)
    else:
        trend_weight = trend_base_weight
        momentum_weight = momentum_base_weight
        volatility_weight = volatility_base_weight
    if chop_regime == "choppy":
        removed = trend_weight * 0.5
        trend_weight -= removed
        momentum_weight += removed
    total_weight = trend_weight + momentum_weight + volatility_weight
    trend_weight /= total_weight
    momentum_weight /= total_weight
    volatility_weight /= total_weight
    trend_score = sum(trend_scores) / len(trend_scores) if trend_scores else 0
    momentum_score = sum(momentum_scores) / len(momentum_scores) if momentum_scores else 0
    volatility_score = sum(volatility_scores) / len(volatility_scores) if volatility_scores else 0
    overall_score = (
        trend_score * trend_weight +
        momentum_score * momentum_weight +
        volatility_score * volatility_weight
    )
    overall_score = max(-1, min(1, overall_score))
    bullish_pct = (overall_score + 1) / 2 * 100
    bearish_pct = 100 - bullish_pct
    if bullish_pct > BUY_THRESHOLD:
        verdict = "BUY"
    elif bullish_pct < SELL_THRESHOLD:
        verdict = "SELL"
    else:
        verdict = "HOLD / NEUTRAL"
    return {
        "overall_score": overall_score,
        "bullish_pct": round(bullish_pct, 1),
        "bearish_pct": round(bearish_pct, 1),
        "verdict": verdict,
        "trend_strength": trend_strength,
        "chop_regime": chop_regime,
        "weights": {
            "trend": round(trend_weight, 3),
            "momentum": round(momentum_weight, 3),
            "volatility": round(volatility_weight, 3),
        },
        "category_scores": {
            "trend": round(trend_score, 3),
            "momentum": round(momentum_score, 3),
            "volatility": round(volatility_score, 3),
        }
    }