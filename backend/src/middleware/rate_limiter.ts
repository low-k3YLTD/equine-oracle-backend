/**
 * Rate Limiting Middleware
 * Implements subscription tier-based rate limiting with Redis backend
 */

import { Request, Response, NextFunction } from 'express';
import { getRedisClient } from '../cache/redis_client';
import { Logger } from '../logging/logger';

const logger = new Logger('RateLimiter');

interface RateLimitConfig {
  free: { hourly: number; daily: number };
  basic: { hourly: number; daily: number };
  premium: { hourly: number; daily: number };
  elite: { hourly: number; daily: number };
}

interface RateLimitInfo {
  limit: number;
  remaining: number;
  resetTime: number;
  retryAfter: number;
}

const DEFAULT_LIMITS: RateLimitConfig = {
  free: { hourly: 100, daily: 500 },
  basic: { hourly: 1000, daily: 10000 },
  premium: { hourly: 10000, daily: 100000 },
  elite: { hourly: 50000, daily: 500000 },
};

class RateLimiter {
  private config: RateLimitConfig;
  private keyPrefix: string = 'rate_limit:';

  constructor(config?: Partial<RateLimitConfig>) {
    this.config = {
      ...DEFAULT_LIMITS,
      ...config,
    };
  }

  /**
   * Get rate limit for subscription tier
   */
  private getLimits(tier: string): { hourly: number; daily: number } {
    return (this.config as any)[tier] || this.config.free;
  }

  /**
   * Check hourly rate limit
   */
  async checkHourlyLimit(userId: string, tier: string): Promise<RateLimitInfo> {
    const client = getRedisClient();
    const limits = this.getLimits(tier);
    const now = new Date();
    const hourKey = `${this.keyPrefix}hourly:${userId}:${now.getFullYear()}-${now.getMonth()}-${now.getDate()}-${now.getHours()}`;

    const current = await client.incr(hourKey);
    await client.expire(hourKey, 3600); // 1 hour

    const remaining = Math.max(0, limits.hourly - current);
    const resetTime = Math.floor(Date.now() / 1000) + 3600;

    return {
      limit: limits.hourly,
      remaining,
      resetTime,
      retryAfter: 3600,
    };
  }

  /**
   * Check daily rate limit
   */
  async checkDailyLimit(userId: string, tier: string): Promise<RateLimitInfo> {
    const client = getRedisClient();
    const limits = this.getLimits(tier);
    const now = new Date();
    const dayKey = `${this.keyPrefix}daily:${userId}:${now.getFullYear()}-${now.getMonth()}-${now.getDate()}`;

    const current = await client.incr(dayKey);
    await client.expire(dayKey, 86400); // 24 hours

    const remaining = Math.max(0, limits.daily - current);
    const resetTime = Math.floor(Date.now() / 1000) + 86400;

    return {
      limit: limits.daily,
      remaining,
      resetTime,
      retryAfter: 86400,
    };
  }

  /**
   * Check if user has quota remaining
   */
  async hasQuota(userId: string, tier: string): Promise<boolean> {
    try {
      const hourly = await this.checkHourlyLimit(userId, tier);
      const daily = await this.checkDailyLimit(userId, tier);

      return hourly.remaining > 0 && daily.remaining > 0;
    } catch (error) {
      logger.error('Error checking quota:', error);
      // Fail open - allow request if Redis is down
      return true;
    }
  }

  /**
   * Get quota info
   */
  async getQuotaInfo(userId: string, tier: string): Promise<any> {
    try {
      const hourly = await this.checkHourlyLimit(userId, tier);
      const daily = await this.checkDailyLimit(userId, tier);

      return {
        hourly: {
          limit: hourly.limit,
          remaining: hourly.remaining,
          resetTime: hourly.resetTime,
        },
        daily: {
          limit: daily.limit,
          remaining: daily.remaining,
          resetTime: daily.resetTime,
        },
      };
    } catch (error) {
      logger.error('Error getting quota info:', error);
      return null;
    }
  }

  /**
   * Reset quota for user
   */
  async resetQuota(userId: string): Promise<boolean> {
    try {
      const client = getRedisClient();
      const pattern = `${this.keyPrefix}*:${userId}:*`;
      const keys = await client.keys(pattern);

      if (keys.length > 0) {
        await client.del(...keys);
        logger.info(`Reset quota for user ${userId}`);
      }

      return true;
    } catch (error) {
      logger.error('Error resetting quota:', error);
      return false;
    }
  }

  /**
   * Express middleware
   */
  middleware() {
    return async (req: Request, res: Response, next: NextFunction) => {
      try {
        // Get user ID and tier from request
        const userId = (req as any).user?.id || 'anonymous';
        const tier = (req as any).user?.tier || 'free';

        // Check quota
        const hasQuota = await this.hasQuota(userId, tier);

        if (!hasQuota) {
          logger.warn(`Rate limit exceeded for user ${userId} (${tier})`);

          res.status(429).json({
            error: 'Rate limit exceeded',
            message: `You have exceeded your ${tier} tier rate limit. Please upgrade your subscription or try again later.`,
            retryAfter: 3600,
          });
          return;
        }

        // Get quota info for headers
        const quotaInfo = await this.getQuotaInfo(userId, tier);

        // Set rate limit headers
        if (quotaInfo) {\n          res.setHeader('X-RateLimit-Limit-Hourly', quotaInfo.hourly.limit);
          res.setHeader('X-RateLimit-Remaining-Hourly', quotaInfo.hourly.remaining);
          res.setHeader('X-RateLimit-Reset-Hourly', quotaInfo.hourly.resetTime);
          res.setHeader('X-RateLimit-Limit-Daily', quotaInfo.daily.limit);
          res.setHeader('X-RateLimit-Remaining-Daily', quotaInfo.daily.remaining);
          res.setHeader('X-RateLimit-Reset-Daily', quotaInfo.daily.resetTime);
        }

        next();
      } catch (error) {
        logger.error('Rate limiter error:', error);
        // Fail open
        next();
      }
    };
  }
}

// Singleton instance
let rateLimiter: RateLimiter | null = null;

/**
 * Initialize rate limiter
 */
export function initializeRateLimiter(config?: Partial<RateLimitConfig>): RateLimiter {
  if (!rateLimiter) {
    rateLimiter = new RateLimiter(config);
  }
  return rateLimiter;
}

/**
 * Get rate limiter
 */
export function getRateLimiter(): RateLimiter {
  if (!rateLimiter) {
    rateLimiter = new RateLimiter();
  }
  return rateLimiter;
}

export { RateLimiter, RateLimitConfig, RateLimitInfo };
