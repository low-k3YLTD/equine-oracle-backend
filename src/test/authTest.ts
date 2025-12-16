import { hashApiKey, extractKeyPrefix, validateApiKey } from '../utils/auth';
import { mockDb } from '../db/mockDb';

async function runAuthTest() {
    const testKey = 'eo_testkey_SECRET';
    const expectedHash = '13ae32ef9511dc71b16b918f89a1352e0a3f6c43a436a4f162e6c834f7fdbcc6';
    const expectedPrefix = 'eo_testkey_';

    console.log("--- Auth Utility Tests ---");
    const actualHash = hashApiKey(testKey);
    console.log(`Test Key: ${testKey}`);
    console.log(`Actual Hash: ${actualHash}`);
    console.log(`Expected Hash: ${expectedHash}`);
    console.log(`Hash Match: ${actualHash === expectedHash}`);

    const actualPrefix = extractKeyPrefix(testKey);
    console.log(`Actual Prefix: ${actualPrefix}`);
    console.log(`Expected Prefix: ${expectedPrefix}`);
    console.log(`Prefix Match: ${actualPrefix === expectedPrefix}`);

    const validationResult = validateApiKey(testKey, expectedHash);
    console.log(`Validation Result: ${validationResult}`);
    console.log(`Validation Match: ${validationResult === true}`);

    console.log("\n--- Mock DB Integration Test ---");
    const userRecord = await mockDb.findUserByApiKeyPrefix(expectedPrefix);
    console.log(`User Record Found: ${!!userRecord}`);
    if (userRecord) {
        console.log(`User ID: ${userRecord.user.id}`);
        console.log(`Stored Hash: ${userRecord.key.keyHash}`);
        const dbValidation = validateApiKey(testKey, userRecord.key.keyHash);
        console.log(`DB Validation Result: ${dbValidation}`);
    }
}

runAuthTest().catch(console.error);
