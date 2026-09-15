import { useState } from 'react';
import { FlaskConical, Loader2, TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8001/api';

const VERDICT_META = {
  buy: { label: 'BUY', icon: TrendingUp, badge: 'badge-up' },
  hold: { label: 'HOLD', icon: Minus, badge: 'badge-flat' },
  sell: { label: 'SELL', icon: TrendingDown, badge: 'badge-down' },
};

const UP = '#00d26a';
const DOWN = '#ff2e2e';

function StatBlock({ meta, data }) {
  const Icon = meta.icon;
  return (
    <div className="panel text-center p-4">
      <span className={`badge ${meta.badge} mx-auto mb-2`}>
        <Icon className="w-3 h-3" />
        {meta.label}
      </span>
      <div className="text-bright font-bold text-2xl tabular-nums">
        {data.hit_rate === null ? '—' : `${data.hit_rate}%`}
      </div>
      <div className="text-muted text-[10px] tracking-widest mt-1">HIT RATE</div>
      <div className="text-muted text-[11px] mt-1.5 tabular-nums">
        {data.count} signals · avg {data.mean_return_pct === null ? '—' : `${data.mean_return_pct > 0 ? '+' : ''}${data.mean_return_pct}%`}
      </div>
    </div>
  );
}

function EquityChart({ trades, horizon }) {
  const w = 800, h = 320;
  const pad = { top: 16, right: 16, bottom: 28, left: 58 };
  const iw = w - pad.left - pad.right;
  const ih = h - pad.top - pad.bottom;

  const isSuccess = (t) => {
    if (t.verdict === 'BUY') return t.fwd_ret_pct > 0;
    if (t.verdict === 'SELL') return t.fwd_ret_pct < 0;
    return Math.abs(t.fwd_ret_pct) < 1.0;
  };

  // cumulative equity: long BUY, short SELL, flat HOLD
  const points = [];
  let cum = 0;
  for (let i = 0; i < trades.length; i++) {
    const t = trades[i];
    const exposure = t.verdict === 'BUY' ? 1 : t.verdict === 'SELL' ? -1 : 0;
    cum += exposure * t.fwd_ret_pct;
    points.push({ cum, trade: t });
  }

  const cums = points.map(p => p.cum);
  const dataMin = Math.min(0, ...cums);
  const dataMax = Math.max(0, ...cums);
  const span = Math.max(dataMax - dataMin, 1);
  const lo = dataMin - span * 0.08;
  const hi = dataMax + span * 0.08;

  const x = (i) => pad.left + (i / Math.max(trades.length - 1, 1)) * iw;
  const y = (v) => pad.top + (1 - (v - lo) / (hi - lo)) * ih;
  const y0 = y(0);

  const ticks = 5;
  const tickVals = Array.from({ length: ticks + 1 }, (_, i) => lo + (hi - lo) * i / ticks);

  // Build line segments, each colored by whether equity is above/below zero
  // (point pair midpoint decides) — solid, no clipping, no gradient trickery.
  const segments = [];
  for (let i = 1; i < points.length; i++) {
    const a = points[i - 1], b = points[i];
    const mid = (a.cum + b.cum) / 2;
    segments.push({
      x1: x(i - 1), y1: y(a.cum), x2: x(i), y2: y(b.cum),
      color: mid >= 0 ? UP : DOWN,
    });
  }

  // Fill area between equity and zero, split by sign: build polygons per contiguous run
  const runs = [];
  let run = null;
  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    const sign = p.cum >= 0 ? 'up' : 'down';
    if (!run || run.sign !== sign) {
      if (run) runs.push(run);
      run = { sign, from: i, to: i };
    } else {
      run.to = i;
    }
  }
  if (run) runs.push(run);

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full min-w-[600px]" role="img" aria-label="Backtest equity curve">
        {/* grid + y labels */}
        {tickVals.map((v, i) => (
          <g key={i}>
            <line x1={pad.left} x2={w - pad.right} y1={y(v)} y2={y(v)} stroke="#1f1f1f" strokeDasharray="3,4" />
            <text x={pad.left - 8} y={y(v) + 4} textAnchor="end" fill="#8a8a8a" fontSize="11" fontFamily="JetBrains Mono, monospace">
              {v.toFixed(1)}%
            </text>
          </g>
        ))}

        {/* zero line */}
        <line x1={pad.left} x2={w - pad.right} y1={y0} y2={y0} stroke="#555" strokeWidth="1" />

        {/* area fills: green above zero, red below */}
        {runs.map((r, ri) => {
          const pts = points.slice(r.from, r.to + 1);
          const path = [
            `M${x(r.from).toFixed(1)},${y0}`,
            ...pts.map((p, j) => `L${x(r.from + j).toFixed(1)},${y(p.cum).toFixed(1)}`),
            `L${x(r.to).toFixed(1)},${y0}`,
            'Z',
          ].join(' ');
          return (
            <path key={ri} d={path} fill={r.sign === 'up' ? 'rgba(0,210,106,0.14)' : 'rgba(255,46,46,0.14)'} />
          );
        })}

        {/* equity segments, colored by side of zero */}
        {segments.map((s, i) => (
          <line key={i} x1={s.x1} y1={s.y1} x2={s.x2} y2={s.y2} stroke={s.color} strokeWidth="1.8" />
        ))}

        {/* signal dots: filled = expectation met, hollow = missed */}
        {points.map((p, i) => {
          const ok = isSuccess(p.trade);
          const isDir = p.trade.verdict !== 'HOLD / NEUTRAL';
          return (
            <circle
              key={i}
              cx={x(i)}
              cy={y(p.cum)}
              r={isDir ? 3 : 1.5}
              fill={ok ? UP : DOWN}
              fillOpacity={isDir ? 1 : 0.5}
              stroke="none"
            >
              <title>{`${p.trade.date}  ${p.trade.verdict}  →  ${p.trade.fwd_ret_pct > 0 ? '+' : ''}${p.trade.fwd_ret_pct}% / ${horizon}d  ${ok ? '✓ MET' : '✗ MISSED'}`}</title>
            </circle>
          );
        })}

        {/* x axis dates */}
        <text x={pad.left} y={h - 8} fill="#8a8a8a" fontSize="11" fontFamily="JetBrains Mono, monospace">{trades[0]?.date}</text>
        <text x={w - pad.right} y={h - 8} textAnchor="end" fill="#8a8a8a" fontSize="11" fontFamily="JetBrains Mono, monospace">{trades[trades.length - 1]?.date}</text>
      </svg>

      <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-1.5 mt-3 text-[11px] text-muted">
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: UP }} /> EXPECTATION MET</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: DOWN }} /> MISSED</span>
        <span className="flex items-center gap-1.5"><span className="w-4 h-0.5 inline-block" style={{ background: UP }} /> EQUITY &gt; 0</span>
        <span className="flex items-center gap-1.5"><span className="w-4 h-0.5 inline-block" style={{ background: DOWN }} /> EQUITY &lt; 0</span>
        <span>LONG BUY / SHORT SELL / FLAT HOLD</span>
      </div>
    </div>
  );
}

