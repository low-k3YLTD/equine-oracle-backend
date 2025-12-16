import { apiKeys, userCredits, users, subscriptions } from "../../drizzle/schema";

// Mock data store
const mockUsers = [
    { id: 1, externalId: "auth_user_1", email: "user1@example.com", subscriptionId: 1, createdAt: new Date(), updatedAt: new Date() },
    { id: 2, externalId: "auth_user_2", email: "user2@example.com", subscriptionId: 2, createdAt: new Date(), updatedAt: new Date() },
];

const mockSubscriptions = [
    { id: 1, tier: "Free", maxPredictionsPerMonth: 100, apiAccess: true, customModels: false, prioritySupport: false, priceMonthly: 0, createdAt: new Date(), updatedAt: new Date() },
    { id: 2, tier: "Basic", maxPredictionsPerMonth: 1000, apiAccess: true, customModels: false, prioritySupport: false, priceMonthly: 29.99, createdAt: new Date(), updatedAt: new Date() },
];

// Mock API key data (hashed key for 'eo_testkey_user1')
interface MockApiKey {
    id: number;
    userId: number;
    keyHash: string;
    keyPrefix: string;
    name: string;
    isActive: boolean;
    createdAt: Date;
    expiresAt: Date | null;
    lastUsedAt: Date | null;
}
const mockApiKeys: MockApiKey[] = [
    // Key: eo_testkey_SECRET
    { id: 1, userId: 1, keyHash: "13ae32ef9511dc71b16b918f89a1352e0a3f6c43a436a4f162e6c834f7fdbcc6", keyPrefix: "eo_testkey_", name: "Test Key 1", isActive: true, createdAt: new Date(), expiresAt: null, lastUsedAt: null },
];

const mockUserCredits = [
    { userId: 1, dailyLimit: 50, dailyUsed: 0, monthlyLimit: 100, monthlyUsed: 0, lastReset: new Date() },
];

// Mock implementation of database operations
export const mockDb = {
    // Simulate finding a user by API key prefix
    async findUserByApiKeyPrefix(prefix: string) {
        const keyRecord = mockApiKeys.find(k => k.keyPrefix === prefix && k.isActive);
        if (!keyRecord) return null;

        const user = mockUsers.find(u => u.id === keyRecord.userId);
        if (!user) return null;

        const subscription = mockSubscriptions.find(s => s.id === user.subscriptionId);
        const credits = mockUserCredits.find(c => c.userId === user.id);

        return {
            user,
            key: keyRecord,
            subscription,
            credits
        };
    },

    // Simulate updating user credits
    async incrementUsedCredits(userId: number, count: number = 1) {
        const creditIndex = mockUserCredits.findIndex(c => c.userId === userId);
        if (creditIndex === -1) return false;

        const credits = mockUserCredits[creditIndex];
        
        // Simple reset logic for mock
        const now = new Date();
        const lastReset = credits.lastReset;
        const isNewDay = now.getDate() !== lastReset.getDate() || now.getMonth() !== lastReset.getMonth() || now.getFullYear() !== lastReset.getFullYear();
        const isNewMonth = now.getMonth() !== lastReset.getMonth() || now.getFullYear() !== lastReset.getFullYear();

        if (isNewDay) {
            credits.dailyUsed = 0;
        }
        if (isNewMonth) {
            credits.monthlyUsed = 0;
        }
        credits.lastReset = now;

        if (credits.dailyUsed + count > credits.dailyLimit || credits.monthlyUsed + count > credits.monthlyLimit) {
            return false; // Rate limit exceeded
        }

        credits.dailyUsed += count;
        credits.monthlyUsed += count;
        return true;
    },

    // Simulate updating last used time for API key
    async updateApiKeyLastUsed(keyId: number) {
        const keyIndex = mockApiKeys.findIndex(k => k.id === keyId);
        if (keyIndex !== -1) {
            mockApiKeys[keyIndex].lastUsedAt = new Date();
        }
    }
};
