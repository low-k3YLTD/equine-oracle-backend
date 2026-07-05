# 🚀 Equine Oracle CI/CD Pipeline Documentation

## Overview

This document describes the comprehensive CI/CD pipeline setup for the Equine Oracle project across all three repositories:
- `equine_oracle_admin` - Admin Dashboard with ML Integration
- `equine-oracle-backend` - Backend Services + ML Pipeline  
- `equine-oracle-frontend` - Public Frontend

## 📁 Pipeline Structure

Each repository has the following GitHub Actions workflows:

### 1. **equine_oracle_admin**
```
.github/workflows/
├── ci.yml              # Main CI/CD pipeline
├── ml-training.yml     # ML model training pipeline
├── security.yml        # Security scanning
└── performance.yml     # Performance benchmarking
```

### 2. **equine-oracle-backend**
```
.github/workflows/
├── ci.yml              # Main CI/CD pipeline
├── ml-pipeline.yml     # ML training & evaluation
├── monitoring.yml      # System monitoring
└── security.yml        # Security scanning (recommended)
```

### 3. **equine-oracle-frontend**
```
.github/workflows/
├── ci.yml              # Main CI/CD pipeline
├── security.yml        # Security scanning
└── performance.yml     # Performance monitoring
```

---

## 🎯 Pipeline Features

### Common Features Across All Repositories

1. **Multi-stage Docker Builds**
   - Builder stage for dependency installation and compilation
   - Runtime stage with only necessary files
   - Optimized image sizes

2. **Dependency Caching**
   - pnpm/npm cache for Node.js dependencies
   - pip cache for Python dependencies
   - Build artifact caching

3. **Security Scanning**
   - Dependency vulnerability scanning (npm audit, Snyk)
   - Code security analysis (Semgrep)
   - Secret detection (TruffleHog)
   - Container image scanning (Trivy)

4. **Performance Monitoring**
   - Lighthouse audits for frontend
   - Load testing for backend
   - ML model performance benchmarks

5. **Notifications**
   - Discord notifications on failures
   - Status updates for deployments

---

## 🔧 Setup Instructions

### Prerequisites

1. **GitHub Repository Secrets**
   Add the following secrets to each repository in GitHub Settings > Secrets:

   ```bash
   # Docker Hub
   DOCKER_HUB_USERNAME
   DOCKER_HUB_TOKEN
   
   # AWS (for model storage)
   AWS_ACCESS_KEY_ID
   AWS_SECRET_ACCESS_KEY
   AWS_REGION
   
   # Discord Notifications
   DISCORD_WEBHOOK
   
   # Snyk (optional)
   SNYK_TOKEN
   
   # Vercel (frontend)
   VERCEL_TOKEN
   
   # Railway (backend)
   RAILWAY_TOKEN
   ```

2. **Environment Variables**
   Each workflow uses environment variables defined in the workflow files. You can override these in GitHub Settings > Environment Variables.

---

## 📊 Pipeline Details

### Main CI/CD Pipeline (`ci.yml`)

#### Stages:

1. **Setup & Cache**
   - Checks out repository
   - Sets up Node.js/Python
   - Restores cached dependencies
   - Installs dependencies if cache miss

2. **Lint & Type Check**
   - Runs TypeScript type checking
   - Runs ESLint/Prettier checks
   - Fails on errors

3. **Test**
   - Runs unit tests
   - Sets up test databases
   - Runs integration tests
   - Generates coverage reports

4. **Build**
   - Compiles application
   - Optimizes build output
   - Uploads build artifacts

5. **Docker**
   - Builds Docker images
   - Pushes to Docker Hub & GitHub Container Registry
   - Uses multi-stage builds

6. **Deploy**
   - Deploys to staging (on `develop` branch)
   - Deploys to production (on `main` branch)
   - Supports Railway, Vercel, and custom deployments

---

### ML Training Pipeline (`ml-pipeline.yml`)

#### Features:

1. **Scheduled Training**
   - Runs daily at 3 AM UTC
   - Can be triggered manually

2. **Training Process**
   - Loads data from multiple sources (CSV, Database, S3)
   - Trains all base models (LightGBM, XGBoost, Random Forest, etc.)
   - Optimizes ensemble weights
   - Evaluates model performance

3. **Model Deployment**
   - Uploads trained models to S3
   - Updates model registry
   - Invalidates CDN cache

4. **Quality Gates**
   - NDCG@1 must be > 0.95
   - Accuracy must be > 0.85
   - Fails pipeline if thresholds not met

#### Usage:

```bash
# Manual trigger with default settings
gh workflow run ml-pipeline.yml

# Retrain all models
gh workflow run ml-pipeline.yml -f retrain_all=true

# Only evaluate existing models
gh workflow run ml-pipeline.yml -f evaluate_only=true
```

---

### Monitoring Pipeline (`monitoring.yml`)

#### Features:

1. **System Health Checks**
   - API endpoint monitoring
   - Database connectivity
   - Redis connectivity
   - Model serving health

2. **Performance Metrics**
   - Collects Prometheus metrics
   - Tracks prediction latency
   - Monitors model accuracy
   - Alerts on anomalies

3. **Alert Management**
   - Checks Alertmanager for active alerts
   - Notifies on critical issues

#### Schedule:
- Runs every 15 minutes
- Can be triggered manually

---

## 🐳 Docker Configuration

### Dockerfiles

Each repository has an optimized Dockerfile:

1. **Admin Dashboard** (`equine_oracle_admin/Dockerfile`)
   - Node.js 20 + pnpm
   - Multi-stage build
   - Non-root user for security

