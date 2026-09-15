import numpy as np
import pandas as pd
from backend.app.constants import MIN_ROWS_FOR_EMA200
from backend.app.data_fetch import fetch_ohlcv, get_ticker_info, DataFetchError
from backend.app.indicators import (
    compute_rsi, compute_macd, compute_stochastic, compute_adx,
    compute_emas, detect_crossovers, compute_bollinger_bands, compute_vwap,
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
HORIZONS = [1, 5, 10, 20]
MIN_CONDITIONAL_SAMPLES = 30
VOL_LOOKBACK = 252
def _score_at(df, i, indicator_cache):
    close, high, low, volume = df['Close'], df['High'], df['Low'], df['Volume']
    price = close.iloc[i]
    def val(s):
        v = s.iloc[i]
        return float(v) if pd.notna(v) else None
    (rsi_s, macd_s, sig_s, hist_s, k_s, d_s, adx_s, ema50_s, ema200_s,
     pb_s, cci_s, wr_s, obv_s, obv_ema_s, mfi_s, aroon_up_s, aroon_down_s,
     roc_s, trix_s, trix_sig_s, cmf_s, chop_s, sr_k_s, sr_d_s) = indicator_cache
    hist_p = float(hist_s.iloc[i - 1]) if i > 0 and pd.notna(hist_s.iloc[i - 1]) else None
    k_p = float(k_s.iloc[i - 1]) if i > 0 and pd.notna(k_s.iloc[i - 1]) else None
    d_p = float(d_s.iloc[i - 1]) if i > 0 and pd.notna(d_s.iloc[i - 1]) else None
    golden, death = detect_crossovers(ema50_s.iloc[:i + 1], ema200_s.iloc[:i + 1])
    rsi_score, _, _ = score_rsi(val(rsi_s))
    macd_score, _, _ = score_macd(val(macd_s), val(sig_s), val(hist_s), hist_p)
    stoch_score, _, _ = score_stochastic(val(k_s), val(d_s), k_p, d_p)
    trend_strength, _ = score_adx(val(adx_s))
    ema_score, _, _ = score_moving_averages(price, val(ema50_s), val(ema200_s), golden, death)
    boll_score, _, _ = score_bollinger(val(pb_s), trend_strength)
    cci_score, _, _ = score_cci(val(cci_s))
    wr_score, _, _ = score_williams_r(val(wr_s))
    obv_score, _, _ = score_obv(val(obv_s), val(obv_ema_s))
    mfi_score, _, _ = score_mfi(val(mfi_s))
    aroon_score, _, _ = score_aroon(val(aroon_up_s), val(aroon_down_s))
    roc_score, _, _ = score_roc(val(roc_s))
    trix_score, _, _ = score_trix(val(trix_s), val(trix_sig_s))
    cmf_score, _, _ = score_cmf(val(cmf_s))
    chop_regime, _ = score_chop(val(chop_s))
    sr_score, _, _ = score_stoch_rsi(
        val(sr_k_s), val(sr_d_s),
        float(sr_k_s.iloc[i - 1]) if i > 0 and pd.notna(sr_k_s.iloc[i - 1]) else None,
        float(sr_d_s.iloc[i - 1]) if i > 0 and pd.notna(sr_d_s.iloc[i - 1]) else None,
    )
    return aggregate_scores(
        rsi_score, macd_score, stoch_score, ema_score, boll_score,
        trend_strength, cci_score, wr_score, mfi_score, obv_score,
        aroon_score, roc_score, trix_score, cmf_score,
        sr_score, chop_regime
    )
def run_forecast(ticker: str, period: str = "2y") -> dict:
    df = fetch_ohlcv(ticker, period=period)
    close, high, low, volume = df['Close'], df['High'], df['Low'], df['Volume']
    n = len(df)
    price = float(close.iloc[-1])
    info = get_ticker_info(ticker)
    indicator_cache = (
        compute_rsi(close),
        *compute_macd(close)[:3],
        *compute_stochastic(high, low, close)[:2],
        compute_adx(high, low, close),
        *compute_emas(close)[:2],
        compute_bollinger_bands(close)[3],
        compute_cci(high, low, close),
        compute_williams_r(high, low, close),
        *compute_obv(close, volume)[:2],
        compute_mfi(high, low, close, volume),
        *compute_aroon(high, low)[:2],
        compute_roc(close),
        *compute_trix(close)[:2],
        compute_cmf(high, low, close, volume),
        compute_chop(high, low, close),
        *compute_stoch_rsi(close)[:2],
    )
    current = _score_at(df, n - 1, indicator_cache)
    current_verdict = current["verdict"]
    log_ret = np.log(close / close.shift(1)).dropna().tail(VOL_LOOKBACK)
    daily_sigma = float(log_ret.std())
    burn_in = max(MIN_ROWS_FOR_EMA200, 210)
    hist = []
    for i in range(burn_in, n - 1):
        agg = _score_at(df, i, indicator_cache)
        hist.append({"verdict": agg["verdict"], "i": i})
    max_h = HORIZONS[-1]
    forecasts = []
    for h in HORIZONS:
        fwd_all, fwd_matching = [], []
        for rec in hist:
            i = rec["i"]
            if i + h >= n:
                continue
            r = close.iloc[i + h] / close.iloc[i] - 1
            fwd_all.append(r)
            if rec["verdict"] == current_verdict:
                fwd_matching.append(r)
        fwd_all = np.array(fwd_all)
        fwd_match = np.array(fwd_matching)
        conditional = len(fwd_match) >= MIN_CONDITIONAL_SAMPLES
        sample = fwd_match if conditional else fwd_all
        sigma_h = daily_sigma * np.sqrt(h)
        exp_low = price * float(np.exp(-sigma_h))
        exp_high = price * float(np.exp(sigma_h))
        if len(sample) > 0:
            prob_up = float((sample > 0).mean()) * 100
            prob_in_range = float((np.abs(np.log1p(sample)) <= sigma_h).mean()) * 100
            emp_low = price * float(np.exp(np.percentile(np.log1p(sample), 16)))
            emp_high = price * float(np.exp(np.percentile(np.log1p(sample), 84)))
        else:
            prob_up = prob_in_range = None
            emp_low, emp_high = exp_low, exp_high
        if len(fwd_all) > 0:
            best = float(fwd_all.max()) * 100
            worst = float(fwd_all.min()) * 100
        else:
            best = worst = None
        forecasts.append({
            "horizon_days": h,
            "expected_low": round(exp_low, 2),
            "expected_high": round(exp_high, 2),
            "empirical_low": round(emp_low, 2),
            "empirical_high": round(emp_high, 2),
            "prob_up_pct": round(prob_up, 1) if prob_up is not None else None,
            "prob_in_range_pct": round(prob_in_range, 1) if prob_in_range is not None else None,
            "hist_best_pct": round(best, 1) if best is not None else None,
            "hist_worst_pct": round(worst, 1) if worst is not None else None,
            "conditional": conditional,
            "sample_size": int(len(sample)),
        })
    return {
        "ticker": ticker,
        "company_name": info.get("longName") or info.get("shortName") or ticker,
        "currency": info.get("currency") or "",
        "current_price": round(price, 2),
        "as_of": close.index[-1].strftime("%Y-%m-%d"),
        "current_verdict": current_verdict,
        "bullish_pct": current["bullish_pct"],
        "daily_volatility_pct": round(daily_sigma * 100, 2),
        "forecasts": forecasts,
    }