# Equine Oracle - Unified Backend System

**Version**: 2.0.0 (Strategic Vision Implementation)  
**Status**: Phase 1 - Quick Wins (In Progress)

## Overview

This is the unified backend system for Equine Oracle, integrating:
- **TS API** - TypeScript/Node.js REST API with tRPC procedures
- **ML Pipeline** - Python-based ensemble ML models with auto-retraining
- **Monitoring & Drift Detection** - Real-time accuracy tracking and model drift detection
- **Continuous Prediction System** - 24/7 autonomous race monitoring and predictions

## Strategic Vision

Transform Equine Oracle from a strong proof-of-concept into a production-grade, market-leading prediction platform through 5 strategic pillars:

1. **ML Pipeline Excellence** - Weighted ensemble, model optimization, advanced features
2. **Production Architecture** - Microservices, Kubernetes, high-performance APIs
3. **Data & ML Ops** - Automated retraining, feature store, monitoring
4. **Security & Compliance** - Advanced threat detection, GDPR compliance, encryption
5. **Mobile & UX** - Enhanced Android app, real-time updates, explainable AI

## Project Structure

```
equine-oracle-unified-backend/
├── backend/                          # TypeScript/Node.js API
│   ├── src/
│   │   ├── api/                     # REST API endpoints
│   │   ├── services/                # Business logic
│   │   ├── models/                  # Data models
│   │   ├── middleware/              # Auth, rate limiting, etc.
│   │   └── utils/                   # Utilities
│   ├── package.json
│   └── tsconfig.json
├── ml/                              # Python ML Pipeline
│   ├── models/                      # Trained models
│   ├── training/                    # Training scripts
│   ├── inference/                   # Prediction service
│   ├── monitoring/                  # Drift detection
│   ├── features/                    # Feature engineering
│   └── requirements.txt
├── monitoring/                      # Prometheus/Grafana configs
│   ├── prometheus.yml
│   ├── grafana/
│   └── dashboards/
├── docker/                          # Docker configurations
│   ├── Dockerfile.backend
│   ├── Dockerfile.ml
│   └── docker-compose.yml
├── kubernetes/                      # K8s manifests
│   ├── deployment.yml
│   ├── service.yml
│   └── hpa.yml
├── docs/                            # Documentation
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── ML_PIPELINE.md
│   └── DEPLOYMENT.md
└── tests/                           # Test suites
    ├── backend/
    ├── ml/
    └── integration/
```

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/low-k3YLTD/equine-oracle-backend.git
cd equine-oracle-backend
```

2. **Set up backend**
```bash
cd backend
npm install
cp .env.example .env
npm run dev
```

3. **Set up ML pipeline**
```bash
cd ml
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m inference.prediction_service
```

4. **Start monitoring**
```bash
docker-compose -f docker/docker-compose.yml up prometheus grafana
```

## Phase 1: Quick Wins (Weeks 1-4)

### Implemented Features

- [x] **Weighted Ensemble Optimization** - Performance-based model weights
- [x] **Model Compatibility Fixes** - Version management and fallback handling
- [x] **Redis Caching** - 5-minute TTL for predictions
- [x] **API Rate Limiting** - Subscription tier-based limits
- [x] **Monitoring Dashboard** - Prometheus + Grafana integration

### Expected Outcomes

- NDCG@1 improvement to 0.970+
- API latency reduced to <200ms (p95)
- All 5+ models active in ensemble
- Basic observability in place

## API Endpoints

### Predictions
- `POST /api/v2/predict` - Get race predictions
- `POST /api/v2/predict/batch` - Batch predictions
- `GET /api/v2/predictions/history` - Prediction history

### Subscription Management
- `GET /api/v2/subscriptions/current` - Current subscription
- `GET /api/v2/subscriptions/rate-limit` - Rate limit info
- `POST /api/v2/subscriptions/upgrade` - Upgrade subscription

### Monitoring
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /api/v2/system/status` - System status

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/equine_oracle
REDIS_URL=redis://localhost:6379

# API
API_PORT=3000
NODE_ENV=development

# ML
MODEL_PATH=/models
PREDICTION_INTERVAL=300000

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

## Testing

```bash
# Backend tests
cd backend
npm test

# ML tests
cd ml
pytest tests/

# Integration tests
npm run test:integration
```

## Deployment

### Docker Compose (Development)
```bash
docker-compose -f docker/docker-compose.yml up
```

### Kubernetes (Production)
```bash
kubectl apply -f kubernetes/
kubectl rollout status deployment/prediction-service
```

## Monitoring & Observability

### Prometheus Metrics
- `prediction_latency_ms` - Prediction processing time
- `model_accuracy_ndcg` - Model accuracy metrics
- `api_requests_total` - Total API requests
- `rate_limit_exceeded_total` - Rate limit violations

### Grafana Dashboards
- **System Health** - CPU, memory, uptime
- **Model Performance** - Accuracy, confidence, latency
- **API Metrics** - Requests, errors, latency distribution
- **Business Metrics** - Predictions/hour, active users, revenue

## Documentation

- [Architecture Design](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [ML Pipeline Guide](docs/ML_PIPELINE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Strategic Vision](docs/STRATEGIC_VISION.md)

## Performance Benchmarks

| Metric | Target | Current |
|--------|--------|---------|
| Prediction Latency (p95) | <150ms | TBD |
| Prediction Latency (p50) | <80ms | TBD |
| API Uptime | 99.95% | TBD |
| Throughput | 10,000 req/s | TBD |
| Model Accuracy (NDCG@1) | 0.975+ | 0.9529 |

## Roadmap

### Phase 1: Quick Wins (Weeks 1-4) ✅
- Weighted ensemble optimization
- Model compatibility fixes
- Redis caching
- Rate limiting
- Monitoring dashboard

### Phase 2: Production Hardening (Weeks 5-12)
- Microservices migration
- Kubernetes deployment
- Automated retraining
- Feature store
- Advanced security

### Phase 3: Advanced Features (Weeks 13-24)
- Multi-model predictions
- Explainable AI (SHAP/LIME)
- Live race updates
- Advanced analytics
- Mobile app v2

### Phase 4: Scale & Optimize (Weeks 25-52)
- Multi-region deployment
- Transformer-based models
- B2B API platform
- Mobile SDK
- White-label solution

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/your-feature`
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or suggestions:
- GitHub Issues: [Report a bug](https://github.com/low-k3YLTD/equine-oracle-backend/issues)
- Email: support@equineoracle.com
- Documentation: [Docs](docs/)

---

**Last Updated**: January 2026  
**Maintained by**: Equine Oracle Team
