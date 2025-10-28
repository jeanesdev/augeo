# Augeo Platform

**Status**: Phase 9 Complete - Production Ready Infrastructure

A comprehensive nonprofit donation tracking platform built with modern cloud-native architecture on Microsoft Azure.

## Overview

Augeo Platform enables nonprofit organizations to track donations, manage donors, coordinate volunteers, and engage their communities. The platform consists of:

- **Admin Portal**: React-based dashboard for NPO staff
- **Donor PWA**: Progressive web app for donor engagement
- **Backend API**: FastAPI-based REST API
- **Infrastructure**: Azure cloud infrastructure with IaC (Bicep)

## Quick Start

### Prerequisites

- **Azure CLI** (2.50+): `curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash`
- **Bicep CLI** (0.20+): Included with Azure CLI
- **Docker**: For local development
- **Node.js** (22+) with **pnpm**: Frontend development
- **Python** (3.11+) with **Poetry**: Backend development
- **Make**: Command orchestration

### Local Development

```bash
# Clone repository
git clone https://github.com/jeanesdev/augeo-platform.git
cd augeo-platform

# Start backend (API server on http://localhost:8000)
make dev-backend  # or make b

# Start frontend (Admin portal on http://localhost:5173)
make dev-frontend  # or make f

# Run both together
make dev-fullstack

# Run tests
make test
```

### Infrastructure Setup

See [Infrastructure README](./infrastructure/README.md) for complete deployment guide.

```bash
# Quick infrastructure deployment
make deploy-infra ENV=production TAG=v1.0.0

# Deploy backend application
make deploy-backend ENV=production TAG=v1.0.0

# Deploy frontend application
make deploy-frontend ENV=production TAG=v1.0.0
```

## Project Structure

```
augeo-platform/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   ├── core/           # Core utilities (config, database, security)
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── services/       # Business logic layer
│   │   └── tests/          # Test suite (224 tests, 40% coverage)
│   ├── alembic/            # Database migrations
│   └── pyproject.toml      # Python dependencies (Poetry)
│
├── frontend/
│   ├── augeo-admin/        # React admin dashboard
│   │   ├── src/
│   │   │   ├── components/ # React components
│   │   │   ├── pages/      # Page components
│   │   │   ├── stores/     # Zustand state management
│   │   │   └── lib/        # Utilities and API client
│   │   └── package.json    # Node dependencies (pnpm)
│   │
│   └── donor-pwa/          # Progressive web app (planned)
│
├── infrastructure/          # Azure infrastructure as code
│   ├── bicep/
│   │   ├── modules/        # Reusable Bicep modules (11 Azure resources)
│   │   ├── parameters/     # Environment configurations (dev, staging, prod)
│   │   └── main.bicep      # Orchestration template
│   └── scripts/            # Deployment automation scripts
│
├── docs/
│   └── operations/         # Operational documentation
│       ├── architecture.md         # Infrastructure overview
│       ├── ci-cd-guide.md          # Deployment guide
│       ├── monitoring-guide.md     # Monitoring & alerting
│       ├── disaster-recovery.md    # DR procedures
│       ├── cost-optimization.md    # Cost management
│       ├── quick-reference.md      # Common operations
│       └── security-checklist.md   # Security validation
│
├── specs/                   # Feature specifications
├── Makefile                # Command shortcuts
└── docker-compose.yml      # Local development services
```

## Technology Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **State Management**: Zustand
- **Build Tool**: Vite
- **UI Library**: shadcn/ui (Tailwind CSS)
- **Routing**: React Router
- **HTTP Client**: Axios
- **Hosting**: Azure Static Web Apps

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic v2
- **Authentication**: OAuth2 + JWT + Redis sessions
- **Password**: bcrypt
- **Testing**: pytest
- **Hosting**: Azure App Service (Docker containers)

### Infrastructure
- **Cloud Provider**: Microsoft Azure
- **IaC**: Bicep (Azure native)
- **CI/CD**: GitHub Actions
- **Monitoring**: Application Insights + Log Analytics
- **Secrets**: Azure Key Vault
- **Database**: PostgreSQL 15 (Flexible Server)
- **Cache**: Redis (Azure Cache for Redis)
- **Storage**: Azure Blob Storage
- **Email**: Azure Communication Services

## Architecture

### Azure Resources (Production)

| Resource | SKU | Purpose | Cost/month |
|----------|-----|---------|------------|
| App Service Plan | Standard S1 (2-10 instances) | Backend API hosting | ~$73-365 |
| Static Web Apps | Standard | Frontend hosting + CDN | ~$9 |
| PostgreSQL | GeneralPurpose D2s_v3 | Primary database | ~$200 |
| Redis | Standard C1 (1 GB) | Session store + cache | ~$75 |
| Application Insights | 5GB/day cap | Monitoring + telemetry | ~$200 |
| Key Vault | Standard | Secrets management | ~$3 |
| Storage Account | GRS | Backups + logs | ~$50 |
| DNS + Email | - | Custom domain + transactional email | ~$40 |
| **Total** | | | **~$650/month** |

### Key Features

**Auto-scaling**: Scales 2-10 instances based on CPU (>70% scale out, <30% scale in)

**High Availability**: Zone-redundant PostgreSQL, geo-redundant backups

**Disaster Recovery**: 1-hour RTO, 15-minute RPO (production)

**Security**: Managed identities, Key Vault secrets, TLS 1.2+, resource locks

**Monitoring**: 4 alert types, 2 availability tests from 3 regions, custom dashboards

