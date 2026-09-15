import json
import os
from typing import List, Dict, Any
import yfinance as yf
from backend.app.constants import EXCHANGE_SUFFIXES, INDICES
SEARCH_CACHE_FILE = os.path.join(os.path.dirname(__file__), 'search_cache.json')
CACHE_DURATION_HOURS = 4
FALLBACK_TICKERS_FILE = os.path.join(os.path.dirname(__file__), 'fallback_tickers.json')
EXCHANGE_CURRENCIES = {
    'NMS': 'USD', 'NYQ': 'USD', 'NGM': 'USD', 'BTS': 'USD', 'PCX': 'USD', 'ASE': 'USD', 'AMX': 'USD', 'OQB': 'USD',
    'TOR': 'CAD', 'TSX': 'CAD', 'VAN': 'CAD',
    'BUE': 'ARS', 'SAO': 'BRL', 'BMF': 'BRL', 'MEX': 'MXN',
    'LSE': 'GBp', 'LDN': 'GBp', 'GER': 'EUR', 'XETRA': 'EUR', 'FRA': 'EUR', 'EURONEXT': 'EUR', 'PAR': 'EUR', 'PA': 'EUR',
    'SWX': 'CHF', 'SIX': 'CHF', 'MAD': 'EUR', 'BME': 'EUR', 'STO': 'SEK', 'OMX': 'SEK', 'HEL': 'EUR',
    'OSL': 'NOK', 'CPH': 'DKK', 'ISE': 'EUR', 'WSE': 'PLN', 'PRG': 'CZK', 'BUD': 'HUF',
    'NSI': 'INR', 'NSE': 'INR', 'BSE': 'INR', 'BOM': 'INR', 'CAL': 'INR',
    'JPX': 'JPY', 'TSE': 'JPY', 'JP': 'JPY',
    'HKG': 'HKD', 'HKEX': 'HKD',
    'SHH': 'CNY', 'SHZ': 'CNY', 'CSS': 'CNY',
    'KSC': 'KRW', 'KRX': 'KRW', 'KOSDAQ': 'KRW',
    'TAI': 'TWD', 'TWSE': 'TWD',
    'ASX': 'AUD', 'AX': 'AUD', 'NZE': 'NZD', 'NZX': 'NZD',
    'SGX': 'SGD', 'SI': 'SGD',
    'TLV': 'ILS', 'DSE': 'AED', 'TAD': 'SAR', 'JNB': 'ZAR', 'JSE': 'ZAR',
    'INDEX': '',
    'NDX': 'USD', 'DJI': 'USD', 'SPX': 'USD',
}
INDEX_CURRENCIES = {
    '^GSPC': 'USD', '^DJI': 'USD', '^IXIC': 'USD', '^FTSE': 'GBp', '^NSEI': 'INR',
    '^BSESN': 'INR', '^N225': 'JPY', '^GDAXI': 'EUR', '^HSI': 'HKD', '^FCHI': 'EUR',
    '^AXJO': 'AUD', '^KS11': 'KRW', '^TWII': 'TWD', '000001.SS': 'CNY',
}
def get_currency_for_result(exchange: str, ticker: str) -> str:
    if ticker in INDEX_CURRENCIES:
        return INDEX_CURRENCIES[ticker]
    return EXCHANGE_CURRENCIES.get(exchange, '')
