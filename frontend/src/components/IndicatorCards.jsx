import { TrendingUp, TrendingDown, Minus, ChevronDown } from 'lucide-react';
import { DEITY_MAP, getVerdictStyle, getScoreBadge, scoreColor } from '../deities';

function fmt(val, decimals = 2) {
  if (val === null || val === undefined) return '—';
  return typeof val === 'number' ? val.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) : val;
}

/* ---------- Header: ticker strip ---------- */
export function HeaderCard({ ticker, companyName, currentPrice, dayChangePct, asOf, currency }) {
  const isPositive = dayChangePct >= 0;
  return (
    <div className="panel fade-in h-full">
      <div className="panel-header">
        <span>{ticker}</span>
        <span className="text-muted font-normal normal-case tracking-normal">{asOf}</span>
      </div>
      <div className="p-6 flex flex-wrap items-center justify-between gap-6">
        <div className="min-w-0">
          <div className="text-amber font-bold text-xl tracking-widest">{ticker}</div>
          <div className="text-muted text-xs mt-1 truncate">{companyName}</div>
          {currency && (
            <div className="text-muted text-[10px] tracking-widest mt-1">{currency}</div>
          )}
        </div>
        <div className="text-right">
          <div className="text-bright font-bold text-4xl md:text-5xl tabular-nums leading-none">
            {fmt(currentPrice)}
          </div>
          <div className={`flex items-center gap-2 mt-3 justify-end font-bold ${isPositive ? 'text-up' : 'text-down'}`}>
            {isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
            <span className="tabular-nums text-xl">{isPositive ? '+' : ''}{dayChangePct.toFixed(2)}%</span>
            <span className="text-muted text-xs font-normal">1D</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- Verdict panel ---------- */
export function VerdictGauge({ overall }) {
  const { bullish_pct: bullishPct, bearish_pct: bearishPct, verdict, trend_strength: trendStrength, chop_regime: chopRegime } = overall;
  const vStyle = getVerdictStyle(verdict);
  const isBuy = verdict === 'BUY';
  const isSell = verdict === 'SELL';
  const Icon = isBuy ? TrendingUp : isSell ? TrendingDown : Minus;
  const vColor = isBuy ? 'var(--color-up)' : isSell ? 'var(--color-down)' : 'var(--color-amber)';

  return (
    <div className="panel fade-in stagger-1 h-full">
      <div className="panel-header">
        <span>Aggregate Signal</span>
        <span className="text-muted font-normal normal-case tracking-normal">ADX: {trendStrength}{chopRegime && chopRegime !== 'unknown' ? ` · CHOP: ${chopRegime}` : ''}</span>
      </div>
      <div className="p-6 text-center">
        <div className={`badge ${vStyle.badge} mx-auto`} style={{ fontSize: 16, padding: '6px 20px' }}>
          <Icon className="w-5 h-5" />
          {verdict === 'HOLD / NEUTRAL' ? 'HOLD' : verdict}
        </div>

        {/* bullish/bearish bar */}
        <div className="mt-6">
          <div className="flex justify-between text-[11px] font-bold mb-1.5">
            <span className="text-up tabular-nums">BULL {bullishPct.toFixed(1)}%</span>
            <span className="text-down tabular-nums">BEAR {bearishPct.toFixed(1)}%</span>
          </div>
          <div className="h-4 flex border border-term-border-hi overflow-hidden">
            <div
              className="h-full transition-all duration-1000"
              style={{ width: `${bullishPct}%`, background: 'linear-gradient(90deg, rgba(0,210,106,0.25), rgba(0,210,106,0.75))' }}
            />
            <div
              className="h-full flex-1 transition-all duration-1000"
              style={{ background: 'linear-gradient(90deg, rgba(255,46,46,0.75), rgba(255,46,46,0.25))' }}
            />
          </div>
          {/* 56/44 verdict thresholds */}
          <div className="relative h-4 -mt-4 pointer-events-none">
            <div className="absolute top-0 bottom-0 w-px bg-muted/60" style={{ left: '44%' }} />
            <div className="absolute top-0 bottom-0 w-px bg-muted/60" style={{ left: '56%' }} />
          </div>
          <div className="flex justify-between text-[10px] text-muted mt-1">
            <span>SELL &lt; 44%</span>
            <span>HOLD BAND</span>
            <span>BUY &gt; 56%</span>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-term-border grid grid-cols-3 gap-2 text-center">
          <div>
            <div className="text-up font-bold tabular-nums text-lg">{bullishPct.toFixed(1)}%</div>
            <div className="text-muted text-[10px] tracking-widest">BULLISH</div>
          </div>
          <div>
            <div className="font-bold tabular-nums text-lg" style={{ color: vColor }}>{verdict === 'HOLD / NEUTRAL' ? 'HOLD' : verdict}</div>
            <div className="text-muted text-[10px] tracking-widest">VERDICT</div>
          </div>
          <div>
            <div className="text-down font-bold tabular-nums text-lg">{bearishPct.toFixed(1)}%</div>
            <div className="text-muted text-[10px] tracking-widest">BEARISH</div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- Indicator table row ---------- */
export function IndicatorCard({ indicator, title, values, showScore = true, keyName, isExpanded = false, onToggle }) {
  const d = DEITY_MAP[keyName] || { label: title, deity: '', period: '', category: '' };
  const score = showScore ? indicator.score : null;
  const sc = score !== null && score !== undefined ? getScoreBadge(score) : null;
  const ScIcon = sc?.icon;
  const color = scoreColor(score ?? 0);

  // score bar: fill from center — right for +, left for −
  const pct = Math.min(Math.abs(score ?? 0), 1) * 50;
  const fillStyle = (score ?? 0) >= 0
    ? { left: '50%', width: `${pct}%`, background: color }
    : { right: '50%', width: `${pct}%`, background: color };

  // compact inline summary of first two values
  const inline = values.slice(0, 2).map(v => `${v.label.split(' ')[0]} ${v.value}`).join('  ·  ');

  return (
    <div className="panel fade-in">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={isExpanded}
        className="w-full text-left cursor-pointer select-none px-4 py-3 flex items-center gap-4 hover:bg-term-panel2 transition-colors"
      >
        <span className="text-amber font-bold text-sm w-24 flex-shrink-0">{d.label}</span>
        <span className="chip flex-shrink-0 hidden lg:inline-flex">{d.category}</span>
        <span className="text-muted text-[10px] w-16 flex-shrink-0 hidden md:inline">{d.period}</span>
        <span className="text-muted text-[10px] flex-1 truncate hidden xl:inline">{inline}</span>
        {sc && (
          <span className={`badge ${sc.badge} flex-shrink-0`}>
            {ScIcon && <ScIcon className="w-3 h-3" />}
            <span className="hidden sm:inline">{sc.label}</span>
          </span>
        )}
        {score !== null && score !== undefined && (
          <span className="score-bar flex-shrink-0 hidden sm:block">
            <span className="score-bar-zero" />
            <span className="score-bar-fill" style={fillStyle} />
          </span>
        )}
        <span className="tabular-nums text-xs w-10 text-right flex-shrink-0" style={{ color }}>
          {score !== null && score !== undefined ? score.toFixed(2) : '—'}
        </span>
        <ChevronDown className={`w-4 h-4 text-muted flex-shrink-0 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`} />
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 pt-1 border-t border-term-border bg-term-panel2/40">
          <div className="pt-3 grid gap-x-8 md:grid-cols-2">
            {values.map((v, i) => (
              <div key={i} className="data-row">
                <span className="data-label">{v.label}</span>
                <span className="data-value">{v.value}</span>
              </div>
            ))}
          </div>
          {indicator.explanation && (
            <p className="mt-3 text-xs text-muted leading-relaxed border-l-2 border-amber/50 pl-3">
              {indicator.explanation}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
