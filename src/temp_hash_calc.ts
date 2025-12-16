import { hashApiKey } from './utils/auth';

const key = 'eo_testkey_SECRET';
const hash = hashApiKey(key);

console.log(hash);
