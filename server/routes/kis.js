/**
 * 한국투자증권 API 프록시
 * - CORS 우회를 위해 백엔드에서 API 호출
 * - 환경변수: KIS_APP_KEY, KIS_APP_SECRET
 */
import express from 'express';
import axios from 'axios';

const router = express.Router();

const KIS_BASE_URL = 'https://openapi.koreainvestment.com:9443';

/**
 * 토큰 발급 (한국투자증권)
 * POST /oauth2/tokenP
 */
router.post('/token', async (req, res) => {
  try {
    const { appKey, appSecret } = req.body;
    const key = appKey || process.env.KIS_APP_KEY;
    const secret = appSecret || process.env.KIS_APP_SECRET;

    if (!key || !secret) {
      return res.status(400).json({
        error: 'KIS_APP_KEY, KIS_APP_SECRET이 필요합니다.',
      });
    }

    const response = await axios.post(
      `${KIS_BASE_URL}/oauth2/tokenP`,
      {
        grant_type: 'client_credentials',
        appkey: key,
        appsecret: secret,
      },
      {
        headers: { 'Content-Type': 'application/json' },
      }
    );

    res.json(response.data);
  } catch (err) {
    const status = err.response?.status || 500;
    const message = err.response?.data?.error_description || err.message;
    res.status(status).json({ error: message });
  }
});

/**
 * 국내주식 시세 조회 (프록시)
 * 클라이언트에서 토큰을 받아 호출
 */
router.post('/proxy', async (req, res) => {
  try {
    const { method = 'GET', path, headers = {}, data } = req.body;

    if (!path) {
      return res.status(400).json({ error: 'path가 필요합니다.' });
    }

    const url = path.startsWith('http') ? path : `${KIS_BASE_URL}${path}`;
    const config = {
      method,
      url,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
    };
    if (data && method !== 'GET') config.data = data;

    const response = await axios(config);
    res.json(response.data);
  } catch (err) {
    const status = err.response?.status || 500;
    const data = err.response?.data || { error: err.message };
    res.status(status).json(data);
  }
});

export default router;
