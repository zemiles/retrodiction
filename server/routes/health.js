/**
 * 헬스체크 엔드포인트
 */
import express from 'express';

const router = express.Router();

router.get('/', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    service: 'retrodiction-server',
  });
});

export default router;
