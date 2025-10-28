# Augeo Platform Infrastructure Architecture

**Last Updated**: 2025-10-27
**Status**: Phase 2 - Foundational Complete

## Overview

The Augeo Platform is deployed on Microsoft Azure using a modern, cloud-native architecture optimized for scalability, security, and cost-efficiency.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Azure Subscription                        │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Resource Group: augeo-{environment}-rg                    │  │
│  │                                                             │  │
│  │  ┌─────────────────┐    ┌──────────────────────────────┐  │  │
│  │  │ Static Web App  │    │    App Service Plan (Linux)  │  │  │
│  │  │   (Frontend)    │    │  ┌────────────────────────┐  │  │  │
│  │  │                 │    │  │   App Service (API)    │  │  │  │
│  │  │  React Admin    │◄───┼──┤   FastAPI Backend      │  │  │  │
│  │  │                 │    │  │   Docker Container     │  │  │  │
│  │  └─────────────────┘    │  └────────────────────────┘  │  │  │
│  │          │               └──────────────────────────────┘  │  │
│  │          │                              │                   │  │
│  │          │                              ▼                   │  │
│  │          │               ┌──────────────────────────────┐  │  │
│  │          │               │    PostgreSQL Flexible       │  │  │
│  │          │               │    Server (Zone-Redundant)   │  │  │
│  │          │               └──────────────────────────────┘  │  │
│  │          │                              │                   │  │
│  │          │                              ▼                   │  │
│  │          │               ┌──────────────────────────────┐  │  │
│  │          │               │  Azure Cache for Redis       │  │  │
│  │          │               │  (Session Store, Cache)      │  │  │
│  │          │               └──────────────────────────────┘  │  │
│  │          │                                                  │  │
│  │          ▼                                                  │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │           Azure Key Vault (Secrets)                   │ │  │
│  │  │  - Database Connection Strings                        │ │  │
│  │  │  - JWT Signing Keys                                   │ │  │
│  │  │  - API Keys (Stripe, Twilio, etc.)                    │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                              ▲                              │  │
│  │                              │ Managed Identity             │  │
│  │                              │                              │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │      Application Insights + Log Analytics            │ │  │
│  │  │  - Request telemetry                                  │ │  │
│  │  │  - Error tracking                                     │ │  │
│  │  │  - Performance metrics                                │ │  │
│  │  │  - Custom dashboards                                  │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                             │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │      Azure Communication Services (Email)             │ │  │
│  │  │  - Transactional emails                               │ │  │
│  │  │  - Custom domain support                              │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                             │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │      Storage Account (Backups, Logs)                  │ │  │
│  │  │  - Database backups                                   │ │  │
│  │  │  - Redis persistence                                  │ │  │
│  │  │  - Audit logs                                         │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                     DNS Zone (augeo.app)                     │ │
│  │  - api.augeo.app → App Service                              │ │
│  │  - admin.augeo.app → Static Web App                         │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Frontend
- **Hosting**: Azure Static Web Apps (Standard tier)
- **Framework**: React 18 with TypeScript
- **State Management**: Zustand
- **Build Tool**: Vite
- **CDN**: Built-in global CDN with automatic edge caching

### Backend
- **Hosting**: Azure App Service (Linux, Docker containers)
- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy
- **Validation**: Pydantic
- **Authentication**: OAuth2 + JWT with Redis sessions

### Database
- **Engine**: PostgreSQL 14 (Flexible Server)
- **HA**: Zone-Redundant configuration (production only)
- **Backup**: Automated daily backups, 30-day retention (production)
- **Encryption**: TLS in transit, encryption at rest

### Cache & Sessions
- **Engine**: Azure Cache for Redis (Standard tier)
- **Persistence**: AOF (Append-Only File) for production
- **Use Cases**: Session storage, API caching, rate limiting

### Secrets Management
- **Service**: Azure Key Vault
- **Authentication**: Managed Identity (no credentials in code)
- **Features**: Soft delete, purge protection, audit logging

### Email
- **Service**: Azure Communication Services
- **Features**: Custom domain, SPF/DKIM/DMARC authentication
- **Cost**: $0.0012 per email after 10k free monthly

### Monitoring
- **Service**: Application Insights + Log Analytics
- **Metrics**: Request rate, response time, error rate, custom metrics
- **Alerts**: Email, Teams, SMS notifications
- **Dashboards**: System health, infrastructure, cost tracking

### CI/CD
- **Platform**: GitHub Actions
- **Authentication**: OIDC federated credentials (no secrets rotation)
- **Workflows**: PR validation, automated deployment, rollback

## Infrastructure as Code

### Tool Selection: Azure Bicep

**Why Bicep over Terraform:**
- Native Azure integration (official Microsoft tool)
- Simpler syntax (declarative, less verbose)
- No state management required
- Better Azure resource support
- Automatic dependency detection

### Repository Structure

```
infrastructure/
├── bicep/
│   ├── main.bicep              # Orchestration template
│   ├── common.bicep            # Common parameters
│   ├── modules/                # Reusable modules
│   │   ├── resource-group.bicep
│   │   ├── app-service-plan.bicep
│   │   ├── app-service.bicep
│   │   ├── static-web-app.bicep
│   │   ├── database.bicep
│   │   ├── redis.bicep
│   │   ├── key-vault.bicep
│   │   ├── monitoring.bicep
│   │   ├── log-analytics.bicep
│   │   ├── storage.bicep
│   │   ├── dns.bicep
│   │   └── communication.bicep
│   └── parameters/
│       ├── dev.bicepparam
│       ├── staging.bicepparam
│       └── production.bicepparam
└── scripts/
    ├── provision.sh
    ├── validate.sh
    ├── deploy-backend.sh
    ├── deploy-frontend.sh
    └── rollback.sh
```

