import numpy as np
import pandas as pd
from backend.app.constants import MIN_ROWS_FOR_EMA200
from backend.app.data_fetch import fetch_ohlcv, DataFetchError
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
HOLD_TOLERANCE_PCT = 1.0
def run_backtest(ticker: str, horizon: int = 5, period: str = "2y") -> dict:
    df = fetch_ohlcv(ticker, period=period)
    close, high, low = df['Close'], df['High'], df['Low']
    volume = df['Volume']
    rsi_s = compute_rsi(close)
    macd_s, signal_s, hist_s = compute_macd(close)
    k_s, d_s = compute_stochastic(high, low, close)
    adx_s = compute_adx(high, low, close)
    ema50_s, ema200_s = compute_emas(close)
    upper_s, middle_s, lower_s, pb_s = compute_bollinger_bands(close)
    vwap_s, _ = compute_vwap(high, low, close, volume)
    cci_s = compute_cci(high, low, close)
    wr_s = compute_williams_r(high, low, close)
    obv_s, obv_ema_s = compute_obv(close, volume)
    mfi_s = compute_mfi(high, low, close, volume)
    aroon_up_s, aroon_down_s = compute_aroon(high, low)
    roc_s = compute_roc(close)
    trix_s, trix_sig_s = compute_trix(close)
    cmf_s = compute_cmf(high, low, close, volume)
    chop_s = compute_chop(high, low, close)
    sr_k_s, sr_d_s = compute_stoch_rsi(close)
    n = len(df)
    burn_in = max(MIN_ROWS_FOR_EMA200, 210)
    trades = []
    for i in range(burn_in, n - horizon):
        price = close.iloc[i]
        def val(s):
            v = s.iloc[i]
            return float(v) if pd.notna(v) else None
        rsi_v = val(rsi_s)
        macd_v, sig_v = val(macd_s), val(signal_s)
        hist_v = val(hist_s)
        hist_p = float(hist_s.iloc[i - 1]) if pd.notna(hist_s.iloc[i - 1]) else hist_v
        k_v, d_v = val(k_s), val(d_s)
        k_p = float(k_s.iloc[i - 1]) if pd.notna(k_s.iloc[i - 1]) else None
        d_p = float(d_s.iloc[i - 1]) if pd.notna(d_s.iloc[i - 1]) else None
        adx_v = val(adx_s)
        ema50_v, ema200_v = val(ema50_s), val(ema200_s)
        pb_v = val(pb_s)
        vwap_v = val(vwap_s)
        cci_v = val(cci_s)
        wr_v = val(wr_s)
        obv_v, obv_ema_v = val(obv_s), val(obv_ema_s)
        mfi_v = val(mfi_s)
        aroon_up_v, aroon_down_v = val(aroon_up_s), val(aroon_down_s)
        roc_v = val(roc_s)
        trix_v, trix_sig_v = val(trix_s), val(trix_sig_s)
        cmf_v = val(cmf_s)
        chop_v = val(chop_s)
        sr_k_v, sr_d_v = val(sr_k_s), val(sr_d_s)
        sr_k_p = float(sr_k_s.iloc[i - 1]) if i > 0 and pd.notna(sr_k_s.iloc[i - 1]) else None
        sr_d_p = float(sr_d_s.iloc[i - 1]) if i > 0 and pd.notna(sr_d_s.iloc[i - 1]) else None
        golden, death = detect_crossovers(
            ema50_s.iloc[:i + 1], ema200_s.iloc[:i + 1]
        )
        rsi_score, _, _ = score_rsi(rsi_v)
        macd_score, _, _ = score_macd(macd_v, sig_v, hist_v, hist_p)
        stoch_score, _, _ = score_stochastic(k_v, d_v, k_p, d_p)
        trend_strength, _ = score_adx(adx_v)
        ema_score, _, _ = score_moving_averages(price, ema50_v, ema200_v, golden, death)
        boll_score, _, _ = score_bollinger(pb_v, trend_strength)
        cci_score, _, _ = score_cci(cci_v)
        wr_score, _, _ = score_williams_r(wr_v)
        obv_score, _, _ = score_obv(obv_v, obv_ema_v)
        mfi_score, _, _ = score_mfi(mfi_v)
        aroon_score, _, _ = score_aroon(aroon_up_v, aroon_down_v)
        roc_score, _, _ = score_roc(roc_v)
        trix_score, _, _ = score_trix(trix_v, trix_sig_v)
        cmf_score, _, _ = score_cmf(cmf_v)
        chop_regime, _ = score_chop(chop_v)
        sr_score, _, _ = score_stoch_rsi(sr_k_v, sr_d_v, sr_k_p, sr_d_p)
        agg = aggregate_scores(
            rsi_score, macd_score, stoch_score, ema_score, boll_score,
            trend_strength, cci_score, wr_score, mfi_score, obv_score,
            aroon_score, roc_score, trix_score, cmf_score,
            sr_score, chop_regime
        )
        fwd_ret = close.iloc[i + horizon] / price - 1
        trades.append({
            "date": close.index[i].strftime("%Y-%m-%d"),
            "verdict": agg["verdict"],
            "bullish_pct": agg["bullish_pct"],
            "price": round(float(price), 2),
            "fwd_ret_pct": round(fwd_ret * 100, 2),
        })
    if not trades:
        raise DataFetchError(
            f"Not enough history to backtest {ticker} (need > {burn_in + horizon} rows)",
            "insufficient_data"
        )
    def summarize(verdict):
        subset = [t for t in trades if t["verdict"] == verdict]
        count = len(subset)
        if count == 0:
            return {"count": 0, "hit_rate": None, "mean_return_pct": None}
        if verdict == "BUY":
            hits = sum(1 for t in subset if t["fwd_ret_pct"] > 0)
        elif verdict == "SELL":
            hits = sum(1 for t in subset if t["fwd_ret_pct"] < 0)
        else:
            hits = sum(1 for t in subset if abs(t["fwd_ret_pct"]) < HOLD_TOLERANCE_PCT)
        return {
            "count": count,
            "hit_rate": round(hits / count * 100, 1),
            "mean_return_pct": round(np.mean([t["fwd_ret_pct"] for t in subset]), 2),
        }
    directional = [t for t in trades if t["verdict"] in ("BUY", "SELL")]
    if directional:
        dir_hits = sum(
            1 for t in directional
            if (t["verdict"] == "BUY" and t["fwd_ret_pct"] > 0)
            or (t["verdict"] == "SELL" and t["fwd_ret_pct"] < 0)
        )
        directional_accuracy = round(dir_hits / len(directional) * 100, 1)
    else:
        directional_accuracy = None
    all_rets = [t["fwd_ret_pct"] for t in trades]
    buy_rets = [t["fwd_ret_pct"] for t in trades if t["verdict"] == "BUY"]
    sell_rets = [t["fwd_ret_pct"] for t in trades if t["verdict"] == "SELL"]
    return {
        "ticker": ticker,
        "horizon_days": horizon,
        "total_signals": len(trades),
        "period": f"{trades[0]['date']} to {trades[-1]['date']}",
        "summary": {
            "buy": summarize("BUY"),
            "hold": summarize("HOLD / NEUTRAL"),
            "sell": summarize("SELL"),
        },
        "directional_accuracy": directional_accuracy,
        "baseline": {
            "mean_abs_return_pct": round(float(np.mean(np.abs(all_rets))), 2),
            "mean_return_all_pct": round(float(np.mean(all_rets)), 2),
            "spread_buy_vs_sell_pct": round(
                (float(np.mean(buy_rets)) if buy_rets else 0)
                - (float(np.mean(sell_rets)) if sell_rets else 0), 2
            ),
        },
        "trades": trades,
    }