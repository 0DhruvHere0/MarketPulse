import { useState, useEffect } from 'react';
import { SearchBox } from './components/SearchBox';
import { HeaderCard, VerdictGauge, IndicatorCard } from './components/IndicatorCards';
import { SimulationView } from './components/ForecastPanel';
import { DEITY_MAP } from './deities';
import { RefreshCw, TrendingUp, TrendingDown } from 'lucide-react';
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001/api';
function fmt(val, decimals = 2) {
  if (val === null || val === undefined) return '—';
  return typeof val === 'number' ? val.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) : val;
}
function getIndicatorValues(indicator, type) {
  switch (type) {
    case 'rsi': return [{ label: 'RSI', value: fmt(indicator.value, 1) }];
    case 'macd': return [
      { label: 'MACD Line', value: fmt(indicator.macd_line, 2) },
      { label: 'Signal Line', value: fmt(indicator.signal_line, 2) },
      { label: 'Histogram', value: fmt(indicator.histogram, 2) },
    ];
    case 'stochastic': return [
      { label: '%K', value: fmt(indicator.k, 1) },
      { label: '%D', value: fmt(indicator.d, 1) },
    ];
    case 'adx': return [
      { label: 'ADX', value: fmt(indicator.value, 1) },
      { label: 'Trend Strength', value: indicator.trend_strength },
    ];
    case 'moving_averages': return [
      { label: 'EMA 50', value: fmt(indicator.ema50, 1) },
      { label: 'EMA 200', value: fmt(indicator.ema200, 1) },
    ];
    case 'bollinger': return [
      { label: 'Upper Band', value: fmt(indicator.upper, 1) },
      { label: 'Middle (SMA20)', value: fmt(indicator.middle, 1) },
      { label: 'Lower Band', value: fmt(indicator.lower, 1) },
      { label: '%B Position', value: fmt(indicator.percent_b, 2) },
    ];
    case 'pivots': return [
      { label: 'Pivot (PP)', value: fmt(indicator.pp, 1) },
      { label: 'Resistance 1', value: fmt(indicator.r1, 1) },
      { label: 'Resistance 2', value: fmt(indicator.r2, 1) },
      { label: 'Support 1', value: fmt(indicator.s1, 1) },
      { label: 'Support 2', value: fmt(indicator.s2, 1) },
      { label: 'Position', value: indicator.position },
      { label: 'Nearest Level', value: indicator.nearest_level },
    ];
    case 'vwap': return [
      { label: 'VWAP (20D approx.)', value: fmt(indicator.value, 1) },
      { label: 'Type', value: indicator.is_approximation ? 'Approximation (Daily)' : 'Intraday' },
    ];
    case 'cci': return [{ label: 'CCI', value: fmt(indicator.value, 1) }];
    case 'williams_r': return [{ label: 'Williams %R', value: fmt(indicator.value, 1) }];
    case 'obv': return [{ label: 'OBV (cumulative)', value: fmt(indicator.value, 0) }];
    case 'mfi': return [{ label: 'MFI', value: fmt(indicator.value, 1) }];
    case 'aroon': return [
      { label: 'Aroon Up', value: fmt(indicator.up, 0) },
      { label: 'Aroon Down', value: fmt(indicator.down, 0) },
    ];
    case 'roc': return [{ label: 'Rate of Change (12D)', value: `${indicator.value > 0 ? '+' : ''}${fmt(indicator.value, 1)}%` }];
    case 'trix': return [
      { label: 'TRIX (15)', value: fmt(indicator.trix, 1) },
      { label: 'Signal (9)', value: fmt(indicator.signal, 1) },
    ];
    case 'cmf': return [{ label: 'Chaikin Money Flow (21)', value: fmt(indicator.value, 2) }];
    case 'chop': return [
      { label: 'Choppiness Index (14)', value: fmt(indicator.value, 1) },
      { label: 'Regime', value: (indicator.regime || '—').toUpperCase() },
    ];
    case 'stoch_rsi': return [
      { label: 'StochRSI %K', value: fmt(indicator.k, 1) },
      { label: 'StochRSI %D', value: fmt(indicator.d, 1) },
    ];
    default: return [];
  }
}
const LOAD_MESSAGES = [
  'FETCHING OHLCV…',
  'COMPUTING INDICATORS…',
  'SCORING SIGNALS…',
  'AGGREGATING VERDICT…',
];
function LoadingState({ symbol }) {
  const [i, setI] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setI(p => (p + 1) % LOAD_MESSAGES.length), 700);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="panel p-12 text-center max-w-xl mx-auto fade-in">
      <div className="text-amber font-bold tracking-widest animate-[blink_1s_infinite]">{LOAD_MESSAGES[i]}</div>
      <p className="text-muted text-xs mt-2">{symbol?.ticker}</p>
    </div>
  );
}
function ErrorState({ error, onRetry }) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="panel max-w-md mx-4 fade-in" style={{ borderColor: 'rgba(255,46,46,0.4)' }}>
        <div className="panel-header"><span style={{ color: DOWN_COLOR }}>Error</span></div>
        <div className="p-8 text-center">
          <p className="text-muted text-sm mb-6">{error}</p>
          <button onClick={onRetry} className="btn-amber">
            <RefreshCw className="w-3.5 h-3.5 mr-2" />
            RETRY
          </button>
        </div>
      </div>
    </div>
  );
}
const DOWN_COLOR = '#ff2e2e';
function HomeView({ onAnalyze }) {
  return (
    <div className="min-h-[65vh] w-full grid place-items-center fade-in">
      <div className="flex flex-col items-center text-center w-full max-w-2xl mx-auto px-2">
        <h1 className="text-bright font-bold text-3xl md:text-4xl tracking-widest">
          MARKET<span className="text-amber">PULSE</span>
        </h1>
        <p className="text-muted text-xs tracking-[0.3em] mt-2 mb-10">ㅤ</p>
        <div className="w-full flex justify-center">
          <SearchBox onSelect={onAnalyze} />
        </div>
      </div>
    </div>
  );
}
function AnalyzeView({ symbol, analysis, loading, error, onRetry, onToggleCard, expandedCards, onGoHome }) {
  return (
    <>
      {loading && !analysis && (
        <div className="flex justify-center py-8">
          <div className="w-full max-w-xl"><LoadingState symbol={symbol} /></div>
        </div>
      )}
      {error && !analysis && (
        <div className="flex justify-center py-8">
          <div className="w-full max-w-md"><ErrorState error={error} onRetry={onRetry} /></div>
        </div>
      )}
      {analysis && (
        <div className="w-full flex flex-col items-center gap-4">
          <div className="w-full grid grid-cols-1 lg:grid-cols-3 gap-4 fade-in">
            <div className="lg:col-span-2 min-w-0">
              <HeaderCard
                ticker={analysis.ticker}
                companyName={analysis.company_name}
                currentPrice={analysis.current_price}
                dayChangePct={analysis.day_change_pct}
                asOf={analysis.as_of}
                currency={analysis.currency}
              />
            </div>
            <VerdictGauge overall={analysis.overall} />
          </div>
          <div className="w-full panel fade-in stagger-2">
            <div className="panel-header">
              <span>Indicators — 18 Signals</span>
              <span className="text-muted font-normal normal-case tracking-normal">click row for detail</span>
            </div>
            <div className="p-2 space-y-1.5">
              {Object.values(DEITY_MAP).map((config) => {
                const indicator = analysis.indicators[config.key];
                if (!indicator) return null;
                return (
                  <IndicatorCard
                    key={config.key}
                    indicator={indicator}
                    title={config.label}
                    values={getIndicatorValues(indicator, config.key)}
                    showScore={!['adx', 'pivots', 'chop'].includes(config.key)}
                    keyName={config.key}
                    isExpanded={expandedCards.has(config.key)}
                    onToggle={() => onToggleCard(config.key)}
                  />
                );
              })}
            </div>
          </div>
          <div className="w-full flex justify-center mt-2 fade-in stagger-3">
            <button onClick={onGoHome} className="btn-ghost">
              ← NEW TICKER
            </button>
          </div>
        </div>
      )}
    </>
  );
}
export default function App() {
  const [page, setPage] = useState('home'); // home | analyze | simulate
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [simSymbol, setSimSymbol] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedCards, setExpandedCards] = useState(new Set());
  const handleSymbolSelect = async (symbol) => {
    setSelectedSymbol(symbol);
    setAnalysis(null);
    setError(null);
    setLoading(true);
    setExpandedCards(new Set(['rsi', 'macd']));
    setPage('analyze');
    try {
      const res = await fetch(`${API_BASE}/analyze?ticker=${encodeURIComponent(symbol.ticker)}`);
      const data = await res.json();
      if (data.detail) {
        setError(data.detail.error || 'No data for this symbol');
      } else {
        setAnalysis(data);
      }
    } catch {
      setError('Cannot reach the backend. Ensure it runs on port 8001.');
    } finally {
      setLoading(false);
    }
  };
  const goHome = () => {
    setPage('home');
    setSelectedSymbol(null);
    setAnalysis(null);
    setError(null);
    setSimSymbol(null);
  };
  const toggleCard = (key) => {
    setExpandedCards(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-term-border bg-term-panel sticky top-0 z-40">
        <div className="w-full px-4 md:px-6 lg:px-8 py-0 flex items-center justify-between">
          <button onClick={goHome} className="flex items-center gap-3 py-2.5 group" aria-label="Go to home">
            <span className="font-bold text-sm tracking-widest text-bright group-hover:text-amber transition-colors">
              MARKET<span className="text-amber group-hover:text-bright transition-colors">PULSE</span>
            </span>
          </button>
          <nav className="flex items-center">
            <button onClick={goHome} className={`tab ${page === 'home' || page === 'analyze' ? 'tab-active' : ''}`}>
              <TrendingUp className="w-3.5 h-3.5 inline mr-1.5" />
              Analyze
            </button>
            <button onClick={() => setPage('simulate')} className={`tab ${page === 'simulate' ? 'tab-active' : ''}`}>
              <TrendingDown className="w-3.5 h-3.5 inline mr-1.5" />
              Simulation
            </button>
          </nav>
        </div>
      </header>
      <main className="flex-1 w-full px-4 md:px-6 lg:px-8 py-6">
        {page === 'home' && <HomeView onAnalyze={handleSymbolSelect} />}
        {page === 'analyze' && (
          <AnalyzeView
            symbol={selectedSymbol}
            analysis={analysis}
            loading={loading}
            error={error}
            onRetry={() => selectedSymbol && handleSymbolSelect(selectedSymbol)}
            onToggleCard={toggleCard}
            expandedCards={expandedCards}
            onGoHome={goHome}
          />
        )}
        {page === 'simulate' && !simSymbol && (
          <div className="min-h-[65vh] w-full grid place-items-center fade-in">
            <div className="flex flex-col items-center text-center w-full max-w-2xl mx-auto px-2">
              <h1 className="text-bright font-bold text-3xl tracking-widest">
                SIM<span className="text-amber">ULATION</span>
              </h1>
              <p className="text-muted text-xs tracking-[0.3em] mt-2 mb-10">
                BACKTEST · FORECAST · PROBABILITY
              </p>
              <div className="w-full flex justify-center">
                <SearchBox
                  onSelect={(s) => setSimSymbol(s)}
                  placeholder="ENTER TICKER TO SIMULATE  —  e.g. AAPL, SBIN, ^NSEI"
                />
              </div>
            </div>
          </div>
        )}
        {page === 'simulate' && simSymbol && (
          <SimulationView symbol={simSymbol} onBack={() => setSimSymbol(null)} />
        )}
      </main>
      <footer className="border-t border-term-border bg-term-panel">
        <div className="w-full px-4 md:px-6 lg:px-8 py-3 flex items-center justify-between text-[11px] text-muted">
          <span>MARKETPULSE TERMINAL</span>
          <span className="flex items-center gap-2">
            <span className="text-up">● LIVE</span>
          </span>
        </div>
      </footer>
    </div>
  );
}