**Cost Management**: Budget alerts (80%, 100%), auto-scaling, daily ingestion caps

## Development Workflow

### Backend Development

```bash
# Install dependencies
cd backend && poetry install

# Run tests
poetry run pytest

# Run linter
poetry run ruff check .

# Run formatter
poetry run black .

# Create migration
poetry run alembic revision -m "description"

# Apply migrations
poetry run alembic upgrade head

# Run dev server
poetry run uvicorn app.main:app --reload
```

### Frontend Development

```bash
# Install dependencies
cd frontend/augeo-admin && pnpm install

# Run dev server
pnpm dev

# Run tests
pnpm test

# Build for production
pnpm build

# Preview production build
pnpm preview
```

### Database Management

```bash
# Connect to local database (Docker)
docker-compose exec postgres psql -U augeo_user -d augeo_db

# Run migrations
make migrate  # or make m

# Create new migration
make migrate-create NAME="add_user_table"

# Seed test data
make db-seed
```

## Deployment

### Environments

| Environment | Purpose | URL | Auto-deploy |
|-------------|---------|-----|-------------|
| Development | Local testing | localhost | No |
| Staging | Pre-production validation | staging.augeo.app | Yes (on merge to main) |
| Production | Live application | augeo.app | Manual approval |

### Deployment Process

1. **PR Validation**: Tests, linting, Bicep validation
2. **Merge to main**: Auto-deploy to staging
3. **Manual approval**: Deploy to production
4. **Health checks**: Verify deployment
5. **Auto-rollback**: On failure (within 30 minutes)

### Quick Deployment Commands

```bash
# Full stack deployment
make deploy-infra ENV=production TAG=v1.0.0
make configure-secrets ENV=production
make deploy-backend ENV=production TAG=v1.0.0
make deploy-frontend ENV=production TAG=v1.0.0

# Backend only
make deploy-backend ENV=production TAG=v1.0.0

# Frontend only
make deploy-frontend ENV=production TAG=v1.0.0

# Rollback
make rollback ENV=production COMPONENT=backend
```

## Common Operations

### View Logs

```bash
# Backend logs (real-time)
make logs-backend ENV=production

# Frontend logs
make logs-frontend ENV=production

# Infrastructure logs
make logs-infra ENV=production
```

### Health Checks

```bash
# All services
make health-check

# Backend only
curl https://api.augeo.app/health

# Frontend only
curl https://admin.augeo.app
```

### Scaling

```bash
# Manual scale
az appservice plan update \
    --name augeo-production-asp \
    --resource-group augeo-production-rg \
    --number-of-workers 5

# View auto-scale settings
make show-autoscale ENV=production
```

### Cost Analysis

```bash
# Current month costs
make cost-analysis ENV=production

# Budget status
make budget-status ENV=production
```

## Monitoring & Alerts

### Dashboards

- **Azure Portal**: Application Insights dashboards
- **System Health**: Request rate, latency, errors, availability
- **Infrastructure**: CPU, memory, database, Redis metrics

### Alert Rules

- **Critical**: Error rate >5%, latency >500ms, availability failures
- **Warning**: CPU >70%, memory >80%
- **Budget**: 80%, 90% (forecast), 100% of monthly budget

### Availability Tests

- Backend: /health endpoint every 5 minutes from 3 regions
- Frontend: Homepage every 5 minutes from 3 regions

## Security

### Authentication
- OAuth2 with JWT (15-min access tokens, 7-day refresh tokens)
- bcrypt password hashing (cost factor 12)
- Redis session store with device tracking
- Rate limiting (5 login attempts per 15 minutes)

### Network Security
- HTTPS only (TLS 1.2+)
- PostgreSQL SSL required
- Redis TLS enforced
- Key Vault for all secrets
- Azure services firewall rules

### Compliance
- SOC 2 Type II (Azure compliance)
- GDPR via data residency
- Security scanning in CI/CD
- Quarterly DR drills

## Documentation

- [Infrastructure Setup](./infrastructure/README.md) - Complete deployment guide
- [Backend README](./backend/README.md) - Backend development guide
- [Frontend README](./frontend/augeo-admin/README.md) - Frontend development guide
- [Architecture Overview](./docs/operations/architecture.md) - Infrastructure details
- [CI/CD Guide](./docs/operations/ci-cd-guide.md) - Deployment procedures
- [Monitoring Guide](./docs/operations/monitoring-guide.md) - Monitoring & alerting
- [Disaster Recovery](./docs/operations/disaster-recovery.md) - DR procedures
- [Cost Optimization](./docs/operations/cost-optimization.md) - Cost management
- [Quick Reference](./docs/operations/quick-reference.md) - Common operations
- [Security Checklist](./docs/operations/security-checklist.md) - Security validation
- [DNS Configuration](./docs/operations/dns-configuration.md) - Domain setup & configuration

## Domain Information

- **Domain**: `augeo.app`
- **Registrar**: Namecheap
- **Registered**: October 28, 2025
- **Expires**: October 28, 2026
- **Auto-Renewal**: Enabled
- **Status**: Ready for Azure DNS configuration

## Contributing

1. Create feature branch from `main`
2. Implement changes with tests
3. Run pre-commit hooks: `make check-commits`
4. Create pull request
5. Wait for CI validation
6. Get approval and merge

## Support

- **Email**: engineering@augeo.app
- **On-call**: ops@augeo.app
- **GitHub Issues**: [augeo-platform/issues](https://github.com/jeanesdev/augeo-platform/issues)

## License

Copyright © 2025 Augeo Platform. All rights reserved.