2. **Backend Service** (`equine-oracle-backend/backend/Dockerfile`)
   - Node.js 20 + pnpm
   - Production-optimized
   - Health checks

3. **ML Service** (`equine-oracle-backend/ml/Dockerfile`)
   - Python 3.11
   - ML dependencies (LightGBM, XGBoost, etc.)
   - Optimized for inference

4. **Frontend** (`equine-oracle-frontend/Dockerfile`)
   - Node.js 20
   - Next.js optimized
   - Static file serving

### Docker Compose

For local development, use the provided `docker-compose.yml`:

```bash
# Start all services
cd equine-oracle-backend
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild images
docker-compose build --no-cache
```

Services included:
- Backend API (port 3000)
- ML Service (port 5000)
- PostgreSQL (port 5432)
- Redis (port 6379)
- Prometheus (port 9090)
- Grafana (port 3001)
- Node Exporter (port 9100)

---

## 🚀 Deployment

### Backend Deployment

The backend can be deployed to:
1. **Railway** (recommended)
2. **AWS ECS/EKS**
3. **Google Cloud Run**
4. **Custom Kubernetes**

#### Railway Deployment

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Deploy:
   ```bash
   railway up
   ```

3. Configure environment variables in Railway dashboard

### Frontend Deployment

The frontend can be deployed to:
1. **Vercel** (recommended)
2. **Netlify**
3. **AWS S3 + CloudFront**
4. **Custom hosting**

#### Vercel Deployment

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Deploy:
   ```bash
   vercel
   ```

3. Configure environment variables in Vercel dashboard

---

## 📈 Monitoring & Observability

### Prometheus Metrics

The backend exposes Prometheus metrics at `/metrics`:

```yaml
# monitoring/prometheus.yml
scrape_configs:
  - job_name: 'prediction-service'
    static_configs:
      - targets: ['backend:3000']
    metrics_path: '/metrics'
```

Key metrics:
- `prediction_latency_ms` - Prediction processing time
- `model_accuracy_ndcg` - Model accuracy (NDCG)
- `api_requests_total` - Total API requests
- `rate_limit_exceeded_total` - Rate limit violations

### Grafana Dashboards

Pre-configured dashboards for:
- System Health (CPU, memory, uptime)
- Model Performance (accuracy, confidence, latency)
- API Metrics (requests, errors, latency distribution)
- Business Metrics (predictions/hour, active users)

---

## 🔒 Security

### Security Scanning

All repositories include:

1. **Dependency Scanning**
   - npm audit (high severity only)
   - Snyk vulnerability scanning

2. **Code Scanning**
   - Semgrep for security patterns
   - Custom security rules

3. **Secret Scanning**
   - TruffleHog for credential detection
   - Git history scanning

4. **Container Scanning**
   - Trivy vulnerability scanning
   - SARIF report generation

### Security Best Practices

1. **Non-root users** in Docker containers
2. **Minimal base images** (Alpine Linux)
3. **Dependency pinning** (exact versions)
4. **Regular scanning** (daily for main branch)
5. **Secret rotation** (automated reminders)

---

## ⚡ Performance Optimization

### Frontend Performance

1. **Lighthouse Audits**
   - Performance score > 70
   - Accessibility score > 80
   - SEO score > 90

2. **Bundle Analysis**
   - Bundle size monitoring
   - Tree shaking
   - Code splitting

3. **Caching**
   - Static file caching
   - API response caching
   - CDN integration

### Backend Performance

1. **Load Testing**
   - Artillery for load testing
   - Performance thresholds
   - Regression detection

2. **ML Performance**
   - Prediction latency < 150ms (p95)
   - Training time monitoring
   - Model optimization

---

## 📝 Customization

### Adding New Workflows

1. Create a new `.yml` file in `.github/workflows/`
2. Define triggers (`on:` section)
3. Define jobs and steps
4. Use existing secrets and environment variables

### Modifying Existing Workflows

1. Edit the workflow file
2. Test changes in a feature branch
3. Merge to main after validation

### Adding New Environment Variables

1. Go to GitHub Repository Settings
2. Navigate to Environments
3. Add new environment
4. Configure protection rules and variables

---

## 🛠️ Troubleshooting

### Common Issues

1. **Cache Miss**
   - Clear cache: `pnpm store prune`
   - Force rebuild: `force_build=true` input

2. **Dependency Conflicts**
   - Check `pnpm-lock.yaml` for conflicts
   - Run `pnpm install --force`

3. **Docker Build Failures**
   - Check Dockerfile syntax
   - Verify base image exists
   - Check disk space

4. **Test Failures**
   - Check test logs
   - Run tests locally
   - Verify test database setup

5. **Deployment Failures**
   - Check environment variables
   - Verify infrastructure is available
   - Check deployment logs

### Debugging Tips

1. **View Workflow Logs**
   ```bash
   gh run view --log
   ```

2. **Download Artifacts**
   ```bash
   gh run download
   ```

3. **SSH into Runner**
   - Enable debug logging in workflow
   - Use `ubuntu-latest` runner for debugging

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
- [Grafana Documentation](https://grafana.com/docs/)

---

## 🎉 Next Steps

1. **Set up repository secrets** in GitHub
2. **Test workflows** in feature branches
3. **Monitor first runs** and adjust as needed
4. **Set up notifications** for your team
5. **Customize workflows** for your specific needs

---

**Last Updated**: 2026-01-16  
**Maintained by**: Equine Oracle Team
