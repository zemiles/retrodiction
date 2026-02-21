/**
 * 암호화된 로컬 스토리지 유틸
 * - 매매 데이터, API 키 등 민감 정보 저장
 */

import { encrypt, decrypt } from './crypto';

const STORAGE_KEY = 'retrodiction_data';

/**
 * 데이터 저장 (암호화)
 * @param {object} data - 저장할 객체
 * @param {string} password - 암호화 비밀번호
 */
export async function saveEncrypted(data, password) {
  const json = JSON.stringify(data);
  const encrypted = await encrypt(json, password);
  localStorage.setItem(STORAGE_KEY, encrypted);
}

/**
 * 데이터 로드 (복호화)
 * @param {string} password - 복호화 비밀번호
 * @returns {Promise<object|null>}
 */
export async function loadEncrypted(password) {
  const encrypted = localStorage.getItem(STORAGE_KEY);
  if (!encrypted) return null;
  try {
    const json = await decrypt(encrypted, password);
    return JSON.parse(json);
  } catch {
    return null;
  }
}

/**
 * 저장된 데이터 존재 여부
 */
export function hasStoredData() {
  return !!localStorage.getItem(STORAGE_KEY);
}
