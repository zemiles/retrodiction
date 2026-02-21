/**
 * 데이터 입력 - 수동 입력 + CSV 업로드
 */
import { useState, useCallback } from 'react';
import { saveEncrypted, hasStoredData } from '../utils/storage';

const INIT_TRADE = {
  symbol: '',
  type: 'buy',
  quantity: 0,
  price: 0,
  date: new Date().toISOString().slice(0, 10),
  memo: '',
};

export default function DataInput() {
  const [trades, setTrades] = useState([{ ...INIT_TRADE }]);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isFirstTime] = useState(!hasStoredData());

  const addTrade = () => {
    setTrades((prev) => [...prev, { ...INIT_TRADE }]);
  };

  const updateTrade = (index, field, value) => {
    setTrades((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  const removeTrade = (index) => {
    if (trades.length <= 1) return;
    setTrades((prev) => prev.filter((_, i) => i !== index));
  };

  const handleFileUpload = useCallback((e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const text = ev.target?.result || '';
        const lines = text.split('\n').filter((l) => l.trim());
        if (lines.length < 2) {
          setMessage('CSV에 헤더와 최소 1행의 데이터가 필요합니다.');
          return;
        }
        const headers = lines[0].split(',').map((h) => h.trim().toLowerCase());
        const parsed = lines.slice(1).map((line) => {
          const values = line.split(',').map((v) => v.trim());
          const row = {};
          headers.forEach((h, i) => (row[h] = values[i] || ''));
          return {
            symbol: row.symbol || row.종목 || '',
            type: (row.type || row.유형 || row.buy_sell || 'buy').toLowerCase().includes('sell') ? 'sell' : 'buy',
            quantity: parseFloat(row.quantity || row.수량 || row.qty || 0) || 0,
            price: parseFloat(row.price || row.가격 || row.price || 0) || 0,
            date: row.date || row.날짜 || new Date().toISOString().slice(0, 10),
            memo: row.memo || row.메모 || '',
          };
        });
        setTrades(parsed.length ? parsed : [{ ...INIT_TRADE }]);
        setMessage(`CSV에서 ${parsed.length}건 불러왔습니다.`);
      } catch (err) {
        setMessage('CSV 파싱 오류: ' + err.message);
      }
    };
    reader.readAsText(file, 'UTF-8');
    e.target.value = '';
  }, []);

  const handleSave = async () => {
    setMessage('');
    const pwd = password || confirmPassword;
    if (!pwd) {
      setMessage('저장 비밀번호를 입력하세요.');
      return;
    }
    if (password && confirmPassword && password !== confirmPassword) {
      setMessage('비밀번호가 일치하지 않습니다.');
      return;
    }
    const valid = trades.filter((t) => t.symbol && t.quantity > 0 && t.price > 0);
    if (!valid.length) {
      setMessage('최소 1건의 유효한 거래를 입력하세요.');
      return;
    }
    try {
      await saveEncrypted({ trades: valid, updatedAt: new Date().toISOString() }, pwd);
      setMessage('저장되었습니다. (암호화됨)');
    } catch (err) {
      setMessage('저장 실패: ' + err.message);
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 'var(--spacing-lg)' }}>
        데이터 입력
      </h1>

      <div className="card">
        <div className="card-title">저장 비밀번호</div>
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--spacing-md)' }}>
          데이터는 암호화되어 저장됩니다. 비밀번호를 분실하면 복구할 수 없습니다.
        </p>
        <div style={{ display: 'flex', gap: 'var(--spacing-md)', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div className="form-group" style={{ marginBottom: 0, minWidth: 180 }}>
            <label className="form-label">비밀번호</label>
            <input
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={isFirstTime ? '저장용 비밀번호' : '기존 비밀번호'}
            />
          </div>
          {isFirstTime && (
            <div className="form-group" style={{ marginBottom: 0, minWidth: 180 }}>
              <label className="form-label">비밀번호 확인</label>
              <input
                type="password"
                className="form-input"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="비밀번호 재입력"
              />
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-title">CSV 업로드</div>
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--spacing-md)' }}>
          헤더: symbol, type, quantity, price, date, memo (또는 한글: 종목, 유형, 수량, 가격, 날짜, 메모)
        </p>
        <input type="file" accept=".csv" onChange={handleFileUpload} />
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-md)' }}>
          <span className="card-title" style={{ marginBottom: 0 }}>수동 입력</span>
          <button className="btn btn-secondary" onClick={addTrade}>+ 추가</button>
        </div>
        {trades.map((t, i) => (
          <div key={i} className="trade-row" style={{ display: 'grid', gap: 'var(--spacing-sm)', alignItems: 'end', marginBottom: 'var(--spacing-md)' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">종목</label>
              <input
                className="form-input"
                value={t.symbol}
                onChange={(e) => updateTrade(i, 'symbol', e.target.value)}
                placeholder="예: 삼성전자, BTC"
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">유형</label>
              <select
                className="form-input"
                value={t.type}
                onChange={(e) => updateTrade(i, 'type', e.target.value)}
              >
                <option value="buy">매수</option>
                <option value="sell">매도</option>
              </select>
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">수량</label>
              <input
                type="number"
                className="form-input"
                value={t.quantity || ''}
                onChange={(e) => updateTrade(i, 'quantity', parseFloat(e.target.value) || 0)}
                placeholder="0"
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">가격</label>
              <input
                type="number"
                className="form-input"
                value={t.price || ''}
                onChange={(e) => updateTrade(i, 'price', parseFloat(e.target.value) || 0)}
                placeholder="0"
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">날짜</label>
              <input
                type="date"
                className="form-input"
                value={t.date}
                onChange={(e) => updateTrade(i, 'date', e.target.value)}
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">메모</label>
              <input
                className="form-input"
                value={t.memo}
                onChange={(e) => updateTrade(i, 'memo', e.target.value)}
                placeholder="선택"
              />
            </div>
            <button className="btn btn-secondary" onClick={() => removeTrade(i)} disabled={trades.length <= 1}>
              삭제
            </button>
          </div>
        ))}
        <div style={{ display: 'flex', gap: 'var(--spacing-md)', alignItems: 'center' }}>
          <button className="btn btn-primary" onClick={handleSave}>저장 (암호화)</button>
          {isFirstTime && (
            <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
              저장 시 비밀번호 입력 필요
            </span>
          )}
        </div>
      </div>

      {message && (
        <div className="card" style={{ background: message.includes('실패') || message.includes('오류') ? 'rgba(244,33,46,0.1)' : 'rgba(0,186,124,0.1)' }}>
          {message}
        </div>
      )}

    </div>
  );
}
