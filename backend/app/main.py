from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import numpy as np
from backend.app.data_fetch import fetch_ohlcv, get_company_name, get_currency, DataFetchError
from backend.app.indicators import (
    compute_rsi, compute_macd, compute_stochastic, compute_adx,
    compute_emas, detect_crossovers, compute_bollinger_bands,
    compute_pivot_points, compute_vwap,
    compute_cci, compute_williams_r, compute_obv, compute_mfi,
    compute_aroon, compute_roc, compute_trix, compute_cmf,
    compute_chop, compute_stoch_rsi
)
from backend.app.scoring import (
    score_rsi, score_macd, score_stochastic, score_adx,
    score_moving_averages, score_bollinger, score_vwap,
    score_cci, score_williams_r, score_obv, score_mfi,
    score_aroon, score_roc, score_trix, score_cmf,
    score_chop, score_stoch_rsi
)
from backend.app.aggregation import aggregate_scores
from backend.app.search import search_symbols
from backend.app.backtest import run_backtest
from backend.app.forecast import run_forecast
app = FastAPI(title="MarketPulse API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class SearchResult(BaseModel):
    name: str
    exchange: str
    ticker: str
    type: str = "stock"
    currency: Optional[str] = None
class IndicatorResult(BaseModel):
    value: Optional[float] = None
    score: Optional[float] = None
    label: Optional[str] = None
    explanation: Optional[str] = None
    macd_line: Optional[float] = None
    signal_line: Optional[float] = None
    histogram: Optional[float] = None
    percent_b: Optional[float] = None
    upper: Optional[float] = None
    middle: Optional[float] = None
    lower: Optional[float] = None
    trend_strength: Optional[str] = None
    ema50: Optional[float] = None
    ema200: Optional[float] = None
    position: Optional[str] = None
    nearest_level: Optional[str] = None
    is_approximation: Optional[bool] = None
    k: Optional[float] = None
    d: Optional[float] = None
class OverallResult(BaseModel):
    bullish_pct: float
    bearish_pct: float
    verdict: str
    trend_strength: str
    chop_regime: Optional[str] = None
class AnalyzeResponse(BaseModel):
    ticker: str
    company_name: str
    currency: Optional[str] = None
    current_price: float
    day_change_pct: float
    as_of: str
    overall: OverallResult
    indicators: dict
@app.get("/api/search")
async def search(q: str = Query(..., min_length=1)):
    results = search_symbols(q)
    return {"results": results}
@app.get("/api/analyze", response_model=AnalyzeResponse)
async def analyze(ticker: str = Query(..., min_length=1)):
    try:
        df = fetch_ohlcv(ticker)
    except DataFetchError as e:
        raise HTTPException(status_code=400, detail={"error": e.message, "type": e.error_type})
    company_name = get_company_name(ticker)
    currency = get_currency(ticker)
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']
    open_ = df['Open']
    current_price = float(close.iloc[-1])
    prev_close = float(close.iloc[-2]) if len(close) > 1 else current_price
    day_change_pct = ((current_price - prev_close) / prev_close) * 100
    as_of = df.index[-1].strftime("%Y-%m-%d")
    rsi_series = compute_rsi(close)
    rsi_value = float(rsi_series.iloc[-1]) if not rsi_series.empty else None
    macd_line_series, signal_line_series, histogram_series = compute_macd(close)
    macd_line = float(macd_line_series.iloc[-1]) if not macd_line_series.empty else None
    signal_line = float(signal_line_series.iloc[-1]) if not signal_line_series.empty else None
    histogram_current = float(histogram_series.iloc[-1]) if not histogram_series.empty else None
    histogram_prev = float(histogram_series.iloc[-2]) if len(histogram_series) > 1 else histogram_current
    k_series, d_series = compute_stochastic(high, low, close)
    k_value = float(k_series.iloc[-1]) if not k_series.empty else None
    d_value = float(d_series.iloc[-1]) if not d_series.empty else None
    k_prev = float(k_series.iloc[-2]) if len(k_series) > 1 else None
    d_prev = float(d_series.iloc[-2]) if len(d_series) > 1 else None
    adx_series = compute_adx(high, low, close)
    adx_value = float(adx_series.iloc[-1]) if not adx_series.empty else None
    ema50_series, ema200_series = compute_emas(close)
    ema50 = float(ema50_series.iloc[-1]) if not ema50_series.empty else None
    ema200 = float(ema200_series.iloc[-1]) if not ema200_series.empty else None
    golden_cross, death_cross = detect_crossovers(ema50_series, ema200_series)
    upper_series, middle_series, lower_series, percent_b_series = compute_bollinger_bands(close)
    upper = float(upper_series.iloc[-1]) if not upper_series.empty else None
    middle = float(middle_series.iloc[-1]) if not middle_series.empty else None
    lower = float(lower_series.iloc[-1]) if not lower_series.empty else None
    percent_b = float(percent_b_series.iloc[-1]) if not percent_b_series.empty else None
    pivots = compute_pivot_points(high, low, close)
    vwap_series, is_approx = compute_vwap(high, low, close, volume)
    vwap_value = float(vwap_series.iloc[-1]) if not vwap_series.empty else None
    rsi_score, rsi_label, rsi_expl = score_rsi(rsi_value)
    macd_score, macd_label, macd_expl = score_macd(macd_line, signal_line, histogram_current, histogram_prev)
    stoch_score, stoch_label, stoch_expl = score_stochastic(k_value, d_value, k_prev, d_prev)
    trend_strength, adx_expl = score_adx(adx_value)
    ema_score, ema_label, ema_expl = score_moving_averages(current_price, ema50, ema200, golden_cross, death_cross)
    boll_score, boll_label, boll_expl = score_bollinger(percent_b, trend_strength)
    vwap_score, vwap_label, vwap_expl = score_vwap(current_price, vwap_value, is_approx)
    cci_series = compute_cci(high, low, close)
    cci_value = float(cci_series.iloc[-1]) if not cci_series.empty and not np.isnan(cci_series.iloc[-1]) else None
    wr_series = compute_williams_r(high, low, close)
    wr_value = float(wr_series.iloc[-1]) if not wr_series.empty and not np.isnan(wr_series.iloc[-1]) else None
    obv_series, obv_ema_series = compute_obv(close, volume)
    obv_value = float(obv_series.iloc[-1]) if not obv_series.empty else None
    obv_ema_value = float(obv_ema_series.iloc[-1]) if not obv_ema_series.empty else None
    mfi_series = compute_mfi(high, low, close, volume)
    mfi_value = float(mfi_series.iloc[-1]) if not mfi_series.empty and not np.isnan(mfi_series.iloc[-1]) else None
    cci_score, cci_label, cci_expl = score_cci(cci_value)
    wr_score, wr_label, wr_expl = score_williams_r(wr_value)
    obv_score, obv_label, obv_expl = score_obv(obv_value, obv_ema_value)
    mfi_score, mfi_label, mfi_expl = score_mfi(mfi_value)
    aroon_up_series, aroon_down_series = compute_aroon(high, low)
    aroon_up = float(aroon_up_series.iloc[-1]) if not aroon_up_series.empty and not np.isnan(aroon_up_series.iloc[-1]) else None
    aroon_down = float(aroon_down_series.iloc[-1]) if not aroon_down_series.empty and not np.isnan(aroon_down_series.iloc[-1]) else None
    roc_series = compute_roc(close)
    roc_value = float(roc_series.iloc[-1]) if not roc_series.empty and not np.isnan(roc_series.iloc[-1]) else None
    trix_series, trix_signal_series = compute_trix(close)
    trix_value = float(trix_series.iloc[-1]) if not trix_series.empty and not np.isnan(trix_series.iloc[-1]) else None
    trix_signal_value = float(trix_signal_series.iloc[-1]) if not trix_signal_series.empty and not np.isnan(trix_signal_series.iloc[-1]) else None
    cmf_series = compute_cmf(high, low, close, volume)
    cmf_value = float(cmf_series.iloc[-1]) if not cmf_series.empty and not np.isnan(cmf_series.iloc[-1]) else None
    chop_series = compute_chop(high, low, close)
    chop_value = float(chop_series.iloc[-1]) if not chop_series.empty and not np.isnan(chop_series.iloc[-1]) else None
    sr_k_series, sr_d_series = compute_stoch_rsi(close)
    sr_k = float(sr_k_series.iloc[-1]) if not sr_k_series.empty and not np.isnan(sr_k_series.iloc[-1]) else None
    sr_d = float(sr_d_series.iloc[-1]) if not sr_d_series.empty and not np.isnan(sr_d_series.iloc[-1]) else None
    sr_k_prev = float(sr_k_series.iloc[-2]) if len(sr_k_series) > 1 and not np.isnan(sr_k_series.iloc[-2]) else None
    sr_d_prev = float(sr_d_series.iloc[-2]) if len(sr_d_series) > 1 and not np.isnan(sr_d_series.iloc[-2]) else None
    aroon_score, aroon_label, aroon_expl = score_aroon(aroon_up, aroon_down)
    roc_score, roc_label, roc_expl = score_roc(roc_value)
    trix_score, trix_label, trix_expl = score_trix(trix_value, trix_signal_value)
    cmf_score, cmf_label, cmf_expl = score_cmf(cmf_value)
    chop_regime, chop_expl = score_chop(chop_value)
    sr_score, sr_label, sr_expl = score_stoch_rsi(sr_k, sr_d, sr_k_prev, sr_d_prev)
    agg = aggregate_scores(
        rsi_score, macd_score, stoch_score, ema_score, boll_score, trend_strength,
        cci_score, wr_score, mfi_score, obv_score,
        aroon_score, roc_score, trix_score, cmf_score,
        sr_score, chop_regime
    )
    indicators = {
        "rsi": {
            "value": round(rsi_value, 1) if rsi_value else None,
            "score": round(rsi_score, 2),
            "label": rsi_label,
            "explanation": rsi_expl
        },
        "macd": {
            "macd_line": round(macd_line, 2) if macd_line else None,
            "signal_line": round(signal_line, 2) if signal_line else None,
            "histogram": round(histogram_current, 2) if histogram_current else None,
            "score": round(macd_score, 2),
            "label": macd_label,
            "explanation": macd_expl
        },
        "stochastic": {
            "k": round(k_value, 1) if k_value else None,
            "d": round(d_value, 1) if d_value else None,
            "score": round(stoch_score, 2),
            "label": stoch_label,
            "explanation": stoch_expl
        },
        "adx": {
            "value": round(adx_value, 1) if adx_value else None,
            "trend_strength": trend_strength
        },
        "moving_averages": {
            "ema50": round(ema50, 1) if ema50 else None,
            "ema200": round(ema200, 1) if ema200 else None,
            "score": round(ema_score, 2),
            "label": ema_label,
            "explanation": ema_expl
        },
        "bollinger": {
            "upper": round(upper, 1) if upper else None,
            "middle": round(middle, 1) if middle else None,
            "lower": round(lower, 1) if lower else None,
            "percent_b": round(percent_b, 2) if percent_b else None,
            "score": round(boll_score, 2),
            "label": boll_label,
            "explanation": boll_expl
        },
        "pivots": {
            "pp": round(pivots['pp'], 1) if pivots['pp'] else None,
            "r1": round(pivots['r1'], 1) if pivots['r1'] else None,
            "r2": round(pivots['r2'], 1) if pivots['r2'] else None,
            "s1": round(pivots['s1'], 1) if pivots['s1'] else None,
            "s2": round(pivots['s2'], 1) if pivots['s2'] else None,
            "position": pivots['position'],
            "nearest_level": pivots['nearest_level']
        },
        "vwap": {
            "value": round(vwap_value, 1) if vwap_value else None,
            "score": round(vwap_score, 2),
            "label": vwap_label,
            "explanation": vwap_expl,
            "is_approximation": is_approx
        },
        "cci": {
            "value": round(cci_value, 1) if cci_value else None,
            "score": round(cci_score, 2),
            "label": cci_label,
            "explanation": cci_expl
        },
        "williams_r": {
            "value": round(wr_value, 1) if wr_value else None,
            "score": round(wr_score, 2),
            "label": wr_label,
            "explanation": wr_expl
        },
        "obv": {
            "value": round(obv_value, 0) if obv_value else None,
            "score": round(obv_score, 2),
            "label": obv_label,
            "explanation": obv_expl
        },
        "mfi": {
            "value": round(mfi_value, 1) if mfi_value else None,
            "score": round(mfi_score, 2),
            "label": mfi_label,
            "explanation": mfi_expl
        },
        "aroon": {
            "up": round(aroon_up, 0) if aroon_up is not None else None,
            "down": round(aroon_down, 0) if aroon_down is not None else None,
            "score": round(aroon_score, 2),
            "label": aroon_label,
            "explanation": aroon_expl
        },
        "roc": {
            "value": round(roc_value, 1) if roc_value is not None else None,
            "score": round(roc_score, 2),
            "label": roc_label,
            "explanation": roc_expl
        },
        "trix": {
            "trix": round(trix_value, 1) if trix_value is not None else None,
            "signal": round(trix_signal_value, 1) if trix_signal_value is not None else None,
            "score": round(trix_score, 2),
            "label": trix_label,
            "explanation": trix_expl
        },
        "cmf": {
            "value": round(cmf_value, 2) if cmf_value is not None else None,
            "score": round(cmf_score, 2),
            "label": cmf_label,
            "explanation": cmf_expl
        },
        "chop": {
            "value": round(chop_value, 1) if chop_value is not None else None,
            "regime": chop_regime,
            "explanation": chop_expl
        },
        "stoch_rsi": {
            "k": round(sr_k, 1) if sr_k is not None else None,
            "d": round(sr_d, 1) if sr_d is not None else None,
            "score": round(sr_score, 2),
            "label": sr_label,
            "explanation": sr_expl
        }
    }
    return {
        "ticker": ticker,
        "company_name": company_name,
        "currency": currency,
        "current_price": round(current_price, 2),
        "day_change_pct": round(day_change_pct, 2),
        "as_of": as_of,
        "overall": {
            "bullish_pct": agg["bullish_pct"],
            "bearish_pct": agg["bearish_pct"],
            "verdict": agg["verdict"],
            "trend_strength": agg["trend_strength"],
            "chop_regime": agg["chop_regime"]
        },
        "indicators": indicators
    }
@app.get("/health")
async def health():
    return {"status": "ok"}
@app.get("/api/backtest")
async def backtest(ticker: str = Query(..., min_length=1), horizon: int = Query(5, ge=1, le=20)):
    try:
        return run_backtest(ticker, horizon=horizon)
    except DataFetchError as e:
        raise HTTPException(status_code=400, detail={"error": e.message, "type": e.error_type})
@app.get("/api/forecast")
async def forecast(ticker: str = Query(..., min_length=1)):
    try:
        return run_forecast(ticker)
    except DataFetchError as e:
        raise HTTPException(status_code=400, detail={"error": e.message, "type": e.error_type})
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)