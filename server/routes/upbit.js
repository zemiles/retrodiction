/**
 * 업비트 API 프록시
 * - Quotation API: 시세 조회 (인증 불필요, CORS 있음 - 프록시로 우회)
 * - Exchange API: 주문/잔고 (클라이언트 JWT 또는 프록시)
 */
import express from 'express';
import axios from 'axios';

const router = express.Router();

const UPBIT_BASE_URL = 'https://api.upbit.com/v1';

/**
 * 시세 조회 프록시 (Quotation API - 인증 불필요)
 * GET /api/upbit/market/all
 * GET /api/upbit/candles/minutes/1?market=KRW-BTC
 * GET /api/upbit/ticker?markets=KRW-BTC
 */
router.get('/market/all', async (req, res) => {
  try {
    const response = await axios.get(`${UPBIT_BASE_URL}/market/all`);
    res.json(response.data);
  } catch (err) {
    res.status(err.response?.status || 500).json(
      err.response?.data || { error: err.message }
    );
  }
});

router.get('/candles/:unit', async (req, res) => {
  try {
    const { unit } = req.params;
    const { market, count = 200 } = req.query;
    if (!market) {
      return res.status(400).json({ error: 'market 쿼리가 필요합니다.' });
    }
    const response = await axios.get(
      `${UPBIT_BASE_URL}/candles/minutes/${unit}`,
      { params: { market, count } }
    );
    res.json(response.data);
  } catch (err) {
    res.status(err.response?.status || 500).json(
      err.response?.data || { error: err.message }
    );
  }
});

router.get('/ticker', async (req, res) => {
  try {
    const { markets } = req.query;
    if (!markets) {
      return res.status(400).json({ error: 'markets 쿼리가 필요합니다.' });
    }
    const response = await axios.get(`${UPBIT_BASE_URL}/ticker`, {
      params: { markets },
    });
    res.json(response.data);
  } catch (err) {
    res.status(err.response?.status || 500).json(
      err.response?.data || { error: err.message }
    );
  }
});

export default router;
