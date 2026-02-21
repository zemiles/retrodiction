/**
 * Trading 봇 - 상태, 설정, 백테스트, 로그
 */
import { useState, useEffect, useCallback } from 'react';
import {
  fetchPythonStatus,
  fetchTradingStatus,
  fetchTradingConfig,
  updateTradingConfig,
  runTradingBacktest,
  fetchTradingLogs,
  tradingStart,
  tradingStop,
  startTradingServer,
  stopTradingServer,
} from '../utils/api';

export default function Trading() {
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState(null);
  const [config, setConfig] = useState(null);
  const [logs, setLogs] = useState([]);
  const [backtestResults, setBacktestResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadStatus = useCallback(async () => {
    try {
      const s = await fetchPythonStatus();
      setConnected(s.connected);
      if (s.connected) {
        const st = await fetchTradingStatus();
        setStatus(st);
      } else {
        setStatus(null);
      }
    } catch (e) {
      setConnected(false);
      setStatus(null);
      setError(e.message);
    }
  }, []);

  const loadConfig = useCallback(async () => {
    if (!connected) return;
    try {
      const c = await fetchTradingConfig();
      setConfig(c);
    } catch (e) {
      setError(e.message);
    }
  }, [connected]);

  const loadLogs = useCallback(async () => {
    if (!connected) return;
    try {
      const data = await fetchTradingLogs(100);
      setLogs(data.logs || []);
    } catch (e) {
      setError(e.message);
    }
  }, [connected]);

  useEffect(() => {
    loadStatus();
    const id = setInterval(loadStatus, 5000);
    return () => clearInterval(id);
  }, [loadStatus]);

  useEffect(() => {
    if (connected) {
      loadConfig();
      loadLogs();
    }
  }, [connected, loadConfig, loadLogs]);

  const handleRunBacktest = async () => {
    setLoading(true);
    setError('');
    setBacktestResults(null);
    try {
      const data = await runTradingBacktest();
      setBacktestResults(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTradingStart = async () => {
    setLoading(true);
    setError('');
    try {
      await tradingStart();
      await loadStatus();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTradingStop = async () => {
    setLoading(true);
    setError('');
    try {
      await tradingStop();
      await loadStatus();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleServerStart = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await startTradingServer();
      if (!data.ok) throw new Error(data.message);
      await loadStatus();
      // 서버가 뜨는 데 시간이 걸리므로 2초 후 재확인
      setTimeout(loadStatus, 2000);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleServerStop = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await stopTradingServer();
      if (!data.ok) throw new Error(data.message);
      setConnected(false);
      setStatus(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConfigSave = async () => {
    if (!config) return;
    setLoading(true);
    setError('');
    try {
      await updateTradingConfig(config);
      await loadConfig();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 'var(--spacing-lg)' }}>
        Trading 봇
      </h1>

      {error && (
        <div className="card" style={{ background: 'rgba(244,33,46,0.1)', marginBottom: 'var(--spacing-md)' }}>
          {error}
        </div>
      )}

      {/* 연결 상태 & 서버 제어 */}
      <div className="card">
        <div className="card-title">연결 상태</div>
        <p style={{ color: connected ? 'var(--color-success)' : 'var(--color-danger)', margin: 0 }}>
          {connected ? 'Trading API 서버 연결됨' : 'Trading API 서버 미연결'}
        </p>
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginTop: 'var(--spacing-xs)', marginBottom: 'var(--spacing-md)' }}>
          아래 버튼으로 서버를 시작하거나, Trading 폴더에서 <code>python api_server.py</code> 실행
        </p>
        <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
          <button
            className="btn btn-primary"
            onClick={handleServerStart}
            disabled={loading || connected}
          >
            서버 시작
          </button>
          <button
            className="btn btn-secondary"
            onClick={handleServerStop}
            disabled={loading || !connected}
          >
            서버 중지
          </button>
        </div>
      </div>

      {connected && status && (
        <>
          {/* 모드 & 트레이딩 제어 */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--spacing-md)' }}>
            <div className="card">
              <div className="card-title">모드</div>
              <p style={{ margin: 0, fontSize: 'var(--font-size-lg)' }}>
                {status.modeLabel || status.mode}
              </p>
            </div>
            <div className="card">
              <div className="card-title">트레이딩</div>
              <p style={{ margin: '0 0 var(--spacing-sm) 0', color: status.tradingRunning ? 'var(--color-success)' : 'var(--color-text-muted)' }}>
                {status.tradingRunning ? '실행 중' : '중지됨'}
              </p>
              <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
                <button
                  className="btn btn-primary"
                  onClick={handleTradingStart}
                  disabled={loading || status.tradingRunning}
                >
                  시작
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={handleTradingStop}
                  disabled={loading || !status.tradingRunning}
                >
                  중지
                </button>
              </div>
            </div>
          </div>

          {/* 설정 */}
          {config && (
            <div className="card">
              <div className="card-title">설정</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--spacing-md)' }}>
                <div className="form-group">
                  <label className="form-label">RSI 기간</label>
                  <input
                    type="number"
                    className="form-input"
                    value={config.strategy?.rsi_period ?? 14}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        strategy: { ...config.strategy, rsi_period: parseInt(e.target.value, 10) },
                      })
                    }
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">매수 RSI (이하)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={config.strategy?.buy_threshold ?? 30}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        strategy: { ...config.strategy, buy_threshold: parseInt(e.target.value, 10) },
                      })
                    }
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">매도 RSI (이상)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={config.strategy?.sell_threshold ?? 70}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        strategy: { ...config.strategy, sell_threshold: parseInt(e.target.value, 10) },
                      })
                    }
                  />
                </div>
              </div>
              <button className="btn btn-primary" onClick={handleConfigSave} disabled={loading}>
                설정 저장
              </button>
            </div>
          )}

          {/* 백테스트 */}
          <div className="card">
            <div className="card-title">백테스트</div>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--spacing-md)' }}>
              현재 설정으로 과거 데이터 백테스트 실행 (한국투자증권 API 인증 필요)
            </p>
            <button className="btn btn-primary" onClick={handleRunBacktest} disabled={loading}>
              {loading ? '실행 중...' : '백테스트 실행'}
            </button>
            {backtestResults?.results?.length > 0 && (
              <div style={{ marginTop: 'var(--spacing-md)', overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--font-size-sm)' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                      <th style={{ textAlign: 'left', padding: 'var(--spacing-sm)' }}>종목</th>
                      <th style={{ textAlign: 'right', padding: 'var(--spacing-sm)' }}>수익률</th>
                      <th style={{ textAlign: 'right', padding: 'var(--spacing-sm)' }}>승률</th>
                      <th style={{ textAlign: 'right', padding: 'var(--spacing-sm)' }}>거래 수</th>
                      <th style={{ textAlign: 'right', padding: 'var(--spacing-sm)' }}>최대 낙폭</th>
                    </tr>
                  </thead>
                  <tbody>
                    {backtestResults.results.map((r) => (
                      <tr key={r.stockCode} style={{ borderBottom: '1px solid var(--color-border)' }}>
                        <td style={{ padding: 'var(--spacing-sm)' }}>{r.stockName} ({r.stockCode})</td>
                        <td
                          style={{
                            padding: 'var(--spacing-sm)',
                            textAlign: 'right',
                            color: r.totalReturnPct >= 0 ? 'var(--color-success)' : 'var(--color-danger)',
                          }}
                        >
                          {(r.totalReturnPct * 100).toFixed(2)}%
                        </td>
                        <td style={{ padding: 'var(--spacing-sm)', textAlign: 'right' }}>
                          {(r.winRate * 100).toFixed(0)}%
                        </td>
                        <td style={{ padding: 'var(--spacing-sm)', textAlign: 'right' }}>{r.numTrades}</td>
                        <td style={{ padding: 'var(--spacing-sm)', textAlign: 'right', color: 'var(--color-danger)' }}>
                          {(r.maxDrawdownPct * 100).toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* 로그 */}
          <div className="card">
            <div className="card-title">최근 로그</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-sm)' }}>
              <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
                최근 {logs.length}건
              </span>
              <button className="btn btn-secondary" onClick={loadLogs} disabled={loading}>
                새로고침
              </button>
            </div>
            <div
              style={{
                maxHeight: 300,
                overflowY: 'auto',
                background: 'var(--color-bg)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--spacing-sm)',
                fontFamily: 'monospace',
                fontSize: 'var(--font-size-xs)',
              }}
            >
              {logs.length === 0 ? (
                <p style={{ color: 'var(--color-text-muted)', margin: 0 }}>로그 없음</p>
              ) : (
                logs
                  .slice()
                  .reverse()
                  .map((l, i) => (
                    <div key={i} style={{ marginBottom: 2, color: l.level === 'ERROR' ? 'var(--color-danger)' : 'var(--color-text)' }}>
                      [{l.time?.slice(11, 19)}] {l.msg}
                    </div>
                  ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