def load_fallback_tickers() -> List[Dict[str, str]]:
    try:
        with open(FALLBACK_TICKERS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []
def create_fallback_tickers():
    fallback = [
        {"name": "Apple Inc.", "exchange": "NASDAQ", "ticker": "AAPL"},
        {"name": "Microsoft Corporation", "exchange": "NASDAQ", "ticker": "MSFT"},
        {"name": "Amazon.com Inc.", "exchange": "NASDAQ", "ticker": "AMZN"},
        {"name": "Alphabet Inc.", "exchange": "NASDAQ", "ticker": "GOOGL"},
        {"name": "Meta Platforms Inc.", "exchange": "NASDAQ", "ticker": "META"},
        {"name": "Tesla Inc.", "exchange": "NASDAQ", "ticker": "TSLA"},
        {"name": "NVIDIA Corporation", "exchange": "NASDAQ", "ticker": "NVDA"},
        {"name": "Berkshire Hathaway Inc.", "exchange": "NYSE", "ticker": "BRK.B"},
        {"name": "JPMorgan Chase & Co.", "exchange": "NYSE", "ticker": "JPM"},
        {"name": "Johnson & Johnson", "exchange": "NYSE", "ticker": "JNJ"},
        {"name": "State Bank of India", "exchange": "NSE", "ticker": "SBIN.NS"},
        {"name": "State Bank of India", "exchange": "BSE", "ticker": "500112.BO"},
        {"name": "Reliance Industries Ltd.", "exchange": "NSE", "ticker": "RELIANCE.NS"},
        {"name": "HDFC Bank Ltd.", "exchange": "NSE", "ticker": "HDFCBANK.NS"},
        {"name": "Infosys Ltd.", "exchange": "NSE", "ticker": "INFY.NS"},
        {"name": "TCS Ltd.", "exchange": "NSE", "ticker": "TCS.NS"},
        {"name": "Vodafone Group Plc", "exchange": "LSE", "ticker": "VOD.L"},
        {"name": "Toyota Motor Corp", "exchange": "TSE", "ticker": "7203.T"},
        {"name": "Sony Group Corp", "exchange": "TSE", "ticker": "6758.T"},
        {"name": "Tencent Holdings Ltd.", "exchange": "HKEX", "ticker": "0700.HK"},
        {"name": "Shopify Inc.", "exchange": "TSX", "ticker": "SHOP.TO"},
        {"name": "SAP SE", "exchange": "XETRA", "ticker": "SAP.DE"},
        {"name": "BHP Group Ltd.", "exchange": "ASX", "ticker": "BHP.AX"},
        {"name": "DBS Group Holdings", "exchange": "SGX", "ticker": "D05.SI"},
        {"name": "Airbus SE", "exchange": "EURONEXT", "ticker": "AIR.PA"},
        {"name": "Nestle SA", "exchange": "SIX", "ticker": "NESN.SW"},
        {"name": "Iberdrola SA", "exchange": "BME", "ticker": "IBE.MC"},
        {"name": "Ericsson AB", "exchange": "OMX", "ticker": "ERIC-B.ST"},
        {"name": "Naspers Ltd.", "exchange": "JSE", "ticker": "NPN.JO"},
        {"name": "Petrobras", "exchange": "BMF", "ticker": "PETR4.SA"},
        {"name": "Samsung Electronics", "exchange": "KRX", "ticker": "005930.KS"},
        {"name": "TSMC", "exchange": "TWSE", "ticker": "2330.TW"},
    ]
    os.makedirs(os.path.dirname(FALLBACK_TICKERS_FILE), exist_ok=True)
    with open(FALLBACK_TICKERS_FILE, 'w') as f:
        json.dump(fallback, f, indent=2)
    return fallback
def load_cache() -> Dict[str, Any]:
    try:
        with open(SEARCH_CACHE_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}
def save_cache(cache: Dict[str, Any]):
    try:
        os.makedirs(os.path.dirname(SEARCH_CACHE_FILE), exist_ok=True)
        with open(SEARCH_CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except Exception:
        pass
def search_yfinance(query: str) -> List[Dict[str, str]]:
    try:
        results = yf.Search(query, max_results=20)
        quotes = results.quotes if hasattr(results, 'quotes') else []
        formatted = []
        for q in quotes:
            symbol = q.get('symbol', '')
            name = q.get('longname') or q.get('shortname') or q.get('name') or symbol
            exchange = q.get('exchange', '')
            quote_type = q.get('quoteType', '').upper()
            if not symbol or not name:
                continue
            formatted.append({
                "name": name,
                "exchange": exchange,
                "ticker": symbol,
                "type": "index" if quote_type == "INDEX" else "stock"
            })
        return formatted
    except Exception:
        return []
def search_indices(query: str) -> List[Dict[str, str]]:
    query_lower = query.lower()
    results = []
    for name, ticker in INDICES.items():
        if query_lower in name.lower() or query_lower in ticker.lower():
            results.append({
                "name": name,
                "exchange": "INDEX",
                "ticker": ticker,
                "type": "index"
            })
    return results
def search_fallback(query: str) -> List[Dict[str, str]]:
    fallback = load_fallback_tickers()
    if not fallback:
        fallback = create_fallback_tickers()
    query_lower = query.lower()
    results = []
    for item in fallback:
        if query_lower in item['name'].lower() or query_lower in item['ticker'].lower():
            results.append({
                "name": item['name'],
                "exchange": item['exchange'],
                "ticker": item['ticker'],
                "type": "stock"
            })
    return results
def search_symbols(query: str) -> List[Dict[str, str]]:
    if not query or len(query.strip()) < 1:
        return []
    cache = load_cache()
    cache_key = query.lower().strip()
    if cache_key in cache:
        return [attach_currency(r) for r in cache[cache_key]]
    results = []
    yf_results = search_yfinance(query)
    results.extend(yf_results)
    index_results = search_indices(query)
    results.extend(index_results)
    seen = set()
    unique_results = []
    for r in results:
        key = (r['ticker'], r['name'], r['exchange'])
        if key not in seen:
            seen.add(key)
            unique_results.append(r)
    if not unique_results:
        fallback_results = search_fallback(query)
        for r in fallback_results:
            key = (r['ticker'], r['name'], r['exchange'])
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
    unique_results = unique_results[:20]
    cache[cache_key] = unique_results
    save_cache(cache)
    return [attach_currency(r) for r in unique_results]
def attach_currency(result: Dict[str, str]) -> Dict[str, str]:
    if not result.get('currency'):
        result['currency'] = get_currency_for_result(result.get('exchange', ''), result.get('ticker', ''))
    return result