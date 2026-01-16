/**
 * Cache Metrics Tracking
 * Tracks cache performance and exports metrics for monitoring
 */

import { Logger } from '../logging/logger';

const logger = new Logger('CacheMetrics');

interface MetricSnapshot {
  timestamp: number;
  hits: number;
  misses: number;
  hitRate: number;
  avgResponseTimeMs: number;
  totalRequests: number;
}

class CacheMetrics {
  private hits: number = 0;
  private misses: number = 0;
  private totalResponseTime: number = 0;
  private requestCount: number = 0;
  private snapshots: MetricSnapshot[] = [];
  private maxSnapshots: number = 1440; // 24 hours at 1-minute intervals

  /**
   * Record cache hit
   */
  recordHit(responseTimeMs: number = 0): void {
    this.hits++;
    this.totalResponseTime += responseTimeMs;
    this.requestCount++;
  }

  /**
   * Record cache miss
   */
  recordMiss(): void {
    this.misses++;
    this.requestCount++;
  }

  /**
   * Get current metrics
   */
  getMetrics() {
    const hitRate = this.requestCount > 0 ? (this.hits / this.requestCount) * 100 : 0;
    const avgResponseTime = this.hits > 0 ? this.totalResponseTime / this.hits : 0;

    return {
      hits: this.hits,
      misses: this.misses,
      totalRequests: this.requestCount,
      hitRate: hitRate.toFixed(2),
      avgResponseTimeMs: avgResponseTime.toFixed(2),
      timestamp: Date.now(),
    };
  }

  /**
   * Take metrics snapshot
   */
  takeSnapshot(): MetricSnapshot {
    const hitRate = this.requestCount > 0 ? (this.hits / this.requestCount) * 100 : 0;
    const avgResponseTime = this.hits > 0 ? this.totalResponseTime / this.hits : 0;

    const snapshot: MetricSnapshot = {
      timestamp: Date.now(),
      hits: this.hits,
      misses: this.misses,
      hitRate,
      avgResponseTimeMs: avgResponseTime,
      totalRequests: this.requestCount,
    };

    this.snapshots.push(snapshot);

    // Keep only recent snapshots
    if (this.snapshots.length > this.maxSnapshots) {
      this.snapshots.shift();
    }

    return snapshot;
  }

  /**
   * Get snapshots
   */
  getSnapshots(limit?: number): MetricSnapshot[] {
    if (!limit) {
      return [...this.snapshots];
    }
    return this.snapshots.slice(-limit);
  }

  /**
   * Get metrics trend
   */
  getTrend(intervalMinutes: number = 60): any {
    const now = Date.now();
    const intervalMs = intervalMinutes * 60 * 1000;
    const cutoff = now - intervalMs;

    const relevantSnapshots = this.snapshots.filter((s) => s.timestamp >= cutoff);

    if (relevantSnapshots.length === 0) {
      return null;
    }

    const avgHitRate =
      relevantSnapshots.reduce((sum, s) => sum + s.hitRate, 0) / relevantSnapshots.length;
    const avgResponseTime =
      relevantSnapshots.reduce((sum, s) => sum + s.avgResponseTimeMs, 0) /
      relevantSnapshots.length;
    const totalRequests = relevantSnapshots.reduce((sum, s) => sum + s.totalRequests, 0);

    return {
      period: `${intervalMinutes} minutes`,
      avgHitRate: avgHitRate.toFixed(2),
      avgResponseTimeMs: avgResponseTime.toFixed(2),
      totalRequests,
      snapshotCount: relevantSnapshots.length,
    };
  }

  /**
   * Reset metrics
   */
  reset(): void {
    this.hits = 0;
    this.misses = 0;
    this.totalResponseTime = 0;
    this.requestCount = 0;
    this.snapshots = [];
    logger.info('Cache metrics reset');
  }

  /**
   * Export metrics for Prometheus
   */
  exportPrometheus(): string {
    const metrics = this.getMetrics();

    return `
# HELP cache_hits_total Total cache hits
# TYPE cache_hits_total counter
cache_hits_total ${metrics.hits}

# HELP cache_misses_total Total cache misses
# TYPE cache_misses_total counter
cache_misses_total ${metrics.misses}

# HELP cache_requests_total Total cache requests
# TYPE cache_requests_total counter
cache_requests_total ${metrics.totalRequests}

# HELP cache_hit_rate Cache hit rate percentage
# TYPE cache_hit_rate gauge
cache_hit_rate ${metrics.hitRate}

# HELP cache_avg_response_time_ms Average response time in milliseconds
# TYPE cache_avg_response_time_ms gauge
cache_avg_response_time_ms ${metrics.avgResponseTimeMs}
    `.trim();
  }
}

export { CacheMetrics, MetricSnapshot };
