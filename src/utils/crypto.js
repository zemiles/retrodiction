/**
 * Web Crypto API 기반 클라이언트 암호화
 * - AES-256-GCM
 * - PBKDF2 키 유도 (salt, 250,000 반복)
 * - 민감한 매매 데이터 저장 시 사용
 */

const ALGORITHM = 'AES-GCM';
const KEY_LENGTH = 256;
const SALT_LENGTH = 16;
const IV_LENGTH = 12;
const PBKDF2_ITERATIONS = 250000;
const HASH = 'SHA-256';

/**
 * 비밀번호로부터 암호화 키 유도
 * @param {string} password - 사용자 비밀번호
 * @param {Uint8Array} salt - 랜덤 salt
 * @returns {Promise<CryptoKey>}
 */
async function deriveKey(password, salt) {
  const encoder = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    encoder.encode(password),
    'PBKDF2',
    false,
    ['deriveBits', 'deriveKey']
  );

  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt,
      iterations: PBKDF2_ITERATIONS,
      hash: HASH,
    },
    keyMaterial,
    { name: ALGORITHM, length: KEY_LENGTH },
    false,
    ['encrypt', 'decrypt']
  );
}

/**
 * 데이터 암호화
 * @param {string} plainText - 평문 JSON 문자열
 * @param {string} password - 비밀번호
 * @returns {Promise<string>} Base64 인코딩된 {iv,salt,ciphertext}
 */
export async function encrypt(plainText, password) {
  const salt = crypto.getRandomValues(new Uint8Array(SALT_LENGTH));
  const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH));
  const key = await deriveKey(password, salt);

  const encoded = new TextEncoder().encode(plainText);
  const ciphertext = await crypto.subtle.encrypt(
    {
      name: ALGORITHM,
      iv,
      tagLength: 128,
    },
    key,
    encoded
  );

  const combined = new Uint8Array(salt.length + iv.length + ciphertext.byteLength);
  combined.set(salt, 0);
  combined.set(iv, salt.length);
  combined.set(new Uint8Array(ciphertext), salt.length + iv.length);

  return btoa(String.fromCharCode(...combined));
}

/**
 * 데이터 복호화
 * @param {string} encryptedBase64 - 암호화된 Base64 문자열
 * @param {string} password - 비밀번호
 * @returns {Promise<string>} 평문 JSON 문자열
 */
export async function decrypt(encryptedBase64, password) {
  const combined = Uint8Array.from(atob(encryptedBase64), (c) => c.charCodeAt(0));
  const salt = combined.slice(0, SALT_LENGTH);
  const iv = combined.slice(SALT_LENGTH, SALT_LENGTH + IV_LENGTH);
  const ciphertext = combined.slice(SALT_LENGTH + IV_LENGTH);

  const key = await deriveKey(password, salt);
  const decrypted = await crypto.subtle.decrypt(
    {
      name: ALGORITHM,
      iv,
      tagLength: 128,
    },
    key,
    ciphertext
  );

  return new TextDecoder().decode(decrypted);
}
