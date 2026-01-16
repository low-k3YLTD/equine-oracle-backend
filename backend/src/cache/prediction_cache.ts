/**
 * Prediction Caching Layer
 * Implements Redis-backed caching for race predictions
 */

import { getRedisClient, getRedisManager } from './redis_client';
import { Logger } from '../logging/logger';
import crypto from 'crypto';

const logger = new Logger('PredictionCache');

interface CacheEntry {
  predictions: any[];
  confidence: number;
  modelVersion: string;
  processingTimeMs: number;
  timestamp: number;
}

interface CacheConfig {
  ttl: number; // Time to live in seconds
  keyPrefix: string;
  compressionThreshold: number; // Compress if larger than this (bytes)
}

class PredictionCache {
  private config: CacheConfig;
  private metrics = {
    hits: 0,
    misses: 0,
    errors: 0,
    evictions: 0,
  };

  constructor(config?: Partial<CacheConfig>) {
    this.config = {
      ttl: 300, // 5 minutes default
      keyPrefix: 'prediction:',
      compressionThreshold: 1024, // 1KB
      ...config,
    };
  }

  /**
   * Generate cache key from race data
   */
  private generateCacheKey(raceId: string, raceData: any): string {
    const hash = crypto
      .createHash('sha256')
      .update(JSON.stringify(raceData))
      .digest('hex')
      .substring(0, 16);

    return `${this.config.keyPrefix}${raceId}:${hash}`;
  }

  /**
   * Get prediction from cache
   */
  async get(raceId: string, raceData: any): Promise<CacheEntry | null> {
    try {
      const client = getRedisClient();
      const key = this.generateCacheKey(raceId, raceData);

      const cached = await client.getBuffer(key);

      if (!cached) {
        this.metrics.misses++;
        return null;
      }

      // Decompress if needed
      let data: CacheEntry;
      try {
        data = JSON.parse(cached.toString());
      } catch {
        // Try decompressing
        const zlib = require('zlib');
        const decompressed = zlib.gunzipSync(cached);
        data = JSON.parse(decompressed.toString());
      }

      this.metrics.hits++;
      logger.debug(`Cache hit for ${raceId}`);

      return data;
    } catch (error) {
      logger.error('Cache get error:', error);
      this.metrics.errors++;
      return null;
    }
  }

  /**
   * Set prediction in cache
   */
  async set(
    raceId: string,
    raceData: any,
    entry: CacheEntry,
    ttl?: number
  ): Promise<boolean> {
    try {
      const client = getRedisClient();
      const key = this.generateCacheKey(raceId, raceData);

      let data = JSON.stringify(entry);

      // Compress if needed
      if (data.length > this.config.compressionThreshold) {
        const zlib = require('zlib');
        data = zlib.gzipSync(data).toString('base64');
      }

      const expiryTime = ttl || this.config.ttl;
      await client.setex(key, expiryTime, data);

      logger.debug(`Cached prediction for ${raceId} (TTL: ${expiryTime}s)`);
      return true;
    } catch (error) {
      logger.error('Cache set error:', error);
      this.metrics.errors++;
      return false;
    }
  }

  /**
   * Delete prediction from cache
   */
  async delete(raceId: string, raceData: any): Promise<boolean> {
    try {
      const client = getRedisClient();
      const key = this.generateCacheKey(raceId, raceData);

      await client.del(key);
      logger.debug(`Deleted cache entry for ${raceId}`);
      return true;
    } catch (error) {
      logger.error('Cache delete error:', error);
      return false;
    }
  }

  /**
   * Clear all predictions from cache
   */
  async clear(): Promise<boolean> {
    try {
      const client = getRedisClient();
      const pattern = `${this.config.keyPrefix}*`;

      const keys = await client.keys(pattern);
      if (keys.length > 0) {
        await client.del(...keys);
        this.metrics.evictions += keys.length;
        logger.info(`Cleared ${keys.length} cache entries`);
      }

      return true;
    } catch (error) {
      logger.error('Cache clear error:', error);
      return false;
    }
  }

  /**
   * Get cache statistics
   */
  async getStats(): Promise<any> {
    try {
      const client = getRedisClient();
      const pattern = `${this.config.keyPrefix}*`;
      const keys = await client.keys(pattern);

      const totalSize = await Promise.all(
        keys.map((key) => client.strlen(key))
      ).then((sizes) => sizes.reduce((a, b) => a + b, 0));

      const hitRate =
        this.metrics.hits + this.metrics.misses > 0
          ? (this.metrics.hits / (this.metrics.hits + this.metrics.misses)) * 100
          : 0;

      return {
        entries: keys.length,
        totalSizeBytes: totalSize,
        hits: this.metrics.hits,
        misses: this.metrics.misses,
        errors: this.metrics.errors,
        evictions: this.metrics.evictions,
        hitRate: hitRate.toFixed(2) + '%',
      };
    } catch (error) {
      logger.error('Error getting cache stats:', error);
      return null;
    }
  }

  /**
   * Invalidate cache by pattern
   */
  async invalidateByPattern(pattern: string): Promise<number> {
    try {
      const client = getRedisClient();
      const keys = await client.keys(pattern);

      if (keys.length > 0) {
        await client.del(...keys);
        this.metrics.evictions += keys.length;
        logger.info(`Invalidated ${keys.length} cache entries matching ${pattern}`);
      }

      return keys.length;
    } catch (error) {
      logger.error('Cache invalidation error:', error);
      return 0;
    }
  }

  /**
   * Get metrics
   */
  getMetrics() {
    return { ...this.metrics };
  }

  /**
   * Reset metrics
   */
  resetMetrics() {
    this.metrics = {
      hits: 0,
      misses: 0,
      errors: 0,
      evictions: 0,
    };
  }
}

// Singleton instance
let predictionCache: PredictionCache | null = null;

/**
 * Initialize prediction cache
 */
export function initializePredictionCache(config?: Partial<CacheConfig>): PredictionCache {
  if (!predictionCache) {
    predictionCache = new PredictionCache(config);
  }
  return predictionCache;
}

/**
 * Get prediction cache
 */
export function getPredictionCache(): PredictionCache {
  if (!predictionCache) {
    predictionCache = new PredictionCache();
  }
  return predictionCache;
}

export { PredictionCache, CacheEntry, CacheConfig };
