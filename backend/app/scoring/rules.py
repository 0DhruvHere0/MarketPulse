import numpy as np
from backend.app.constants import (
    OBV_EMA_PERIOD, ROC_PERIOD,
    CHOP_TRENDING_THRESHOLD, CHOP_CHOPPY_THRESHOLD,
)
def score_rsi(rsi_value: float) -> tuple[float, str, str]:
    if rsi_value is None or np.isnan(rsi_value):
        return 0.0, "Neutral", "RSI data unavailable"
    if rsi_value > 70:
        score = -1 * min((rsi_value - 70) / 15, 1)
    elif rsi_value < 30:
        score = min((30 - rsi_value) / 15, 1)
    else:
        score = (50 - rsi_value) / 20
    label = "Bearish" if score < -0.15 else "Bullish" if score > 0.15 else "Neutral"
    if rsi_value > 70:
        explanation = f"RSI at {rsi_value:.1f} indicates overbought conditions"
    elif rsi_value < 30:
        explanation = f"RSI at {rsi_value:.1f} indicates oversold conditions"
    else:
        explanation = f"RSI at {rsi_value:.1f} is in neutral territory"
    return score, label, explanation
def score_macd(macd_line: float, signal_line: float, histogram_current: float, histogram_prev: float) -> tuple[float, str, str]:
    if any(v is None or np.isnan(v) for v in [macd_line, signal_line, histogram_current, histogram_prev]):
        return 0.0, "Neutral", "MACD data unavailable"
    base = 1.0 if macd_line > signal_line else -1.0
    widening = abs(histogram_current) > abs(histogram_prev)
    score = base * (0.8 if widening else 0.4)
    label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
    trend = "bullish" if macd_line > signal_line else "bearish"
    hist_desc = "widening" if widening else "narrowing"
    explanation = f"MACD {trend}, histogram {hist_desc} (MACD: {macd_line:.2f}, Signal: {signal_line:.2f})"
    return score, label, explanation
def score_stochastic(k_value: float, d_value: float, k_prev: float = None, d_prev: float = None) -> tuple[float, str, str]:
    if k_value is None or np.isnan(k_value):
        return 0.0, "Neutral", "Stochastic data unavailable"
    if k_value > 80:
        score = -1 * min((k_value - 80) / 15, 1)
    elif k_value < 20:
        score = min((20 - k_value) / 15, 1)
    else:
        score = (50 - k_value) / 30
    if k_prev is not None and d_prev is not None and not np.isnan(k_prev) and not np.isnan(d_prev):
        if k_prev < d_prev and k_value > d_value and k_value < 20:
            score = min(score + 0.3, 1)
    score = max(-1, min(1, score))
    label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
    if k_value > 80:
        explanation = f"Stochastic %K at {k_value:.1f} indicates overbought conditions"
    elif k_value < 20:
        explanation = f"Stochastic %K at {k_value:.1f} indicates oversold conditions"
    else:
        explanation = f"Stochastic %K at {k_value:.1f} is in neutral territory"
    return score, label, explanation
def score_adx(adx_value: float) -> tuple[str, str]:
    if adx_value is None or np.isnan(adx_value):
        return "unknown", "ADX data unavailable"
    if adx_value > 25:
        trend_strength = "strong"
    elif adx_value < 20:
        trend_strength = "weak"
    else:
        trend_strength = "moderate"
    explanation = f"ADX at {adx_value:.1f} indicates {trend_strength} trend"
    return trend_strength, explanation
def score_moving_averages(price: float, ema50: float, ema200: float, golden_cross: bool, death_cross: bool) -> tuple[float, str, str]:
    if any(v is None or np.isnan(v) for v in [price, ema50, ema200]):
        return 0.0, "Neutral", "Moving average data unavailable"
    if price > ema50 and price > ema200:
        score = 0.7
    elif price < ema50 and price < ema200:
        score = -0.7
    else:
        score = 0.2 if price > ema200 else -0.2
    if golden_cross:
        score = min(score + 0.3, 1)
    if death_cross:
        score = max(score - 0.3, -1)
    label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
    position = []
    if price > ema50:
        position.append("above EMA50")
    else:
        position.append("below EMA50")
    if price > ema200:
        position.append("above EMA200")
    else:
        position.append("below EMA200")
    cross_info = ""
    if golden_cross:
        cross_info = " Golden cross detected recently."
    elif death_cross:
        cross_info = " Death cross detected recently."
    explanation = f"Price is {', '.join(position)}.{cross_info}"
    return score, label, explanation
