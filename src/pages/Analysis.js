/**
 * 분석 결과 - 통계, 차트
 */
import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { loadEncrypted } from '../utils/storage';

function computeStats(trades) {
  if (!trades?.length) return null;
  const bySymbol = {};
  trades.forEach((t) => {
    if (!bySymbol[t.symbol]) bySymbol[t.symbol] = { buys: [], sells: [], symbol: t.symbol };
    if (t.type === 'buy') bySymbol[t.symbol].buys.push(t);
    else bySymbol[t.symbol].sells.push(t);
  });

  const symbols = Object.keys(bySymbol);
  const summary = symbols.map((sym) => {
    const d = bySymbol[sym];
    const buyTotal = d.buys.reduce((s, b) => s + b.quantity * b.price, 0);
    const sellTotal = d.sells.reduce((s, b) => s + b.quantity * b.price, 0);
    const profit = sellTotal - buyTotal;
    const winRate = d.sells.length ? (d.sells.filter((s) => s.price > 0).length / d.sells.length) * 100 : 0;
    return {
      symbol: sym,
      buyTotal,
      sellTotal,
      profit,
      tradeCount: d.buys.length + d.sells.length,
      winRate,
    };
  });

  const totalProfit = summary.reduce((s, x) => s + x.profit, 0);
  const buySellCount = { buy: trades.filter((t) => t.type === 'buy').length, sell: trades.filter((t) => t.type === 'sell').length };

  return {
    trades,
    bySymbol,
    summary,
    totalProfit,
    buySellCount,
    totalTrades: trades.length,
  };
}

export default function Analysis() {
  const [stats, setStats] = useState(null);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const loadData = async () => {
    if (!password) {
      setError('비밀번호를 입력하세요.');
      return;
    }
    setError('');
    try {
      const data = await loadEncrypted(password);
      if (!data?.trades?.length) {
        setStats(null);
        setError('저장된 데이터가 없습니다.');
        return;
      }
      setStats(computeStats(data.trades));
    } catch {
      setError('비밀번호가 올바르지 않거나 복호화에 실패했습니다.');
      setStats(null);
    }
  };

  const pieData = stats?.buySellCount
    ? [
        { name: '매수', value: stats.buySellCount.buy, color: 'var(--color-primary)' },
        { name: '매도', value: stats.buySellCount.sell, color: 'var(--color-success)' },
      ]
    : [];

  return (
    <div>
      <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 'var(--spacing-lg)' }}>
        분석 결과
      </h1>

      <div className="card">
        <div className="card-title">데이터 불러오기</div>
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--spacing-md)' }}>
          암호화된 데이터를 복호화하려면 저장 시 사용한 비밀번호를 입력하세요.
        </p>
        <div style={{ display: 'flex', gap: 'var(--spacing-md)', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            type="password"
            className="form-input"
            style={{ maxWidth: 200 }}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="비밀번호"
          />
          <button className="btn btn-primary" onClick={loadData}>불러오기</button>
        </div>
        {error && <p style={{ color: 'var(--color-danger)', marginTop: 'var(--spacing-sm)' }}>{error}</p>}
      </div>

      {stats && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--spacing-md)' }}>
            <div className="card">
              <div className="card-title">총 거래 수</div>
              <p style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-bold)', margin: 0 }}>
                {stats.totalTrades}건
              </p>
            </div>
            <div className="card">
              <div className="card-title">총 손익</div>
              <p
                style={{
                  fontSize: 'var(--font-size-2xl)',
                  fontWeight: 'var(--font-weight-bold)',
                  margin: 0,
                  color: stats.totalProfit >= 0 ? 'var(--color-success)' : 'var(--color-danger)',
                }}
              >
                {stats.totalProfit >= 0 ? '+' : ''}
                {stats.totalProfit.toLocaleString()}원
              </p>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 'var(--spacing-md)' }}>
            <div className="card">
              <div className="card-title">매수/매도 비율</div>
              {pieData.length ? (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2} dataKey="value">
                      {pieData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p style={{ color: 'var(--color-text-muted)' }}>데이터 없음</p>
              )}
            </div>

            <div className="card">
              <div className="card-title">종목별 손익</div>
              {stats.summary?.length ? (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={stats.summary} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                    <XAxis dataKey="symbol" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="profit" fill="var(--color-primary)" name="손익" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p style={{ color: 'var(--color-text-muted)' }}>데이터 없음</p>
              )}
            </div>
          </div>

          <div className="card">
            <div className="card-title">종목별 상세</div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--font-size-sm)' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <th style={{ textAlign: 'left', padding: 'var(--spacing-sm)' }}>종목</th>
                    <th style={{ textAlign: 'right', padding: 'var(--spacing-sm)' }}>거래 수</th>
                    <th style={{ textAlign: 'right', padding: 'var(--spacing-sm)' }}>매수 총액</th>
                    <th style={{ textAlign: 'right', padding: 'var(--spacing-sm)' }}>매도 총액</th>
                    <th style={{ textAlign: 'right', padding: 'var(--spacing-sm)' }}>손익</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.summary.map((s) => (
                    <tr key={s.symbol} style={{ borderBottom: '1px solid var(--color-border)' }}>
                      <td style={{ padding: 'var(--spacing-sm)' }}>{s.symbol}</td>
                      <td style={{ textAlign: 'right', padding: 'var(--spacing-sm)' }}>{s.tradeCount}</td>
                      <td style={{ textAlign: 'right', padding: 'var(--spacing-sm)' }}>{s.buyTotal.toLocaleString()}</td>
                      <td style={{ textAlign: 'right', padding: 'var(--spacing-sm)' }}>{s.sellTotal.toLocaleString()}</td>
                      <td
                        style={{
                          textAlign: 'right',
                          padding: 'var(--spacing-sm)',
                          color: s.profit >= 0 ? 'var(--color-success)' : 'var(--color-danger)',
                        }}
                      >
                        {s.profit >= 0 ? '+' : ''}
                        {s.profit.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
