# MarketPulse

A web app for technical analysis of stocks and indices from global exchanges. Search for any symbol, get real-time indicator computations, individual signal scores, and an aggregated Bullish/Bearish/Neutral verdict.

**No price prediction, no ML, no forecasting.** Purely deterministic rule-based technical analysis. Indicators are lagging calculations with no predictive power. Not investment advice.

---

## Features

- **Global Symbol Search** — Autocomplete across 20+ exchanges (NASDAQ, NYSE, NSE, BSE, LSE, TSE, HKEX, TSX, XETRA, ASX, and more) plus major indices (S&P 500, Nifty 50, FTSE 100, Nikkei 225, etc.)
- **18 Technical Indicators** — RSI, MACD, Stochastic, CCI, Williams %R, MFI, Aroon, ROC, TRIX, CMF (21-period), CHOP, Stochastic RSI, EMA50/EMA200, Bollinger Bands, Pivot Points, VWAP
- **Rule-Based Scoring** — Each indicator maps to a [-1, +1] score with Bullish/Bearish/Neutral label
- **Weighted Aggregation** — Category weights (Trend 40%, Momentum 35%, Volatility 25%) with ADX trend-strength gating
- **18-Indicator Scoring Engine** — analyze, backtest, and forecast endpoints all use the same scoring pipeline
- **CHOP Regime Gate** — CHOP >61.8 dampens TREND weight ×0.5, shifts to MOMENTUM; stacked on ADX gate
- **CMF 21-period** — Money Flow Index money-flow volume oscillator
- **Verdict Bands** — BUY ≥56, SELL ≤44 across 5 tickers (AAPL, MSFT, SBIN.NS, RELIANCE.NS, ^NSEI)
- **Backtest** — Walk-forward replay over 2y history with equity curve
- **Forecast** — 1σ probability ranges, probability of rise, best/worst historical extremes
- **Responsive/Fullscreen UI** — Fluid layout, no max-width caps, indicator cards wide, 2×2 forecast grid on xl, full-bleed header/footer

---

## Architecture

```
Frontend (React, Vite) → FastAPI → Stage 1: Data Fetch (yfinance)
                        → Stage 2: Indicator Computation (pure functions)
                        → Stage 3: Signal Scoring (pure functions)
                        → Stage 4: Aggregation (pure function with CHOP/ADX regime gates)
                        → JSON Response
```

All computation stages (2-4) are pure functions with no side effects — independently unit-testable.

---

## Screenshots

| Page | Location |
|------|----------|
| Home / Search | `frontend/public/screenshots/home-search.png` |
| Analyze Page | `frontend/public/screenshots/analyze-page.png` |
| Indicator Cards | `frontend/public/screenshots/indicator-cards.png` |
| Backtest View | `frontend/public/screenshots/backtest-view.png` |
| Forecast View | `frontend/public/screenshots/forecast-view.png` |

*Add screenshot images to `frontend/public/screenshots/` directory.*

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, FastAPI |
| Data | yfinance, pandas, pandas-ta |
| Frontend | React, Vite, Recharts |
| Deployment | Stateless backend (Render/Railway), Static frontend (Vercel/Netlify) |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### Backend

Run from the repository root (the app imports `backend.app.*`, so it must not be run from inside `backend/`):

```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8001
```

Or simply `./start.sh` to launch backend + frontend together.

API runs at `http://localhost:8001`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

---

## API Endpoints

### `GET /api/search?q={query}`

Search symbols across global exchanges.

**Response:**

```json
{
  "results": [
    { "name": "State Bank Of India", "exchange": "NSE", "ticker": "SBIN.NS", "type": "stock" },
    { "name": "State Bank Of India", "exchange": "BSE", "ticker": "500112.BO", "type": "stock" },
    { "name": "Nifty 50", "exchange": "INDEX", "ticker": "^NSEI", "type": "index" }
  ]
}
```

### `GET /api/analyze?ticker={ticker}`

Full technical analysis for a ticker.

**Response:**

```json
{
  "ticker": "SBIN.NS",
  "company_name": "State Bank Of India",
  "current_price": 812.45,
  "day_change_pct": 1.2,
  "as_of": "2026-09-05",
  "overall": {
    "bullish_pct": 68.4,
    "bearish_pct": 31.6,
    "verdict": "BUY",
    "trend_strength": "strong"
  },
  "indicators": {
    "rsi": { "value": 58.2, "score": 0.1, "label": "Neutral", "explanation": "..." },
    "macd": { "macd_line": 4.2, "signal_line": 3.1, "histogram": 1.1, "score": 0.8, "label": "Bullish", "explanation": "..." },
    ...
  }
}
```

### `GET /health`

Health check.

---

## Indicators & Formulas

All computed on daily OHLCV. Periods are configurable constants in `backend/app/constants.py`.

