/**
 * 매매 제안 - 패턴 기반 참고용 제안
 */
import { useState } from 'react';
import { loadEncrypted } from '../utils/storage';

function generateRecommendations(trades) {
  if (!trades?.length) return [];

  const bySymbol = {};
  trades.forEach((t) => {
    if (!bySymbol[t.symbol]) bySymbol[t.symbol] = { buys: [], sells: [] };
    if (t.type === 'buy') bySymbol[t.symbol].buys.push(t);
    else bySymbol[t.symbol].sells.push(t);
  });

  const recs = [];
  Object.entries(bySymbol).forEach(([symbol, d]) => {
    const buys = d.buys;
    const sells = d.sells;

    if (buys.length >= 1 && sells.length >= 1) {
      const firstBuyDate = new Date(buys[0].date);
      const holdDays = sells.map((s) => (new Date(s.date) - firstBuyDate) / (1000 * 60 * 60 * 24));
      const avgHoldDays = holdDays.reduce((a, b) => a + b, 0) / holdDays.length;
      if (avgHoldDays > 0 && avgHoldDays < 365) {
        recs.push({
          symbol,
          type: 'hold_period',
          message: `${symbol}: 과거 평균 보유 기간 약 ${Math.round(avgHoldDays)}일. 단기 매매보다는 중기 보유가 수익에 유리했을 수 있습니다.`,
          priority: 1,
        });
      }
    }

    if (sells.length >= 2) {
      const buyTotal = buys.reduce((a, b) => a + b.price * b.quantity, 0);
      const buyQty = buys.reduce((a, b) => a + b.quantity, 0);
      const avgBuyPrice = buyQty ? buyTotal / buyQty : 0;
      const profits = sells.map((sell) => (avgBuyPrice ? ((sell.price - avgBuyPrice) / avgBuyPrice) * 100 : 0));
      const avgProfitPct = profits.reduce((a, b) => a + b, 0) / profits.length;
      if (avgProfitPct > 5) {
        recs.push({
          symbol,
          type: 'profit_taking',
          message: `${symbol}: 과거 매도 시 평균 수익률 약 ${avgProfitPct.toFixed(1)}%. 비슷한 수익 구간에서 매도하는 패턴을 유지할 수 있습니다.`,
          priority: 2,
        });
      } else if (avgProfitPct < -5) {
        recs.push({
          symbol,
          type: 'loss_cut',
          message: `${symbol}: 과거 매도 시 평균 수익률이 마이너스였습니다. 손절 기준을 명확히 하는 것이 좋습니다.`,
          priority: 3,
        });
      }
    }

    const buyCount = buys.length;
    const sellCount = sells.length;
    if (buyCount > sellCount + 2) {
      recs.push({
        symbol,
        type: 'position',
        message: `${symbol}: 매수 횟수가 매도보다 많습니다. 포지션 규모를 점검해 보세요.`,
        priority: 2,
      });
    }
  });

  return recs.sort((a, b) => a.priority - b.priority);
}

export default function Recommendations() {
  const [recs, setRecs] = useState([]);
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
        setRecs([]);
        setError('저장된 데이터가 없습니다.');
        return;
      }
      setRecs(generateRecommendations(data.trades));
    } catch {
      setError('비밀번호가 올바르지 않거나 복호화에 실패했습니다.');
      setRecs([]);
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 'var(--spacing-lg)' }}>
        매매 제안
      </h1>

      <div className="card" style={{ background: 'rgba(255,173,31,0.08)', borderColor: 'var(--color-warning)' }}>
        <div className="card-title">⚠️ 참고용 안내</div>
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', margin: 0 }}>
          아래 제안은 과거 매매 패턴을 기반으로 한 참고용 정보입니다. 투자 조언이 아니며, 최종 투자 결정은 본인 책임입니다.
        </p>
      </div>

      <div className="card">
        <div className="card-title">데이터 불러오기</div>
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

      {recs.length > 0 && (
        <div className="card">
          <div className="card-title">종목별 매매 제안</div>
          <ul style={{ paddingLeft: 'var(--spacing-lg)', margin: 0 }}>
            {recs.map((r, i) => (
              <li key={i} style={{ marginBottom: 'var(--spacing-md)', lineHeight: 1.5 }}>
                {r.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {recs.length === 0 && !error && password && (
        <div className="card">
          <p style={{ color: 'var(--color-text-muted)' }}>
            제안을 생성할 수 있는 충분한 데이터가 없습니다. 더 많은 매매 내역을 입력해 주세요.
          </p>
        </div>
      )}
    </div>
  );
}
