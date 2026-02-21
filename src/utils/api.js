/**
 * API 클라이언트 - 백엔드 서버 호출
 */

const API_BASE = process.env.REACT_APP_API_URL || '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchUpbitMarkets() {
  const res = await fetch(`${API_BASE}/upbit/market/all`);
  return res.json();
}

export async function fetchUpbitTicker(markets) {
  const params = new URLSearchParams({ markets: markets.join(',') });
  const res = await fetch(`${API_BASE}/upbit/ticker?${params}`);
  return res.json();
}

export async function fetchUpbitCandles(market, unit = 1, count = 200) {
  const res = await fetch(
    `${API_BASE}/upbit/candles/${unit}?market=${encodeURIComponent(market)}&count=${count}`
  );
  return res.json();
}

export async function fetchPythonStatus() {
  const res = await fetch(`${API_BASE}/python/status`);
  return res.json();
}

export async function startTradingServer() {
  const res = await fetch(`${API_BASE}/python/start-server`, { method: 'POST' });
  return res.json();
}

export async function stopTradingServer() {
  const res = await fetch(`${API_BASE}/python/stop-server`, { method: 'POST' });
  return res.json();
}

export async function proxyToPython(method, path, data) {
  const res = await fetch(`${API_BASE}/python/proxy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ method, path, data }),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json.error || json.message || res.statusText);
  return json;
}

// Trading 봇 API
export async function fetchTradingStatus() {
  return proxyToPython('GET', 'status');
}

export async function fetchTradingConfig() {
  return proxyToPython('GET', 'config');
}

export async function updateTradingConfig(config) {
  return proxyToPython('POST', 'config', config);
}

export async function runTradingBacktest() {
  return proxyToPython('POST', 'backtest', {});
}

export async function fetchTradingLogs(limit = 100) {
  return proxyToPython('GET', `logs?limit=${limit}`);
}

export async function tradingStart() {
  return proxyToPython('POST', 'trading/start', {});
}

export async function tradingStop() {
  return proxyToPython('POST', 'trading/stop', {});
}

export async function fetchTradingCharts() {
  return proxyToPython('GET', 'charts');
}
