/**
 * 대시보드 - 요약 정보 및 빠른 접근
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { fetchHealth, fetchPythonStatus } from '../utils/api';
import { hasStoredData } from '../utils/storage';

export default function Dashboard() {
  const [serverOk, setServerOk] = useState(null);
  const [pythonOk, setPythonOk] = useState(null);

  useEffect(() => {
    fetchHealth()
      .then((d) => setServerOk(d.status === 'ok'))
      .catch(() => setServerOk(false));

    fetchPythonStatus()
      .then((d) => setPythonOk(d.connected))
      .catch(() => setPythonOk(false));
  }, []);

  const hasData = hasStoredData();

  return (
    <div>
      <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 'var(--spacing-lg)' }}>
        대시보드
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 'var(--spacing-md)' }}>
        <div className="card">
          <div className="card-title">백엔드 서버</div>
          <p style={{ color: serverOk ? 'var(--color-success)' : 'var(--color-danger)', margin: 0 }}>
            {serverOk === null ? '확인 중...' : serverOk ? '연결됨' : '연결 안 됨'}
          </p>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginTop: 'var(--spacing-xs)' }}>
            Node.js API 서버 (포트 3001)
          </p>
        </div>

        <div className="card">
          <div className="card-title">Python 자동매매</div>
          <p style={{ color: pythonOk ? 'var(--color-success)' : 'var(--color-text-muted)', margin: 0 }}>
            {pythonOk === null ? '확인 중...' : pythonOk ? '연결됨' : '미연결'}
          </p>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginTop: 'var(--spacing-xs)' }}>
            server/.env에 PYTHON_TRADING_SERVER_URL 설정
          </p>
        </div>

        <div className="card">
          <div className="card-title">저장된 데이터</div>
          <p style={{ color: hasData ? 'var(--color-success)' : 'var(--color-text-muted)', margin: 0 }}>
            {hasData ? '있음' : '없음'}
          </p>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginTop: 'var(--spacing-xs)' }}>
            암호화되어 로컬에 저장
          </p>
        </div>
      </div>

      <div className="card" style={{ marginTop: 'var(--spacing-lg)' }}>
        <div className="card-title">빠른 시작</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--spacing-md)' }}>
          <Link to="/input" className="btn btn-primary">
            매매 데이터 입력
          </Link>
          <Link to="/analysis" className="btn btn-secondary">
            분석 결과 보기
          </Link>
          <Link to="/recommendations" className="btn btn-secondary">
            매매 제안 보기
          </Link>
          <Link to="/trading" className="btn btn-secondary">
            Trading 봇
          </Link>
        </div>
      </div>
    </div>
  );
}