| Indicator | Parameters | Formula |
|-----------|------------|---------|
| **RSI** | 14-period | Wilder's smoothing (EMA-style, α=1/14) |
| **MACD** | 12, 26, 9 | EMA12 - EMA26, Signal = EMA9(MACD), Histogram = MACD - Signal |
| **Stochastic** | 14, 3, 3 | %K = SMA3(100×(Close-Low14)/(High14-Low14)), %D = SMA3(%K) |
| **ADX** | 14-period | Wilder's ADX via `pandas_ta` (library implementation) |
| **EMA50/EMA200** | 50, 200 | `close.ewm(span=N, adjust=False).mean()` |
| **Bollinger Bands** | 20, 2σ | Middle = SMA20, Upper/Lower = Middle ± 2×StdDev, %B = (Close-Lower)/(Upper-Lower) |
| **Pivot Points** | Classic | PP=(H+L+C)/3, R1=2×PP-L, S1=2×PP-H, R2=PP+(H-L), S2=PP-(H-L) |
| **VWAP** | 20-day rolling | Σ(TP×V)/ΣV where TP=(H+L+C)/3 — *approximation for daily data* |

---

## Scoring Rules

Each indicator → (score ∈ [-1, 1], label, explanation).

### RSI (14)
```
RSI > 70:  score = -1 × min((RSI-70)/15, 1)      # Overbought → Bearish
RSI < 30:  score = min((30-RSI)/15, 1)            # Oversold → Bullish
Else:      score = (50 - RSI) / 20                 # Mild lean centered at 50
```

### MACD (12,26,9)
```
base = +1 if MACD > Signal else -1
widening = |Hist[-1]| > |Hist[-2]|
score = base × (0.8 if widening else 0.4)
```

### Stochastic (14,3,3)
```
%K > 80:  score = -1 × min((%K-80)/15, 1)
%K < 20:  score = min((20-%K)/15, 1)
Else:     score = (50 - %K) / 30
Bonus: +0.3 if %K crosses above %D from below 20 (capped at ±1)
```

### ADX (14) — Trend Strength Gate Only
```
ADX > 25:  "strong"
ADX < 20:  "weak"
Else:      "moderate"
```
*Does not produce directional score — used as gate in aggregation.*

### Moving Averages (EMA50, EMA200)
```
Price > EMA50 & > EMA200:  score = 0.7
Price < EMA50 & < EMA200:  score = -0.7
Mixed:                     score = 0.2 if > EMA200 else -0.2
Golden cross (≤5 days):    score = min(score + 0.3, 1)
Death cross (≤5 days):     score = max(score - 0.3, -1)
```

### Bollinger Bands (%B)
```
%B > 1.0:     score = -0.6
%B < 0.0:     score = 0.6
%B > 0.8:     score = -0.3
%B < 0.2:     score = 0.3
Else:         score = 0
In strong trend: score ×= 0.5  (dampened — band-rides are continuation)
```

### Pivot Points
Informational only — no score.

### VWAP (20-day rolling approx.)
```
score = 0.4 if Price > VWAP else -0.4
Labelled as approximation in UI.
```

---

## Aggregation Logic

### Category Weights (Base)

| Category | Indicators | Weight |
|----------|------------|--------|
| TREND | MACD, EMA Signal | 0.40 |
| MOMENTUM | RSI, Stochastic | 0.35 |
| VOLATILITY | Bollinger | 0.25 |
| INFO_ONLY | Pivots, VWAP | Excluded |

### ADX Gating (applied before final weighting)

| Trend Strength | TREND Weight | MOMENTUM Weight | VOLATILITY Weight | Bollinger Dampen |
|----------------|--------------|-----------------|-------------------|------------------|
| Weak (ADX < 20) | ×0.5 | +removed weight | unchanged | 1.0× |
| Moderate | 0.40 | 0.35 | 0.25 | 1.0× |
| Strong (ADX > 25) | ×1.15 (capped) | redistributed | redistributed | 0.5× |

Weights renormalized to sum to 1.0.

### Final Score
```
category_score = average of member indicator scores
overall_score = Σ(category_score × adjusted_weight)  ∈ [-1, 1]
bullish_pct = (overall_score + 1) / 2 × 100
bearish_pct = 100 - bullish_pct
```

### Verdict Bands

| Bullish % | Verdict |
|-----------|---------|
| > 65 | BUY |
| < 35 | SELL |
| 35-65 | HOLD / NEUTRAL |

---

## Design Rationale (Required by Spec)

### Weighting Scheme (0.40 / 0.35 / 0.25)

Deliberate design choice, not arbitrary defaults:
- **Trend (40%)**: MACD + EMA crossover capture primary trend direction — highest weight because trend-following has the strongest theoretical basis in technical analysis.
- **Momentum (35%)**: RSI + Stochastic measure overbought/oversold and momentum shifts — slightly lower because momentum signals are mean-reverting and less reliable in strong trends.
- **Volatility (25%)**: Bollinger Bands alone — lowest weight because %B is a mean-reversion tool that fails in trending markets (hence the ADX dampening).

