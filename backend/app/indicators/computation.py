import pandas as pd
import numpy as np
import pandas_ta as ta
from backend.app.constants import (
    RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    STOCH_K_PERIOD, STOCH_D_PERIOD, STOCH_SMOOTH,
    ADX_PERIOD, EMA_SHORT, EMA_LONG,
    BOLLINGER_PERIOD, BOLLINGER_STD, VWAP_WINDOW,
    CCI_PERIOD, WILLIAMS_R_PERIOD, OBV_EMA_PERIOD, MFI_PERIOD,
    AROON_PERIOD, ROC_PERIOD, TRIX_PERIOD, TRIX_SIGNAL_PERIOD, CMF_PERIOD,
    CHOP_PERIOD, STOCH_RSI_PERIOD, STOCH_RSI_SMOOTH, STOCH_RSI_D_PERIOD
)
def compute_rsi(close: pd.Series) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
def compute_macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = close.ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = close.ewm(span=MACD_SLOW, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=MACD_SIGNAL, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram
def compute_stochastic(high: pd.Series, low: pd.Series, close: pd.Series) -> tuple[pd.Series, pd.Series]:
    low_min = low.rolling(STOCH_K_PERIOD).min()
    high_max = high.rolling(STOCH_K_PERIOD).max()
    k_raw = 100 * (close - low_min) / (high_max - low_min)
    k = k_raw.rolling(STOCH_SMOOTH).mean()
    d = k.rolling(STOCH_D_PERIOD).mean()
    return k, d
def compute_adx(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    adx_df = ta.adx(high, low, close, length=ADX_PERIOD)
    if adx_df is not None and f'ADX_{ADX_PERIOD}' in adx_df.columns:
        return adx_df[f'ADX_{ADX_PERIOD}']
    return pd.Series(index=close.index, dtype=float)
def compute_emas(close: pd.Series) -> tuple[pd.Series, pd.Series]:
    ema50 = close.ewm(span=EMA_SHORT, adjust=False).mean()
    ema200 = close.ewm(span=EMA_LONG, adjust=False).mean()
    return ema50, ema200
def detect_crossovers(ema50: pd.Series, ema200: pd.Series, lookback: int = 5) -> tuple[bool, bool]:
    if len(ema50) < lookback + 1 or len(ema200) < lookback + 1:
        return False, False
    golden_cross = False
    death_cross = False
    for i in range(1, min(lookback + 1, len(ema50))):
        idx = -i
        prev_idx = -i - 1
        if abs(prev_idx) > len(ema50):
            break
        if ema50.iloc[prev_idx] <= ema200.iloc[prev_idx] and ema50.iloc[idx] > ema200.iloc[idx]:
            golden_cross = True
        if ema50.iloc[prev_idx] >= ema200.iloc[prev_idx] and ema50.iloc[idx] < ema200.iloc[idx]:
            death_cross = True
    return golden_cross, death_cross
def compute_bollinger_bands(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    middle = close.rolling(BOLLINGER_PERIOD).mean()
    std = close.rolling(BOLLINGER_PERIOD).std()
    upper = middle + BOLLINGER_STD * std
    lower = middle - BOLLINGER_STD * std
    percent_b = (close - lower) / (upper - lower)
    return upper, middle, lower, percent_b
def compute_pivot_points(high: pd.Series, low: pd.Series, close: pd.Series) -> dict:
    if len(high) < 2 or len(low) < 2 or len(close) < 2:
        return {
            'pp': None, 'r1': None, 'r2': None, 's1': None, 's2': None,
            'position': 'unknown', 'nearest_level': 'unknown'
        }
    prev_high = high.iloc[-2]
    prev_low = low.iloc[-2]
    prev_close = close.iloc[-2]
    current_close = close.iloc[-1]
    pp = (prev_high + prev_low + prev_close) / 3
    r1 = 2 * pp - prev_low
    s1 = 2 * pp - prev_high
    r2 = pp + (prev_high - prev_low)
    s2 = pp - (prev_high - prev_low)
    position = "above PP" if current_close > pp else "below PP"
    levels = {'R1': r1, 'R2': r2, 'S1': s1, 'S2': s2, 'PP': pp}
    nearest = min(levels.items(), key=lambda x: abs(x[1] - current_close))
    distance_pct = abs(nearest[1] - current_close) / current_close * 100
    nearest_level = f"{nearest[0]} ({distance_pct:.1f}% away)"
    return {
        'pp': pp, 'r1': r1, 'r2': r2, 's1': s1, 's2': s2,
        'position': position, 'nearest_level': nearest_level
    }
def compute_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> tuple[pd.Series, bool]:
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).rolling(VWAP_WINDOW).sum() / volume.rolling(VWAP_WINDOW).sum()
    return vwap, True
def compute_cci(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    typical_price = (high + low + close) / 3
    sma_tp = typical_price.rolling(CCI_PERIOD).mean()
    mean_deviation = (typical_price - sma_tp).abs().rolling(CCI_PERIOD).mean()
    cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
    return cci
def compute_williams_r(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    high_max = high.rolling(WILLIAMS_R_PERIOD).max()
    low_min = low.rolling(WILLIAMS_R_PERIOD).min()
    wr = -100 * (high_max - close) / (high_max - low_min)
    return wr
def compute_obv(close: pd.Series, volume: pd.Series) -> tuple[pd.Series, pd.Series]:
    direction = close.diff().fillna(0).apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)
    obv = (direction * volume).cumsum()
    obv_ema = obv.ewm(span=OBV_EMA_PERIOD, adjust=False).mean()
    return obv, obv_ema
def compute_mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    typical_price = (high + low + close) / 3
    raw_money_flow = typical_price * volume
    tp_diff = typical_price.diff()
    positive_flow = raw_money_flow.where(tp_diff > 0, 0.0)
    negative_flow = raw_money_flow.where(tp_diff < 0, 0.0)
    pos_sum = positive_flow.rolling(MFI_PERIOD).sum()
    neg_sum = negative_flow.rolling(MFI_PERIOD).sum()
    with np.errstate(divide='ignore', invalid='ignore'):
        money_ratio = pos_sum / neg_sum.replace(0, np.nan)
        mfi = 100 - (100 / (1 + money_ratio))
    return mfi.fillna(50)
def compute_aroon(high: pd.Series, low: pd.Series) -> tuple[pd.Series, pd.Series]:
    window = AROON_PERIOD + 1
    high_idx = high.rolling(window).apply(np.argmax, raw=True)
    low_idx = low.rolling(window).apply(np.argmin, raw=True)
    aroon_up = 100 * (window - 1 - high_idx) / AROON_PERIOD
    aroon_down = 100 * (window - 1 - low_idx) / AROON_PERIOD
    return aroon_up, aroon_down
def compute_roc(close: pd.Series) -> pd.Series:
    return close.pct_change(ROC_PERIOD) * 100
def compute_trix(close: pd.Series) -> tuple[pd.Series, pd.Series]:
    ema1 = np.log(close).ewm(span=TRIX_PERIOD, adjust=False).mean()
    ema2 = ema1.ewm(span=TRIX_PERIOD, adjust=False).mean()
    ema3 = ema2.ewm(span=TRIX_PERIOD, adjust=False).mean()
    trix = ema3.pct_change() * 10000  # scaled to readable numbers
    signal = trix.ewm(span=TRIX_SIGNAL_PERIOD, adjust=False).mean()
    return trix, signal
def compute_cmf(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    money_flow_multiplier = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
    money_flow_volume = money_flow_multiplier * volume
    cmf = money_flow_volume.rolling(CMF_PERIOD).sum() / volume.rolling(CMF_PERIOD).sum()
    return cmf.fillna(0)
def compute_chop(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    tr_hl = high - low
    tr_hc = (high - prev_close).abs()
    tr_lc = (low - prev_close).abs()
    true_range = pd.concat([tr_hl, tr_hc, tr_lc], axis=1).max(axis=1)
    sum_tr = true_range.rolling(CHOP_PERIOD).sum()
    max_high = high.rolling(CHOP_PERIOD).max()
    min_low = low.rolling(CHOP_PERIOD).min()
    range_ = (max_high - min_low).replace(0, np.nan)
    chop = 100 * np.log10(sum_tr / range_) / np.log10(CHOP_PERIOD)
    return chop
def compute_stoch_rsi(close: pd.Series) -> tuple[pd.Series, pd.Series]:
    rsi = compute_rsi(close)
    rsi_min = rsi.rolling(STOCH_RSI_PERIOD).min()
    rsi_max = rsi.rolling(STOCH_RSI_PERIOD).max()
    rsi_range = (rsi_max - rsi_min).replace(0, np.nan)
    raw = (rsi - rsi_min) / rsi_range * 100
    k = raw.rolling(STOCH_RSI_SMOOTH).mean()
    d = k.rolling(STOCH_RSI_D_PERIOD).mean()
    return k, d