import * as crypto from 'crypto';

// Use a secure, slow hashing algorithm like Argon2 in production.
// For this example, we'll use a simple SHA256 with a salt.
const SALT = process.env.API_KEY_SALT || 'a_strong_default_salt_for_dev';

/**
 * Hashes an API key for secure storage.
 * @param key The plain text API key.
 * @returns The hashed key.
 */
export function hashApiKey(key: string): string {
    return crypto.createHmac('sha256', SALT)
                 .update(key)
                 .digest('hex');
}

/**
 * Generates a new API key with a prefix.
 * @param prefix The prefix for the key (e.g., 'eo_').
 * @returns The generated API key.
 */
export function generateApiKey(prefix: string = 'eo_'): string {
    const randomBytes = crypto.randomBytes(16).toString('hex');
    return `${prefix}${randomBytes}`;
}

/**
 * Extracts the prefix from an API key.
 * @param key The API key.
 * @returns The key prefix.
 */
export function extractKeyPrefix(key: string): string {
    // Assuming the prefix is everything up to the last underscore, e.g., 'eo_testkey_SECRET' -> 'eo_testkey_'
    const lastUnderscoreIndex = key.lastIndexOf('_');
    if (lastUnderscoreIndex !== -1) {
        return key.substring(0, lastUnderscoreIndex + 1);
    }
    return '';
}

/**
 * Validates a plain text key against a stored hash.
 * @param plainKey The plain text key from the request.
 * @param storedHash The hashed key from the database.
 * @returns True if the keys match, false otherwise.
 */
export function validateApiKey(plainKey: string, storedHash: string): boolean {
    const hashedKey = hashApiKey(plainKey);
    return hashedKey === storedHash;
}
