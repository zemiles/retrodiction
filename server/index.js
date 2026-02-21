/**
 * Retrodiction 백엔드 서버
 * - 한국투자증권 API 프록시
 * - 업비트 API 프록시 (필요 시)
 * - Python 자동매매 서버 연동 엔드포인트
 */
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

import kisRouter from './routes/kis.js';
import upbitRouter from './routes/upbit.js';
import pythonRouter from './routes/python.js';
import healthRouter from './routes/health.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

// 미들웨어
app.use(cors({ origin: ['http://localhost:3000', 'http://127.0.0.1:3000'] }));
app.use(express.json());

// API 라우트
app.use('/api/kis', kisRouter);      // 한국투자증권
app.use('/api/upbit', upbitRouter);  // 업비트
app.use('/api/python', pythonRouter); // Python 자동매매 서버 연동
app.use('/api/health', healthRouter);

// 루트
app.get('/', (req, res) => {
  res.json({
    name: 'Retrodiction API',
    version: '0.1.0',
    endpoints: {
      health: '/api/health',
      kis: '/api/kis',
      upbit: '/api/upbit',
      python: '/api/python',
    },
  });
});

app.listen(PORT, () => {
  console.log(`[Retrodiction] 서버 실행 중: http://localhost:${PORT}`);
});
