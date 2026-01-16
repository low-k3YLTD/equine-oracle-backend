# Phase 1 Implementation Guide
**Quick Wins: Weeks 1-4**

## Overview

This guide provides step-by-step instructions for implementing Phase 1 quick wins that deliver immediate value:
- +1.5-2.5% accuracy improvement
- -50% latency reduction
- All models online
- Production observability

## Core Components Implemented

### 1. Weighted Ensemble (`ml/ensemble/weighted_ensemble.py`)

**What it does**:
- Combines multiple ML models with performance-based weights
- Provides confidence scores for predictions
- Supports probability calibration
- Tracks uncertainty intervals

**Key Classes**:
- `WeightedEnsemble` - Main ensemble implementation
- `EnsembleOptimizer` - Bayesian optimization for weight discovery
- `ModelMetrics` - Performance tracking

**Usage Example**:
```python
from ml.ensemble.weighted_ensemble import WeightedEnsemble, EnsembleOptimizer

# Initialize ensemble with models
ensemble = WeightedEnsemble({
    'lgbm_ranker': lgbm_model,
    'xgboost': xgb_model,
    'random_forest': rf_model,
    'gradient_boosting': gb_model,
    'logistic_regression': lr_model
})

# Set optimal weights (from optimization)
ensemble.set_weights({
    'lgbm_ranker': 0.35,
    'xgboost': 0.25,
    'random_forest': 0.20,
    'gradient_boosting': 0.12,
    'logistic_regression': 0.08
})

# Make predictions with confidence
predictions, confidence = ensemble.predict_with_confidence(X_test)

# Evaluate performance
metrics = ensemble.evaluate(X_test, y_test)
print(f"NDCG@1: {metrics['ndcg_at_1']:.4f}")
```

### 2. Model Registry (`ml/models/model_registry.py`)

**What it does**:
- Manages model versioning and compatibility
- Handles version mismatches gracefully
- Provides fallback loading strategies
- Tracks model metadata

**Key Classes**:
- `ModelRegistry` - Centralized model management
- `CompatibilityLayer` - Version compatibility checking

**Usage Example**:
```python
from ml.models.model_registry import ModelRegistry

# Initialize registry
registry = ModelRegistry('./models')

# Register models with version info
registry.register_model(
    'lgbm_ranker',
    lgbm_model,
    version='1.0',
    sklearn_version='1.3.2'
)

# Load models with automatic fallback
ensemble = registry.load_ensemble([
    'lgbm_ranker',
    'xgboost',
    'random_forest'
])

# Check compatibility
report = registry.get_compatibility_report()
print(f"Compatibility issues: {report['total_issues']}")
```

### 3. Redis Caching (`backend/src/cache/`)

**What it does**:
- Caches predictions with 5-minute TTL
- Tracks cache hit/miss metrics
- Supports compression for large entries
- Provides cache invalidation

**Key Files**:
- `redis_client.ts` - Connection management
- `prediction_cache.ts` - Prediction caching logic
- `cache_metrics.ts` - Metrics tracking

**Usage Example**:
```typescript
import { initializeRedis } from './cache/redis_client';
import { initializePredictionCache } from './cache/prediction_cache';

// Initialize Redis
await initializeRedis();

// Initialize cache
const cache = initializePredictionCache({ ttl: 300 });

// Get from cache
let prediction = await cache.get(raceId, raceData);

if (!prediction) {
  // Cache miss - generate prediction
  prediction = await generatePrediction(raceData);
  
  // Store in cache
  await cache.set(raceId, raceData, prediction);
}

// Get cache stats
const stats = await cache.getStats();
console.log(`Cache hit rate: ${stats.hitRate}`);
```

### 4. Rate Limiting (`backend/src/middleware/rate_limiter.ts`)

**What it does**:
- Enforces subscription tier limits
- Tracks hourly and daily quotas
- Returns rate limit headers
- Supports quota reset

**Tier Limits**:
```
Free:     100 req/hour,   500 req/day
Basic:   1000 req/hour, 10000 req/day
Premium: 10000 req/hour, 100000 req/day
Elite:   50000 req/hour, 500000 req/day
```

**Usage Example**:
```typescript
import { initializeRateLimiter } from './middleware/rate_limiter';

// Initialize rate limiter
const rateLimiter = initializeRateLimiter();

// Use as Express middleware
app.use(rateLimiter.middleware());

// Check quota programmatically
const hasQuota = await rateLimiter.hasQuota(userId, tier);

// Get quota info
const quotaInfo = await rateLimiter.getQuotaInfo(userId, tier);
console.log(`Remaining today: ${quotaInfo.daily.remaining}`);
```

### 5. Monitoring (`monitoring/`)

**What it does**:
- Prometheus metrics collection
- Alert rules for critical issues
- Grafana dashboard configuration
- Performance tracking

**Key Metrics**:
- `prediction_latency_ms` - Prediction time
- `model_accuracy_ndcg` - Model accuracy
- `cache_hit_rate` - Cache effectiveness
- `api_requests_total` - Request volume
- `rate_limit_exceeded_total` - Limit violations

**Setup**:
```bash
# Start Prometheus
docker run -d -p 9090:9090 \
  -v $(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v $(pwd)/monitoring/alerts.yml:/etc/prometheus/alerts.yml \
  prom/prometheus

# Start Grafana
docker run -d -p 3000:3000 grafana/grafana
```