export function BacktestView({ symbol, onBack }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [horizon, setHorizon] = useState(5);

  const runTest = async (h = horizon) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/backtest?ticker=${encodeURIComponent(symbol.ticker)}&horizon=${h}`);
      const data = await res.json();
      if (data.detail) {
        setError(data.detail.error || 'Backtest failed');
      } else {
        setResult(data);
      }
    } catch {
      setError('Cannot reach the backend. Ensure it runs on port 8001.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full">
      <div className="panel fade-in mb-4">
        <div className="panel-header">
          <span>{symbol.ticker} — Walk-Forward Trial</span>
          <button onClick={onBack} className="text-muted hover:text-amber font-normal normal-case tracking-normal transition-colors">← NEW TICKER</button>
        </div>
        <div className="p-4 flex flex-wrap items-center justify-center gap-3">
          <label className="text-xs text-muted tracking-widest" htmlFor="horizon">FORWARD WINDOW:</label>
          <select
            id="horizon"
            value={horizon}
            onChange={(e) => {
              const h = Number(e.target.value);
              setHorizon(h);
              if (result || error) runTest(h);
            }}
            className="text-sm px-3 py-1.5 border border-term-border-hi bg-term-panel text-bright cursor-pointer"
          >
            {[1, 5, 10, 20].map((h) => (
              <option key={h} value={h}>{h} DAY{h > 1 ? 'S' : ''}</option>
            ))}
          </select>
          <button onClick={() => runTest()} disabled={loading} className="btn-amber">
            {loading ? <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" /> : <FlaskConical className="w-3.5 h-3.5 mr-2" />}
            RUN TRIAL
          </button>
        </div>
      </div>

      {loading && (
        <div className="panel p-10 text-center">
          <Loader2 className="w-8 h-8 text-amber animate-spin mx-auto mb-3" />
          <p className="text-muted text-sm">REPLAYING {symbol.ticker} HISTORY…</p>
        </div>
      )}

      {error && !loading && (
        <div className="panel p-8 text-center" style={{ borderColor: 'rgba(255,46,46,0.4)' }}>
          <AlertCircle className="w-8 h-8 text-down mx-auto mb-3" />
          <p className="text-muted text-sm mb-5">{error}</p>
          <button onClick={() => runTest()} className="btn-ghost">RETRY</button>
        </div>
      )}

      {result && !loading && (
        <div className="space-y-4">
          {/* verdict stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 fade-in stagger-1">
            <StatBlock meta={VERDICT_META.buy} data={result.summary.buy} />
            <StatBlock meta={VERDICT_META.hold} data={result.summary.hold} />
            <StatBlock meta={VERDICT_META.sell} data={result.summary.sell} />
          </div>

          {/* headline numbers */}
          <div className="panel fade-in stagger-2">
            <div className="panel-header"><span>Performance</span></div>
            <div className="p-4 grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="text-bright font-bold text-2xl tabular-nums">
                  {result.directional_accuracy === null ? '—' : `${result.directional_accuracy}%`}
                </div>
                <div className="text-muted text-[10px] tracking-widest mt-1">DIR. ACCURACY</div>
              </div>
              <div>
                <div
                  className="font-bold text-2xl tabular-nums"
                  style={{ color: result.baseline.spread_buy_vs_sell_pct >= 0 ? UP : DOWN }}
                >
                  {result.baseline.spread_buy_vs_sell_pct > 0 ? '+' : ''}{result.baseline.spread_buy_vs_sell_pct}%
                </div>
                <div className="text-muted text-[10px] tracking-widest mt-1">BUY−SELL SPREAD</div>
              </div>
              <div>
                <div className="text-bright font-bold text-2xl tabular-nums">{result.total_signals}</div>
                <div className="text-muted text-[10px] tracking-widest mt-1">SIGNALS</div>
              </div>
            </div>
          </div>

          {/* equity chart */}
          <div className="panel fade-in stagger-3">
            <div className="panel-header">
              <span>Equity Curve — Cumulative P&L</span>
              <span className="text-muted font-normal normal-case tracking-normal">{result.period}</span>
            </div>
            <div className="p-4">
              <EquityChart trades={result.trades} horizon={result.horizon_days} />
            </div>
          </div>

          <div className="w-full flex justify-center pt-2">
            <p className="text-muted text-[11px] leading-relaxed text-center max-w-2xl">
              Each day is scored using only prior data, then checked against the realized {result.horizon_days}-day return.
              Green dots: verdict expectation met. Red dots: missed. The curve shows cumulative P&L of taking every signal
              (long BUY / short SELL / flat HOLD). Positive spread = the rules add value for this ticker.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
