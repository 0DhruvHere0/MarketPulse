import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
export const DEITY_MAP = {
  rsi: { key: 'rsi', label: 'RSI', deity: 'ZEUS', period: '14', category: 'MOMENTUM' },
  macd: { key: 'macd', label: 'MACD', deity: 'HERMES', period: '12,26,9', category: 'TREND' },
  stochastic: { key: 'stochastic', label: 'STOCH', deity: 'DEMETER', period: '14,3,3', category: 'MOMENTUM' },
  adx: { key: 'adx', label: 'ADX', deity: 'ARES', period: '14', category: 'STRENGTH' },
  moving_averages: { key: 'moving_averages', label: 'EMA', deity: 'APOLLO', period: '50/200', category: 'TREND' },
  bollinger: { key: 'bollinger', label: 'BOLL', deity: 'ATHENA', period: '20,2σ', category: 'VOLATILITY' },
  pivots: { key: 'pivots', label: 'PIVOT', deity: 'HEPHAESTUS', period: 'CLASSIC', category: 'REFERENCE' },
  vwap: { key: 'vwap', label: 'VWAP', deity: 'POSEIDON', period: '20D', category: 'VOLUME' },
  cci: { key: 'cci', label: 'CCI', deity: 'ARTEMIS', period: '20', category: 'MOMENTUM' },
  williams_r: { key: 'williams_r', label: 'W%R', deity: 'IRIS', period: '14', category: 'MOMENTUM' },
  obv: { key: 'obv', label: 'OBV', deity: 'HESTIA', period: 'EMA21', category: 'VOLUME' },
  mfi: { key: 'mfi', label: 'MFI', deity: 'PLUTUS', period: '14', category: 'MOMENTUM' },
  aroon: { key: 'aroon', label: 'AROON', deity: 'ATLAS', period: '25', category: 'TREND' },
  roc: { key: 'roc', label: 'ROC', deity: 'NOTUS', period: '12', category: 'MOMENTUM' },
  trix: { key: 'trix', label: 'TRIX', deity: 'NIKE', period: '15,9', category: 'MOMENTUM' },
  cmf: { key: 'cmf', label: 'CMF', deity: 'HERMES.T', period: '21', category: 'VOLUME' },
  chop: { key: 'chop', label: 'CHOP', deity: 'HECATE', period: '14', category: 'REGIME' },
  stoch_rsi: { key: 'stoch_rsi', label: 'S-RSI', deity: 'IRIS-II', period: '14,14,3,3', category: 'MOMENTUM' },
};
export function getVerdictStyle(verdict) {
  if (verdict === 'BUY') return { badge: 'badge-up' };
  if (verdict === 'SELL') return { badge: 'badge-down' };
  return { badge: 'badge-flat' };
}
export function getScoreBadge(score) {
  if (score > 0.15) return { badge: 'badge-up', icon: TrendingUp, label: 'BULL' };
  if (score < -0.15) return { badge: 'badge-down', icon: TrendingDown, label: 'BEAR' };
  return { badge: 'badge-flat', icon: Minus, label: 'NEUTRAL' };
}
export function scoreColor(score) {
  if (score > 0.15) return '#00d26a';
  if (score < -0.15) return '#ff2e2e';
  return '#ff9900';
}