### ADX Gating Logic

- **Weak trend (ADX < 20)**: Market is ranging. Trend-following indicators (MACD, EMA) produce whipsaws → reduce TREND weight by 50%, shift to MOMENTUM (mean-reversion works better in ranges).
- **Strong trend (ADX > 25)**: Trend-following is reliable → boost TREND weight by 15%. Bollinger band touches are continuation signals, not reversals → dampen VOLATILITY score by 50%.
- **Moderate**: Base weights.

This is a *design choice with explicit reasoning*, not an arbitrary default.

### VWAP Approximation

VWAP is computed over a 20-day rolling window on daily bars, **not** true intraday session VWAP. It is labeled `is_approximation: true` in the API and "(approx.)" in the UI. True VWAP requires intraday data with session reset.

### Supported Exchanges (v1)

| Exchange | Suffix | Example |
|----------|--------|---------|
| NASDAQ/NYSE (US) | (none) | AAPL, MSFT |
| NSE (India) | .NS | SBIN.NS, RELIANCE.NS |
| BSE (India) | .BO | 500112.BO |
| LSE (London) | .L | VOD.L |
| TSE (Tokyo) | .T | 7203.T |
| HKEX (Hong Kong) | .HK | 0700.HK |
| TSX (Toronto) | .TO | SHOP.TO |
| XETRA (Germany) | .DE | SAP.DE |
| ASX (Australia) | .AX | BHP.AX |
| SGX (Singapore) | .SI | D05.SI |
| Euronext (Paris) | .PA | AIR.PA |
| SIX (Switzerland) | .SW | NESN.SW |
| BME (Madrid) | .MC | IBE.MC |
| OMX (Stockholm) | .ST | ERIC-B.ST |
| JSE (Johannesburg) | .JO | NPN.JO |
| B3 (Brazil) | .SA | PETR4.SA |
| KRX (Korea) | .KS | 005930.KS |
| TWSE (Taiwan) | .TW | 2330.TW |
| Shanghai Composite | 000001.SS |

Symbol search uses yfinance's unofficial `yf.Search()` endpoint (primary) with a bundled fallback list of ~30 major tickers. The live endpoint is reverse-engineered and may change or rate-limit without notice.

### Supported Indices (bundled locally)

| Index | Symbol |
|-------|--------|
| S&P 500 | ^GSPC |
| Dow Jones | ^DJI |
| Nasdaq | ^IXIC |
| FTSE 100 | ^FTSE |
| Nikkei 225 | ^N225 |
| DAX | ^GDAXI |
| Nifty 50 | ^NSEI |
| Sensex | ^BSESN |
| Hang Seng | ^HSI |
| CAC 40 | ^FCHI |
| ASX 200 | ^AXJO |
| KOSPI | ^KS11 |
| Taiwan Weighted | ^TWII |
| Shanghai Composite | 000001.SS |

---

## Disclaimer

> **This is technical analysis, not investment advice.** Indicators are lagging, rule-based calculations with no predictive power. The weighting scheme and scoring rules are deliberate design choices for demonstration purposes. Past indicator behavior does not guarantee future results. Do not trade real money based on this dashboard.

---

## Project Structure

```
MarketPulse/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── aggregation/      # Stage 4: weighted aggregation + ADX/CHOP gating
│   │   ├── constants.py      # All periods, weights, thresholds
│   │   ├── data_fetch/       # Stage 1: yfinance wrapper + validation
│   │   ├── indicators/       # Stage 2: 18 pure computation functions
│   │   ├── scoring/          # Stage 3: 18 pure scoring functions
│   │   ├── search/           # Symbol search (live + fallback)
│   │   └── main.py           # FastAPI app + /api/search, /api/analyze, /api/backtest, /api/forecast
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchBox.jsx      # Autocomplete with live search
│   │   │   ├── IndicatorCards.jsx # Verdict gauge + indicator grid
│   │   │   ├── BacktestPanel.jsx  # Walk-forward backtest view
│   │   │   └── ForecastPanel.jsx  # Forecast 1σ grid view
│   │   ├── App.jsx                # Main dashboard, layout, views
│   │   └── main.jsx
│   └── package.json
├── .gitignore
├── README.md
└── start.sh
```

---

## Development

### Run Tests

```bash
# Backend unit tests
cd backend
python -c "
from app.indicators import *
from app.scoring import *
from app.aggregation import *
print('All imports OK')
# Run scoring tests
from app.scoring import score_rsi, score_macd, ...
"

# Frontend
cd frontend
npm run build  # TypeScript/type check
```

### Configuration

Edit `backend/app/constants.py` to adjust:
- Indicator periods (RSI, MACD, Stochastic, ADX, EMA, Bollinger, VWAP, CMF, CHOP)
- Category weights and ADX thresholds
- Verdict bands (BUY/HOLD/SELL)
- Exchange suffix mapping
- CHOP regime gate thresholds

---

## License

MIT — For educational and research purposes only.