## Environment Configuration

### Development

**Purpose**: Feature development and testing

**Configuration**:
- App Service Plan: Basic B1 (1 instance)
- PostgreSQL: Burstable B1ms (no HA)
- Redis: Basic C0 (250 MB)
- Backups: 7-day retention
- Cost: ~$42/month

### Staging

**Purpose**: Pre-production validation and QA testing

**Configuration**:
- App Service Plan: Standard S1 (1 instance)
- PostgreSQL: General Purpose D2s_v3 (no HA)
- Redis: Standard C1 (1 GB)
- Backups: 7-day retention
- Cost: ~$100/month

### Production

**Purpose**: Live production workloads

**Configuration**:
- App Service Plan: Standard S1 (2-5 instances, autoscaling)
- PostgreSQL: General Purpose D2s_v3 (Zone-Redundant HA)
- Redis: Standard C1 (1 GB, AOF persistence)
- Backups: 30-day retention
- Resource locks: Enabled (prevent accidental deletion)
- Cost: ~$289/month

## Security Architecture

### Network Security
- App Service VNet integration (planned)
- Private endpoints for PostgreSQL (production)
- Redis firewall rules (App Service subnet only)
- Key Vault network ACLs

### Identity & Access
- Managed Identity for all service-to-service authentication
- Azure AD authentication for PostgreSQL (planned)
- RBAC for resource access control
- Audit logging for all access

### Data Protection
- TLS 1.2+ for all connections
- Encryption at rest (Azure default)
- Database backups encrypted
- Key Vault for secrets (no hardcoded credentials)

### Compliance
- SOC 2 Type II (Azure compliance)
- GDPR compliance via data residency
- Regular security scanning in CI/CD
- Quarterly disaster recovery drills

## Disaster Recovery

### RTO/RPO Targets

| Component | RTO | RPO | Recovery Method |
|-----------|-----|-----|-----------------|
| App Service | 15 min | 0 | Redeploy from GitHub |
| Static Web App | 5 min | 0 | Redeploy from GitHub |
| PostgreSQL | 1 hour | 15 min | Point-in-time restore |
| Redis | 30 min | 1 hour | RDB snapshot restore |
| Key Vault | N/A | N/A | Soft delete (90-day recovery) |

### Backup Strategy
- **PostgreSQL**: Automated daily backups, 30-day retention
- **Redis**: RDB snapshots every 4 hours to Storage Account
- **Application Code**: Git repository (GitHub)
- **Infrastructure**: Bicep templates in Git

## Cost Optimization

### Resource Tagging
All resources tagged with:
- `Environment`: dev/staging/production
- `Project`: augeo-platform
- `Owner`: operations
- `CostCenter`: For chargeback

### Cost Controls
- Azure Cost Management budgets with alerts
- Autoscaling to match demand (production)
- Dev environment shut down outside business hours (planned)
- Storage lifecycle policies (archive after 90 days)

### Monthly Cost Estimates

| Environment | Monthly Cost | Annual Cost |
|-------------|--------------|-------------|
| Development | $42 | $504 |
| Staging | $100 | $1,200 |
| Production | $289 | $3,468 |
| **Total** | **$431** | **$5,172** |

## Deployment Strategy

### Blue-Green Deployment
- App Service deployment slots
- Zero-downtime deployments
- Quick rollback capability (swap slots)

### Database Migrations
- Alembic for schema migrations
- Run migrations before app deployment
- Backward-compatible changes only

### CI/CD Pipeline
1. PR validation (tests, linting, Bicep validation)
2. Merge to main → auto-deploy to staging
3. Manual approval → deploy to production
4. Health checks post-deployment
5. Auto-rollback on failure

## Monitoring & Alerting

### Key Metrics
- Request rate (requests/minute)
- Response time (P95 latency)
- Error rate (%)
- CPU usage (%)
- Memory usage (%)
- Database connections
- Redis cache hit rate

### Alert Rules
- **Critical**: Error rate >5%, P95 latency >500ms
- **Warning**: CPU >80%, Memory >80%
- **Info**: Deployment success/failure

### Notification Channels
- Email (operations team)
- Microsoft Teams webhook
- SMS for critical alerts (on-call rotation)

## Next Steps

1. ✅ **Phase 1: Setup** - Complete
2. ✅ **Phase 2: Foundational** - Complete
3. 🔄 **Phase 3: Infrastructure Provisioning** - In Progress
4. 📋 **Phase 4: CI/CD Pipeline** - Planned
5. 📋 **Phase 5: Custom Domain & Email** - Planned
6. 📋 **Phase 6: Secrets Management** - Planned
7. 📋 **Phase 7: Backup & DR** - Planned
8. 📋 **Phase 8: Monitoring** - Planned
9. 📋 **Phase 9: Polish** - Planned

## References

- **Specification**: `/specs/004-cloud-infrastructure-deployment/spec.md`
- **Research Decisions**: `/specs/004-cloud-infrastructure-deployment/research.md`
- **Data Model**: `/specs/004-cloud-infrastructure-deployment/data-model.md`
- **Tasks**: `/specs/004-cloud-infrastructure-deployment/tasks.md`
- **Quickstart Guide**: `/specs/004-cloud-infrastructure-deployment/quickstart.md`