## Integration Steps

### Step 1: Set Up Environment

```bash
# Backend
cd backend
npm install redis ioredis express
npm install --save-dev @types/express @types/node

# ML
cd ../ml
pip install -r requirements.txt
pip install scikit-learn==1.3.2 xgboost==2.0.3 lightgbm==4.1.0
```

### Step 2: Configure Services

```bash
# Create .env file
cat > backend/.env << EOF
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
DATABASE_URL=postgresql://user:pass@localhost:5432/equine_oracle
LOG_LEVEL=INFO
NODE_ENV=development
EOF

# Create Python config
cat > ml/config.py << EOF
MODEL_PATH = './models'
CACHE_TTL = 300
BATCH_SIZE = 32
EOF
```

### Step 3: Initialize Services

```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Start PostgreSQL
docker run -d -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  postgres:14

# Start backend
cd backend
npm run dev

# Start ML service
cd ../ml
python -m inference.prediction_service
```

### Step 4: Test Components

```bash
# Test Redis connection
redis-cli ping

# Test cache
curl http://localhost:3000/api/cache/stats

# Test rate limiting
curl -H "Authorization: Bearer token" \
  http://localhost:3000/api/predict

# Test metrics
curl http://localhost:3000/metrics
```

## Performance Validation

### Benchmark Predictions

```python
import time
from ml.ensemble.weighted_ensemble import WeightedEnsemble

# Load ensemble
ensemble = WeightedEnsemble.load('./models/ensemble_v1.pkl')

# Benchmark
start = time.time()
for _ in range(1000):
    predictions = ensemble.predict(X_test)
elapsed = time.time() - start

print(f"1000 predictions in {elapsed:.2f}s")
print(f"Avg latency: {(elapsed/1000)*1000:.2f}ms")
```

### Load Test

```bash
# Using Apache Bench
ab -n 10000 -c 100 http://localhost:3000/api/predict

# Using wrk
wrk -t4 -c100 -d30s http://localhost:3000/api/predict
```

### Cache Effectiveness

```bash
# Monitor cache stats
watch -n 5 'curl -s http://localhost:3000/api/cache/stats | jq'
```

## Monitoring & Observability

### Key Dashboards

1. **System Health**
   - CPU, Memory, Disk usage
   - Network I/O
   - Uptime

2. **Model Performance**
   - NDCG@1, @3 scores
   - Prediction confidence
   - Model inference time
   - Accuracy trends

3. **API Metrics**
   - Request rate
   - Error rate
   - Latency distribution
   - Rate limit violations

4. **Business Metrics**
   - Predictions/hour
   - Active users
   - Subscription distribution
   - Revenue tracking

### Alert Configuration

Critical alerts:
- Prediction service down
- Model accuracy < 0.95
- Error rate > 5%
- Database connection pool exhausted

Warning alerts:
- Latency p95 > 200ms
- Cache hit rate < 50%
- High CPU/Memory usage
- Slow database queries

## Troubleshooting

### Issue: Cache not working

```bash
# Check Redis connection
redis-cli ping

# Check cache metrics
curl http://localhost:3000/api/cache/stats

# Clear cache
redis-cli FLUSHDB
```

### Issue: Rate limiting too strict

```python
# Adjust limits in rate_limiter.ts
DEFAULT_LIMITS = {
    'free': { hourly: 200, daily: 1000 },  # Increased
    ...
}
```

### Issue: Model loading fails

```python
# Check compatibility
from ml.models.model_registry import CompatibilityLayer
CompatibilityLayer.validate_environment()

# Get compatibility report
registry.get_compatibility_report()
```

### Issue: High latency

```bash
# Check cache hit rate
curl http://localhost:3000/api/cache/stats

# Check database query time
curl http://localhost:3000/metrics | grep database_query

# Check model inference time
curl http://localhost:3000/metrics | grep model_inference
```

## Success Criteria Checklist

- [ ] Weighted ensemble implemented and tested
- [ ] All 5+ models loading successfully
- [ ] NDCG@1 ≥ 0.970 (improvement from 0.9529)
- [ ] Redis caching operational
- [ ] Cache hit rate > 60%
- [ ] API latency p95 < 200ms
- [ ] Rate limiting enforced
- [ ] Prometheus metrics collected
- [ ] Grafana dashboards operational
- [ ] Alert rules configured
- [ ] Load tests passed (1000 req/s)
- [ ] Documentation complete

## Next Steps

After Phase 1 completion:

1. **Phase 2**: Production Hardening
   - Microservices migration
   - Kubernetes deployment
   - Automated retraining

2. **Phase 3**: Advanced Features
   - Explainable AI
   - Live race updates
   - Advanced analytics

3. **Phase 4**: Scale & Optimize
   - Multi-region deployment
   - Transformer models
   - B2B API platform

## Support & Resources

- **Documentation**: See `docs/` directory
- **API Reference**: `docs/API_REFERENCE.md`
- **ML Pipeline**: `docs/ML_PIPELINE.md`
- **Deployment**: `docs/DEPLOYMENT.md`
- **Issues**: GitHub Issues
- **Email**: support@equineoracle.com

---

**Phase 1 Status**: Implementation Guide Complete  
**Last Updated**: January 2026
