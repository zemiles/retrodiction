/**
 * Python 자동매매 서버 연동
 * - 사용자의 Python 트레이딩 서버와 통신
 * - 환경변수: PYTHON_TRADING_SERVER_URL
 * - 버튼으로 Trading API 서버 시작/중지
 */
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import path from 'path';
import express from 'express';
import axios from 'axios';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TRADING_DIR = path.join(__dirname, '..', '..', 'Trading');

const router = express.Router();

const PYTHON_SERVER_URL = process.env.PYTHON_TRADING_SERVER_URL || 'http://localhost:5000';
let tradingProcess = null;

/**
 * Python 서버 상태 확인
 * GET /api/python/status
 */
/**
 * Trading API 서버 시작 (버튼용)
 * POST /api/python/start-server
 */
router.post('/start-server', (req, res) => {
  if (tradingProcess) {
    return res.json({ ok: false, message: '이미 실행 중입니다.' });
  }

  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  const apiScript = path.join(TRADING_DIR, 'api_server.py');

  try {
    tradingProcess = spawn(pythonCmd, [apiScript], {
      cwd: TRADING_DIR,
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    tradingProcess.stdout?.on('data', (d) => console.log(`[Trading] ${d.toString().trim()}`));
    tradingProcess.stderr?.on('data', (d) => console.error(`[Trading] ${d.toString().trim()}`));
    tradingProcess.on('exit', (code) => {
      tradingProcess = null;
      console.log(`[Trading] 프로세스 종료 (code: ${code})`);
    });
    tradingProcess.on('error', (err) => {
      tradingProcess = null;
      console.error('[Trading] 시작 실패:', err);
    });

    res.json({ ok: true, message: 'Trading API 서버 시작 중... (몇 초 후 연결됨)' });
  } catch (err) {
    tradingProcess = null;
    res.status(500).json({ ok: false, message: err.message });
  }
});

/**
 * Trading API 서버 중지 (버튼용)
 * POST /api/python/stop-server
 */
router.post('/stop-server', (req, res) => {
  if (!tradingProcess) {
    return res.json({ ok: false, message: '실행 중인 서버가 없습니다.' });
  }
  tradingProcess.kill('SIGTERM');
  tradingProcess = null;
  res.json({ ok: true, message: 'Trading API 서버 중지 요청됨' });
});

router.get('/status', async (req, res) => {
  if (!PYTHON_SERVER_URL) {
    return res.json({
      connected: false,
      message: 'PYTHON_TRADING_SERVER_URL이 설정되지 않았습니다.',
    });
  }

  try {
    const response = await axios.get(`${PYTHON_SERVER_URL}/health`, {
      timeout: 3000,
    });
    res.json({
      connected: true,
      url: PYTHON_SERVER_URL,
      data: response.data,
    });
  } catch (err) {
    res.json({
      connected: false,
      url: PYTHON_SERVER_URL,
      error: err.message || '연결 실패',
    });
  }
});

/**
 * Python 서버로 요청 프록시
 * POST /api/python/proxy
 * body: { method, path, data }
 */
router.post('/proxy', async (req, res) => {
  if (!PYTHON_SERVER_URL) {
    return res.status(503).json({
      error: 'Python 트레이딩 서버 URL이 설정되지 않았습니다.',
    });
  }

  try {
    const { method = 'GET', path = '', data } = req.body;
    const url = `${PYTHON_SERVER_URL.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
    const config = {
      method,
      url,
      timeout: 10000,
      headers: { 'Content-Type': 'application/json' },
    };
    if (data && method !== 'GET') config.data = data;

    const response = await axios(config);
    res.json(response.data);
  } catch (err) {
    const status = err.response?.status || 502;
    const data = err.response?.data || { error: err.message };
    res.status(status).json(data);
  }
});

export default router;
