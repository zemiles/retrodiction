/**
 * Retrodiction - 매매 패턴 분석 & 제안 앱
 */
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import DataInput from './pages/DataInput';
import Analysis from './pages/Analysis';
import Recommendations from './pages/Recommendations';
import Trading from './pages/Trading';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="input" element={<DataInput />} />
          <Route path="analysis" element={<Analysis />} />
          <Route path="recommendations" element={<Recommendations />} />
          <Route path="trading" element={<Trading />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
