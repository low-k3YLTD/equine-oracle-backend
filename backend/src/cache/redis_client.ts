/**
 * Redis Client Configuration and Connection Management
 * Handles connection pooling, error handling, and metrics
 */

import Redis from 'ioredis';
import { Logger } from '../logging/logger';
import { CacheMetrics } from './cache_metrics';

const logger = new Logger('RedisClient');

interface RedisConfig {
  host: string;
  port: number;
  password?: string;
  db?: number;
  maxRetriesPerRequest?: number;
  enableReadyCheck?: boolean;
  enableOfflineQueue?: boolean;
  retryStrategy?: (times: number) => number;
}

class RedisClientManager {
  private client: Redis | null = null;
  private subscriber: Redis | null = null;
  private config: RedisConfig;
  private metrics: CacheMetrics;
  private isConnected: boolean = false;

  constructor(config?: Partial<RedisConfig>) {
    this.config = {
      host: process.env.REDIS_HOST || 'localhost',
      port: parseInt(process.env.REDIS_PORT || '6379'),
      password: process.env.REDIS_PASSWORD,
      db: parseInt(process.env.REDIS_DB || '0'),
      maxRetriesPerRequest: 3,
      enableReadyCheck: true,
      enableOfflineQueue: true,
      retryStrategy: (times: number) => Math.min(times * 50, 2000),
      ...config,
    };

    this.metrics = new CacheMetrics();
  }

  /**
   * Connect to Redis
   */
  async connect(): Promise<void> {
    try {
      this.client = new Redis(this.config);
      this.subscriber = new Redis(this.config);

      // Handle connection events
      this.client.on('connect', () => {
        logger.info('Connected to Redis');
        this.isConnected = true;
      });

      this.client.on('error', (err) => {
        logger.error('Redis error:', err);
        this.isConnected = false;
      });

      this.client.on('reconnecting', () => {
        logger.warn('Reconnecting to Redis...');
      });

      // Wait for connection
      await this.client.ping();
      this.isConnected = true;
      logger.info('Redis connection verified');
    } catch (error) {
      logger.error('Failed to connect to Redis:', error);
      throw error;
    }
  }

  /**
   * Disconnect from Redis
   */
  async disconnect(): Promise<void> {
    try {
      if (this.client) {
        await this.client.quit();
      }
      if (this.subscriber) {
        await this.subscriber.quit();
      }
      this.isConnected = false;
      logger.info('Disconnected from Redis');
    } catch (error) {
      logger.error('Error disconnecting from Redis:', error);
    }
  }

  /**
   * Get Redis client
   */
  getClient(): Redis {
    if (!this.client) {
      throw new Error('Redis client not initialized. Call connect() first.');
    }
    return this.client;
  }

  /**
   * Get subscriber client
   */
  getSubscriber(): Redis {
    if (!this.subscriber) {
      throw new Error('Redis subscriber not initialized. Call connect() first.');
    }
    return this.subscriber;
  }

  /**
   * Check if connected
   */
  isReady(): boolean {
    return this.isConnected && this.client?.status === 'ready';
  }

  /**
   * Get metrics
   */
  getMetrics(): CacheMetrics {
    return this.metrics;
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      const pong = await this.client?.ping();
      return pong === 'PONG';
    } catch (error) {
      logger.error('Redis health check failed:', error);
      return false;
    }
  }
}

// Singleton instance
let redisManager: RedisClientManager | null = null;

/**
 * Initialize Redis client
 */
export async function initializeRedis(config?: Partial<RedisConfig>): Promise<RedisClientManager> {
  if (!redisManager) {
    redisManager = new RedisClientManager(config);
    await redisManager.connect();
  }
  return redisManager;
}

/**
 * Get Redis client manager
 */
export function getRedisManager(): RedisClientManager {
  if (!redisManager) {
    throw new Error('Redis not initialized. Call initializeRedis() first.');
  }
  return redisManager;
}

/**
 * Get Redis client
 */
export function getRedisClient(): Redis {
  return getRedisManager().getClient();
}

/**
 * Disconnect Redis
 */
export async function disconnectRedis(): Promise<void> {
  if (redisManager) {
    await redisManager.disconnect();
    redisManager = null;
  }
}

export { RedisClientManager, RedisConfig };
