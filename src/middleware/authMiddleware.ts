import { Request, Response, NextFunction } from 'express';
import { mockDb } from '../db/mockDb';
import { extractKeyPrefix, validateApiKey } from '../utils/auth';

// Simple in-memory rate limiter for demonstration
const rateLimitStore = new Map<number, { count: number, resetTime: number }>();
const WINDOW_MS = 60 * 1000; // 1 minute window

/**
 * Middleware for API Key Authentication and Rate Limiting.
 */
export async function authMiddleware(req: Request, res: Response, next: NextFunction) {
    const apiKey = req.headers['x-api-key'] as string;

    if (!apiKey) {
        return res.status(401).json({ error: 'Unauthorized: Missing X-API-Key header' });
    }

    const keyPrefix = extractKeyPrefix(apiKey);
    if (!keyPrefix) {
        return res.status(401).json({ error: 'Unauthorized: Invalid API Key format' });
    }

    // 1. Find user by key prefix
    const userRecord = await mockDb.findUserByApiKeyPrefix(keyPrefix);
    if (!userRecord) {
        return res.status(401).json({ error: 'Unauthorized: Invalid API Key' });
    }

    // 2. Validate the full key hash
    if (!validateApiKey(apiKey, userRecord.key.keyHash)) {
        return res.status(401).json({ error: 'Unauthorized: Invalid API Key' });
    }

    // 3. Check if key is active
    if (!userRecord.key.isActive) {
        return res.status(403).json({ error: 'Forbidden: API Key is inactive' });
    }

    // 4. Check subscription and rate limits (using mockDb for credit check)
    if (userRecord.credits) {
        const creditCheck = await mockDb.incrementUsedCredits(userRecord.user.id);
        if (!creditCheck) {
            return res.status(429).json({ error: 'Too Many Requests: Daily/Monthly limit exceeded' });
        }
    } else {
        // Fallback to simple in-memory rate limiting if credit system is not set up for the user
        const userId = userRecord.user.id;
        const now = Date.now();
        const limit = 60; // 60 requests per minute

        const record = rateLimitStore.get(userId) || { count: 0, resetTime: now + WINDOW_MS };

        if (record.resetTime < now) {
            record.count = 0;
            record.resetTime = now + WINDOW_MS;
        }

        if (record.count >= limit) {
            return res.status(429).json({ error: 'Too Many Requests: Rate limit exceeded (60/min)' });
        }

        record.count++;
        rateLimitStore.set(userId, record);
    }

    // 5. Update last used time
    await mockDb.updateApiKeyLastUsed(userRecord.key.id);

    // Attach user info to request object for downstream handlers
    (req as any).user = userRecord.user;
    (req as any).subscription = userRecord.subscription;

    next();
}
