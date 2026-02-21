/**
 * 레이아웃 - 네비게이션 + 콘텐츠 영역
 */
import { NavLink, Outlet } from 'react-router-dom';

export default function Layout() {
  return (
    <div className="app">
      <nav className="nav">
        <span className="nav-brand">📊 Retrodiction</span>
        <div className="nav-links">
          <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
            대시보드
          </NavLink>
          <NavLink to="/input" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            데이터 입력
          </NavLink>
          <NavLink to="/analysis" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            분석 결과
          </NavLink>
          <NavLink to="/recommendations" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            매매 제안
          </NavLink>
          <NavLink to="/trading" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Trading 봇
          </NavLink>
        </div>
      </nav>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