def score_bollinger(percent_b: float, trend_strength: str) -> tuple[float, str, str]:
    if percent_b is None or np.isnan(percent_b):
        return 0.0, "Neutral", "Bollinger Bands data unavailable"
    if percent_b > 1.0:
        score = -0.6
    elif percent_b < 0.0:
        score = 0.6
    elif percent_b > 0.8:
        score = -0.3
    elif percent_b < 0.2:
        score = 0.3
    else:
        score = 0.0
    if trend_strength == "strong":
        score *= 0.5
    label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
    if percent_b > 1.0:
        explanation = f"Price above upper Bollinger Band (%B: {percent_b:.2f})"
    elif percent_b < 0.0:
        explanation = f"Price below lower Bollinger Band (%B: {percent_b:.2f})"
    elif percent_b > 0.8:
        explanation = f"Price near upper Bollinger Band (%B: {percent_b:.2f})"
    elif percent_b < 0.2:
        explanation = f"Price near lower Bollinger Band (%B: {percent_b:.2f})"
    else:
        explanation = f"Price within Bollinger Bands (%B: {percent_b:.2f})"
    if trend_strength == "strong":
        explanation += " (dampened due to strong trend)"
    return score, label, explanation
def score_vwap(price: float, vwap_value: float, is_approximation: bool = True) -> tuple[float, str, str]:
    if price is None or vwap_value is None or np.isnan(price) or np.isnan(vwap_value):
        return 0.0, "Neutral", "VWAP data unavailable"
    score = 0.4 if price > vwap_value else -0.4
    label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
    approx_note = " (approx.)" if is_approximation else ""
    explanation = f"Price {'above' if price > vwap_value else 'below'} VWAP{approx_note} (Price: {price:.2f}, VWAP: {vwap_value:.2f})"
    return score, label, explanation
def score_cci(cci_value: float) -> tuple[float, str, str]:
    if cci_value is None or np.isnan(cci_value):
        return 0.0, "Neutral", "CCI data unavailable"
    if cci_value > 100:
        score = -1 * min((cci_value - 100) / 100, 1)
    elif cci_value < -100:
        score = min((-100 - cci_value) / 100, 1)
    else:
        score = cci_value / 250
    score = max(-1, min(1, score))
    label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
    if cci_value > 100:
        explanation = f"CCI at {cci_value:.0f} indicates overbought (above +100)"
    elif cci_value < -100:
        explanation = f"CCI at {cci_value:.0f} indicates oversold (below -100)"
    else:
        explanation = f"CCI at {cci_value:.0f} is within normal range (-100 to +100)"
    return score, label, explanation
def score_williams_r(wr_value: float) -> tuple[float, str, str]:
    if wr_value is None or np.isnan(wr_value):
        return 0.0, "Neutral", "Williams %R data unavailable"
    if wr_value > -20:
        score = -1 * min((wr_value - (-20)) / 15, 1)
    elif wr_value < -80:
        score = min((-80 - wr_value) / 15, 1)
    else:
        score = (-50 - wr_value) / 30
    score = max(-1, min(1, score))
    label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
    if wr_value > -20:
        explanation = f"Williams %R at {wr_value:.1f} indicates overbought (above -20)"
    elif wr_value < -80:
        explanation = f"Williams %R at {wr_value:.1f} indicates oversold (below -80)"
    else:
        explanation = f"Williams %R at {wr_value:.1f} is in neutral territory"
    return score, label, explanation
def score_obv(obv_value: float, obv_ema: float) -> tuple[float, str, str]:
    if obv_value is None or obv_ema is None or np.isnan(obv_value) or np.isnan(obv_ema):
        return 0.0, "Neutral", "OBV data unavailable"
    score = 0.5 if obv_value > obv_ema else -0.5
    label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
    direction = "accumulation" if obv_value > obv_ema else "distribution"
    explanation = f"OBV {'above' if obv_value > obv_ema else 'below'} its EMA{OBV_EMA_PERIOD} — net {direction} (OBV: {obv_value:,.0f})"
    return score, label, explanation
def score_mfi(mfi_value: float) -> tuple[float, str, str]:
    if mfi_value is None or np.isnan(mfi_value):
        return 0.0, "Neutral", "MFI data unavailable"
    if mfi_value > 80:
        score = -1 * min((mfi_value - 80) / 10, 1)
    elif mfi_value < 20:
        score = min((20 - mfi_value) / 10, 1)
    else:
        score = (50 - mfi_value) / 25
    score = max(-1, min(1, score))
    label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
    if mfi_value > 80:
        explanation = f"MFI at {mfi_value:.1f} indicates overbought with heavy money inflow"
    elif mfi_value < 20:
        explanation = f"MFI at {mfi_value:.1f} indicates oversold with money outflow"
    else:
        explanation = f"MFI at {mfi_value:.1f} is in neutral territory"
    return score, label, explanation
