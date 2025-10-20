# Augeo Platform - Backend API

FastAPI-based backend API for the Augeo nonprofit auction platform, featuring authentication, role-based access control, and multi-tenant data isolation.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Poetry (Python dependency manager)

### Installation

1. **Start infrastructure services**:
   ```bash
   docker-compose up -d
   ```

2. **Install dependencies**:
   ```bash
   cd backend
   poetry install
   poetry shell
   ```

3. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Start development server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

API will be available at: http://localhost:8000
API docs (Swagger): http://localhost:8000/docs

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── api/              # API routes
│   │   └── v1/           # API version 1
│   ├── core/             # Core utilities (config, security, database)
│   ├── middleware/       # Custom middleware (auth, rate limiting)
│   ├── models/           # SQLAlchemy database models
│   ├── schemas/          # Pydantic request/response schemas
│   ├── services/         # Business logic services
│   └── tests/            # Test suite
├── alembic/              # Database migrations
│   └── versions/         # Migration files
├── pyproject.toml        # Poetry dependencies
├── alembic.ini           # Alembic configuration
└── pytest.ini            # Pytest configuration
```

## 🧪 Testing

```bash
# Run all tests with coverage
pytest

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m contract      # Contract tests (API validation)

# Run with verbose output
pytest -v

# Generate coverage report
pytest --cov=app --cov-report=html
```

## 🔧 Development

### Code Quality

```bash
# Lint with Ruff
ruff check .

# Format with Black
black .

# Type check with mypy
mypy app --strict --ignore-missing-imports

# Run all checks
pre-commit run --all-files
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## 🔐 Environment Variables

See `.env.example` for all required environment variables.

**Critical settings**:
- `JWT_SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SUPER_ADMIN_EMAIL` / `SUPER_ADMIN_PASSWORD`: Initial admin credentials

## 📚 API Documentation

Interactive API documentation is automatically generated:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+ (async)
- **Database**: PostgreSQL 15+ with Row-Level Security
- **Cache**: Redis 7+
- **Validation**: Pydantic 2.x
- **Authentication**: OAuth2 + JWT (python-jose)
- **Password Hashing**: bcrypt (passlib)
- **Migrations**: Alembic
- **Testing**: pytest, factory_boy
- **Linting**: Ruff, Black, mypy

## 📖 Documentation

For detailed documentation, see:
- [Quickstart Guide](../.specify/specs/001-user-authentication-role/quickstart.md)
- [API Contracts](../.specify/specs/001-user-authentication-role/contracts/)
- [Data Model](../.specify/specs/001-user-authentication-role/data-model.md)
- [Implementation Plan](../.specify/specs/001-user-authentication-role/plan.md)

## 🤝 Contributing

1. Create a feature branch from `develop`
2. Write tests first (TDD)
3. Implement feature
4. Run code quality checks
5. Submit PR for review

## 📄 License

See [LICENSE](../LICENSE) file.
