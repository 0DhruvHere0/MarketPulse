import { useState, useEffect } from 'react';
import { FlaskConical, Loader2, TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react';
import { BacktestView } from './BacktestPanel';

const API_BASE = 'http://localhost:8001/api';

const VERDICT_META = {
  buy: { label: 'BUY', icon: TrendingUp, badge: 'badge-up' },
  hold: { label: 'HOLD', icon: Minus, badge: 'badge-flat' },
  sell: { label: 'SELL', icon: TrendingDown, badge: 'badge-down' },
};

function ForecastRow({ f, currentPrice }) {
  const probUp = f.prob_up_pct;
  const probDown = probUp === null ? null : 100 - probUp;
  const markerPct = Math.min(100, Math.max(0, ((currentPrice - f.expected_low) / (f.expected_high - f.expected_low)) * 100));

  return (
    <div className="panel">
      <div className="panel-header">
        <span>{f.horizon_days} Day{f.horizon_days > 1 ? 's' : ''} Forward</span>
        <span className="text-muted font-normal normal-case tracking-normal">
          {f.conditional ? `${f.sample_size} similar verdicts` : `${f.sample_size} historical days`}
        </span>
      </div>
      <div className="p-5">
        {/* low / now / high */}
        <div className="grid grid-cols-3 gap-4 text-center mb-4">
          <div>
            <div className="text-muted text-[10px] tracking-widest mb-1">LOW (1σ)</div>
            <div className="text-down font-bold text-xl tabular-nums">{f.expected_low.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-muted text-[10px] tracking-widest mb-1">NOW</div>
            <div className="text-bright font-bold text-xl tabular-nums">{currentPrice.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-muted text-[10px] tracking-widest mb-1">HIGH (1σ)</div>
            <div className="text-up font-bold text-xl tabular-nums">{f.expected_high.toLocaleString()}</div>
          </div>
        </div>

        {/* range bar with now marker */}
        <div className="relative h-3 border border-term-border-hi mb-1"
          style={{ background: 'linear-gradient(90deg, rgba(255,46,46,0.35), rgba(42,42,42,0.4), rgba(0,210,106,0.35))' }}>
          <div
            className="absolute -top-1 -bottom-1 w-[3px] bg-bright"
            style={{ left: `calc(${markerPct}% - 1.5px)` }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-muted mb-5">
          <span>{f.expected_low.toLocaleString()}</span>
          <span>RANGE ±{(((f.expected_high - f.expected_low) / 2) / currentPrice * 100).toFixed(1)}%</span>
          <span>{f.expected_high.toLocaleString()}</span>
        </div>

        {/* rise / fall probability */}
        <div className="flex justify-between text-xs font-bold mb-1.5">
          <span className="text-up tabular-nums">▲ RISE {probUp === null ? '—' : `${probUp}%`}</span>
          <span className="text-down tabular-nums">FALL {probDown === null ? '—' : `${probDown}%`}</span>
        </div>
        <div className="h-3 flex border border-term-border-hi overflow-hidden">
          <div className="h-full transition-all duration-700" style={{ width: `${probUp ?? 50}%`, background: 'linear-gradient(90deg, rgba(0,210,106,0.5), rgba(0,210,106,0.9))' }} />
          <div className="h-full flex-1" style={{ background: 'linear-gradient(90deg, rgba(255,46,46,0.9), rgba(255,46,46,0.5))' }} />
        </div>

        {/* extremes */}
        <div className="grid grid-cols-3 gap-4 mt-5 pt-4 border-t border-term-border text-center">
          <div>
            <div className="text-muted text-[10px] tracking-widest mb-0.5">BEST SEEN</div>
            <div className="text-up font-bold tabular-nums text-sm">{f.hist_best_pct === null ? '—' : `+${f.hist_best_pct}%`}</div>
          </div>
          <div>
            <div className="text-muted text-[10px] tracking-widest mb-0.5">RANGE HELD</div>
            <div className="text-bright font-bold tabular-nums text-sm">{f.prob_in_range_pct === null ? '—' : `${f.prob_in_range_pct}%`}</div>
          </div>
          <div>
            <div className="text-muted text-[10px] tracking-widest mb-0.5">WORST SEEN</div>
            <div className="text-down font-bold tabular-nums text-sm">{f.hist_worst_pct === null ? '—' : `${f.hist_worst_pct}%`}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ForecastView({ symbol, onBack }) {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      setForecast(null);
      try {
        const res = await fetch(`${API_BASE}/forecast?ticker=${encodeURIComponent(symbol.ticker)}`);
        const data = await res.json();
        if (!cancelled) {
          if (data.detail) setError(data.detail.error || 'Forecast failed');
          else setForecast(data);
        }
      } catch {
        if (!cancelled) setError('Cannot reach the backend. Ensure it runs on port 8001.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [symbol.ticker]);

  if (loading || (!forecast && !error)) {
    return (
      <div className="panel p-12 text-center max-w-xl mx-auto fade-in">
        <Loader2 className="w-8 h-8 text-amber animate-spin mx-auto mb-3" />
        <p className="text-bright text-sm font-bold tracking-widest">COMPUTING FORECAST</p>
        <p className="text-muted text-xs mt-1">{symbol.ticker} · volatility + precedent scan</p>
      </div>
    );
  }

  if (error || !forecast) {
    return (
      <div className="panel p-8 text-center max-w-xl mx-auto" style={{ borderColor: 'rgba(255,46,46,0.4)' }}>
        <AlertCircle className="w-8 h-8 text-down mx-auto mb-3" />
        <p className="text-muted text-sm mb-5">{error}</p>
        <button onClick={onBack} className="btn-ghost">← NEW TICKER</button>
      </div>
    );
  }

  const vMeta = VERDICT_META[forecast.current_verdict === 'BUY' ? 'buy' : forecast.current_verdict === 'SELL' ? 'sell' : 'hold'];
  const VerdictIcon = vMeta.icon;

  return (
    <div className="w-full">
      {/* quote strip */}
      <div className="panel fade-in mb-4">
        <div className="panel-header">
          <span>{forecast.ticker} — Forecast</span>
          <button onClick={onBack} className="text-muted hover:text-amber font-normal normal-case tracking-normal transition-colors">← NEW TICKER</button>
        </div>
        <div className="p-5 grid grid-cols-3 gap-2 text-center">
          <div>
            <div className="text-bright font-bold text-2xl tabular-nums">{forecast.current_price.toLocaleString()}</div>
            <div className="text-muted text-[10px] tracking-widest mt-1">LAST{forecast.currency ? ` (${forecast.currency})` : ''}</div>
          </div>
          <div className="flex flex-col items-center justify-center gap-1">
            <span className={`badge ${vMeta.badge}`}>
              <VerdictIcon className="w-3 h-3" />
              {vMeta.label}
            </span>
            <div className="text-muted text-[10px] tabular-nums">{forecast.bullish_pct}% BULL</div>
          </div>
          <div>
            <div className="text-bright font-bold text-2xl tabular-nums">{forecast.daily_volatility_pct}%</div>
            <div className="text-muted text-[10px] tracking-widest mt-1">DAILY VOL</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {forecast.forecasts.map((f, i) => (
          <div key={f.horizon_days} className={`fade-in stagger-${i + 1} min-w-0`}>
            <ForecastRow f={f} currentPrice={forecast.current_price} />
          </div>
        ))}
      </div>

      <div className="w-full flex justify-center mt-6">
        <p className="text-muted text-[11px] leading-relaxed text-center max-w-2xl">
          Ranges are 1σ (≈68%) from realized volatility. Probabilities from historical days with the same verdict.
          BEST/WORST SEEN are actual historical extremes — the range can be exceeded. Statistical description, not prediction.
        </p>
      </div>
    </div>
  );
}

export function SimulationView({ symbol, onBack }) {
  const [mode, setMode] = useState('forecast');

  const tabs = [
    { id: 'forecast', label: 'Forecast', icon: null },
    { id: 'backtest', label: 'Backtest', icon: FlaskConical },
  ];

  return (
    <div className="w-full">
      <div className="flex items-center justify-center gap-1 mb-6 border-b border-term-border">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setMode(t.id)}
            className={`tab inline-flex items-center gap-2 ${mode === t.id ? 'tab-active' : ''}`}
          >
            {t.icon && <t.icon className="w-3.5 h-3.5" />}
            {t.label}
          </button>
        ))}
      </div>

      {mode === 'forecast'
        ? <ForecastView symbol={symbol} onBack={onBack} />
        : <BacktestView symbol={symbol} onBack={onBack} />}
    </div>
  );
}