def score_aroon(aroon_up: float, aroon_down: float) -> tuple[float, str, str]:
    if aroon_up is None or aroon_down is None or np.isnan(aroon_up) or np.isnan(aroon_down):
        return 0.0, "Neutral", "Aroon data unavailable"
    osc = aroon_up - aroon_down
    score = max(-1, min(1, osc / 100))
    if aroon_up > 70 and aroon_down < 30:
        label = "Bullish"
        explanation = f"Aroon Up {aroon_up:.0f} vs Down {aroon_down:.0f} — fresh highs, strong uptrend"
    elif aroon_down > 70 and aroon_up < 30:
        label = "Bearish"
        explanation = f"Aroon Up {aroon_up:.0f} vs Down {aroon_down:.0f} — fresh lows, strong downtrend"
    else:
        label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
        explanation = f"Aroon Up {aroon_up:.0f} vs Down {aroon_down:.0f} — no dominant trend direction"
    return score, label, explanation
def score_roc(roc_value: float) -> tuple[float, str, str]:
    if roc_value is None or np.isnan(roc_value):
        return 0.0, "Neutral", "ROC data unavailable"
    score = max(-1, min(1, roc_value / 5))
    label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
    if roc_value > 5:
        explanation = f"ROC at {roc_value:.1f}% shows strong upward momentum over {ROC_PERIOD} days"
    elif roc_value < -5:
        explanation = f"ROC at {roc_value:.1f}% shows strong downward momentum over {ROC_PERIOD} days"
    else:
        explanation = f"ROC at {roc_value:.1f}% is moderate over {ROC_PERIOD} days"
    return score, label, explanation
def score_trix(trix_value: float, trix_signal: float) -> tuple[float, str, str]:
    if trix_value is None or trix_signal is None or np.isnan(trix_value) or np.isnan(trix_signal):
        return 0.0, "Neutral", "TRIX data unavailable"
    base = 1.0 if trix_value > trix_signal else -1.0
    magnitude = min(abs(trix_value - trix_signal) / 5, 1)
    score = base * (0.3 + 0.7 * magnitude)
    label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
    direction = "above" if trix_value > trix_signal else "below"
    explanation = f"TRIX {direction} its signal line (TRIX: {trix_value:.1f}, Signal: {trix_signal:.1f}) — {'bullish' if base > 0 else 'bearish'} smoothed momentum"
    return score, label, explanation
def score_cmf(cmf_value: float) -> tuple[float, str, str]:
    if cmf_value is None or np.isnan(cmf_value):
        return 0.0, "Neutral", "CMF data unavailable"
    if cmf_value > 0.10:
        score = min(cmf_value / 0.25, 1)
    elif cmf_value < -0.10:
        score = max(cmf_value / 0.25, -1)
    else:
        score = cmf_value / 0.10 * 0.2
    label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
    if cmf_value > 0.10:
        explanation = f"CMF at {cmf_value:+.2f} — net accumulation (buying pressure) over 21 days"
    elif cmf_value < -0.10:
        explanation = f"CMF at {cmf_value:+.2f} — net distribution (selling pressure) over 21 days"
    else:
        explanation = f"CMF at {cmf_value:+.2f} — balanced buying and selling pressure"
    return score, label, explanation
def score_chop(chop_value: float) -> tuple[str, str]:
    if chop_value is None or np.isnan(chop_value):
        return "unknown", "Choppiness data unavailable"
    if chop_value > CHOP_CHOPPY_THRESHOLD:
        regime = "choppy"
    elif chop_value < CHOP_TRENDING_THRESHOLD:
        regime = "trending"
    else:
        regime = "transitional"
    explanation = f"Choppiness Index at {chop_value:.1f} — market is {regime}"
    return regime, explanation
def score_stoch_rsi(k_value: float, d_value: float, k_prev: float = None, d_prev: float = None) -> tuple[float, str, str]:
    if k_value is None or np.isnan(k_value):
        return 0.0, "Neutral", "Stochastic RSI data unavailable"
    if k_value > 80:
        score = -1 * min((k_value - 80) / 15, 1)
    elif k_value < 20:
        score = min((20 - k_value) / 15, 1)
    else:
        score = (50 - k_value) / 30
    if (k_prev is not None and d_prev is not None
            and not np.isnan(k_prev) and not np.isnan(d_prev)
            and k_prev < d_prev and k_value > d_value and k_value < 20):
        score = min(score + 0.3, 1)
    score = max(-1, min(1, score))
    label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
    if k_value > 80:
        explanation = f"StochRSI %K at {k_value:.0f} — overbought (hyper-sensitive momentum extreme)"
    elif k_value < 20:
        explanation = f"StochRSI %K at {k_value:.0f} — oversold (hyper-sensitive momentum extreme)"
    else:
        explanation = f"StochRSI %K at {k_value:.0f} — within normal band"
    return score, label, explanation