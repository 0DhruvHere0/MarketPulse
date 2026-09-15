import { useState, useEffect, useRef, useCallback } from 'react';
import { Search, Loader2, X } from 'lucide-react';

const API_BASE = 'http://localhost:8001/api';

export function SearchBox({ onSelect, placeholder = 'ENTER TICKER / COMPANY  —  e.g. AAPL, SBIN, ^NSEI' }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);
  const debounceRef = useRef(null);

  const fetchResults = useCallback(async (q) => {
    if (!q) { setResults([]); setShowDropdown(false); return; }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      setResults((data.results || []).slice(0, 8));
      setSelectedIndex(-1);
      setShowDropdown(true);
    } catch {
      setResults([]);
      setShowDropdown(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchResults(query), 180);
    return () => clearTimeout(debounceRef.current);
  }, [query, fetchResults]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setShowDropdown(false);
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleKeyDown = (e) => {
    if (!showDropdown || results.length === 0) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedIndex(prev => Math.min(prev + 1, results.length - 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setSelectedIndex(prev => Math.max(prev - 1, -1)); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0 && results[selectedIndex]) {
        onSelect(results[selectedIndex]);
        setQuery(results[selectedIndex].name);
        setShowDropdown(false);
      }
    } else if (e.key === 'Escape') { setShowDropdown(false); }
  };

  const handleSelect = (result) => { onSelect(result); setQuery(result.name); setShowDropdown(false); setResults([]); };
  const handleFocus = () => { if (results.length > 0) setShowDropdown(true); };
  const clearQuery = () => { setQuery(''); setResults([]); setShowDropdown(false); inputRef.current?.focus(); };

  return (
    <div className="relative w-full max-w-2xl" ref={dropdownRef}>
      <div className="term-input-wrap">
        <label htmlFor="ticker-input" className="sr-only">Search for a symbol</label>
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <span className="text-amber font-bold text-sm">&gt;</span>
        </div>
        <input
          ref={inputRef}
          id="ticker-input"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={handleFocus}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="term-input pl-8 pr-12"
          autoComplete="off"
          autoFocus
        />
        {query && (
          <button onClick={clearQuery} className="absolute inset-y-0 right-9 flex items-center p-2 text-muted hover:text-down transition-colors" aria-label="Clear">
            <X className="w-4 h-4" />
          </button>
        )}
        <div className="absolute inset-y-0 right-3 flex items-center">
          {loading ? <Loader2 className="w-4 h-4 text-amber animate-spin" /> : <Search className="w-4 h-4 text-muted" />}
        </div>
      </div>

      {showDropdown && results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 z-50 fade-in">
          <div className="panel scrollbar-thin max-h-80 overflow-y-auto">
            {results.map((result, index) => (
              <button
                key={`${result.ticker}-${result.exchange}`}
                onClick={() => handleSelect(result)}
                onMouseEnter={() => setSelectedIndex(index)}
                className={`w-full px-4 py-2.5 text-left transition-colors duration-100 flex items-center gap-4
                  ${index === selectedIndex ? 'bg-amber/10 border-l-2 border-amber' : 'border-l-2 border-transparent hover:bg-term-panel2'}`}
              >
                <span className="font-bold text-bright text-sm w-40 truncate">{result.name}</span>
                <span className="text-amber font-bold text-xs flex-1 text-left">{result.ticker}</span>
                {result.currency && (
                  <span className="text-muted text-[11px] border border-term-border px-1.5 py-0.5">{result.currency}</span>
                )}
                <span className="text-muted text-[11px] w-14 text-right">{result.exchange}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {showDropdown && results.length === 0 && query && !loading && (
        <div className="absolute top-full left-0 right-0 mt-1 z-50 fade-in">
          <div className="panel p-4 text-center">
            <span className="text-muted text-sm">NO MATCH FOR </span>
            <span className="text-amber text-sm">"{query}"</span>
          </div>
        </div>
      )}
    </div>
  );
}
