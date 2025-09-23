# Users Microservice Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Application Layer](#application-layer)
5. [Database Layer](#database-layer)
6. [Containerization](#containerization)
7. [Kubernetes Configuration](#kubernetes-configuration)
8. [Development Workflow](#development-workflow)
9. [API Endpoints](#api-endpoints)
10. [Best Practices Demonstrated](#best-practices-demonstrated)

## Overview

This is a modern FastAPI-based microservice that demonstrates production-ready practices for building, containerizing, and deploying applications on Kubernetes. The service provides user management functionality with PostgreSQL persistence.

### Key Technologies
- **FastAPI**: Modern, fast Python web framework
- **SQLAlchemy 2.0**: Modern Python SQL toolkit with async support
- **PostgreSQL**: Production-ready relational database
- **Docker**: Containerization platform
- **Kubernetes**: Container orchestration
- **Skaffold**: Development workflow tool

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/REST API + JWT Authentication
┌─────────────────────▼───────────────────────────────────────┐
│                  Load Balancer                             │
│                 (Kubernetes Service)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Users API Pod                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              FastAPI Application                    │   │
│  │  ┌─────────────┬─────────────┬─────────────────┐   │   │
│  │  │   Auth      │   Users     │    Profile      │   │   │
│  │  │ (JWT/Login) │ (CRUD Ops)  │ (Profile Mgmt)  │   │   │
│  │  └─────────────┴─────────────┴─────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │     Models, Schemas & Validation Layer         │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │           Database Connection Pool              │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┐   │
└─────────────────────┬───────────────────────────────────────┘
                      │ SQL Connection
┌─────────────────────▼───────────────────────────────────────┐
│                PostgreSQL StatefulSet                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 Database                            │   │
│  │         ┌─────────────────────────────┐             │   │
│  │         │        users table          │             │   │
│  │         │  - id (PK)                  │             │   │
│  │         │  - email (unique)           │             │   │
│  │         │  - name                     │             │   │
│  │         │  - hashed_password          │             │   │
│  │         │  - is_active                │             │   │
│  │         │  - is_superuser             │             │   │
│  │         │  - bio                      │             │   │
│  │         │  - avatar_url               │             │   │
│  │         │  - location                 │             │   │
│  │         │  - website                  │             │   │
│  │         │  - phone                    │             │   │
│  │         │  - preferences (JSON)       │             │   │
│  │         │  - created_at               │             │   │
│  │         │  - updated_at               │             │   │
│  │         └─────────────────────────────┘             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
users/
├── app/                          # Application source code
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI application entry point
│   ├── auth.py                  # Authentication utilities (JWT, password hashing)
│   ├── db.py                    # Database configuration and sessions
│   ├── models.py                # SQLAlchemy database models
│   ├── schemas.py               # Pydantic data validation schemas
│   └── routers/                 # API route handlers
│       ├── __init__.py
│       ├── auth.py             # Authentication endpoints (login, register)
│       ├── users.py            # User management endpoints (admin)
│       └── profile.py          # User profile management endpoints
├── k8s/                         # Kubernetes manifests
│   ├── app-db.secret.yaml      # Database credentials and JWT secret
│   ├── postgres.service.yaml   # PostgreSQL service discovery
│   ├── postgres.statefulset.yaml # PostgreSQL deployment
│   ├── users-api.deployment.yaml # Application deployment
│   └── users-api.service.yaml  # Application service discovery
├── Dockerfile                   # Container image definition
├── .dockerignore               # Files to exclude from Docker build
├── requirements.txt            # Python dependencies
├── skaffold.yaml              # Development workflow configuration
├── demo_api.py                # Comprehensive API demonstration script
└── docs.md                    # This documentation file
```

## Application Layer

### 1. FastAPI Application (`app/main.py`)

The main application file demonstrates modern Python async patterns and proper application lifecycle management:

```python
from fastapi import FastAPI, HTTPException, Depends
import os
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .db import engine, Base, get_session
from .routers import users as users_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables at startup (we'll switch to Alembic migrations later)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="Users API", version="0.2.0", lifespan=lifespan)
```

**Key Learning Points:**
- **Lifespan Management**: The `lifespan` context manager handles startup and shutdown events
- **Async Context Manager**: Proper resource management using `async with`
- **Database Initialization**: Tables are created automatically on startup
- **Clean Shutdown**: Database connections are properly disposed of

### 2. Health Check Endpoints

Essential for Kubernetes deployments:

```python
@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.get("/readyz")
async def ready():
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="db not ready")
```

**Why This Matters:**
- **Liveness Probe** (`/healthz`): Kubernetes uses this to determine if the pod is alive
- **Readiness Probe** (`/readyz`): Kubernetes uses this to determine if the pod can accept traffic
- **Database Connectivity**: Readiness check verifies database connection

### 3. Modular Router System (`app/routers/users.py`)

FastAPI's router system promotes clean, modular code:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db_session
from .. import models
from ..schemas import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=list[UserRead])
async def list_users(session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(models.User).order_by(models.User.id))
    return [UserRead.model_validate(u) for u in res.scalars().all()]
```

**Architecture Benefits:**
- **Separation of Concerns**: Each router handles a specific domain
- **Dependency Injection**: Database sessions are injected automatically
- **Type Safety**: Response models ensure consistent API contracts

## Database Layer

### 1. Database Configuration (`app/db.py`)

Modern async SQLAlchemy setup with proper connection management:

```python
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://appuser:apppass@postgres:5432/appdb",
)

class Base(DeclarativeBase):
    pass

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
```

**Key Features:**
- **Environment Configuration**: Database URL from environment variables
- **Connection Pooling**: Built-in connection pool with health checks
- **Async Support**: Full async/await support for better performance

### 2. Database Models (`app/models.py`)

Modern SQLAlchemy 2.0 syntax with type hints:

```python
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class User(Base):
    __tablename__ = "users"

    # Basic user information
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Extended profile fields
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # User preferences stored as JSON
    preferences: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    
    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
```

**Modern Patterns:**
- **Type Annotations**: `Mapped[]` provides better IDE support and type checking
- **Timezone Awareness**: Proper UTC timestamp handling
- **Database Constraints**: Unique constraints and indexes for performance

### 3. Data Validation (`app/schemas.py`)

Pydantic schemas for request/response validation:

```python
from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    name: str | None = None

class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
```

**Benefits:**
- **Automatic Validation**: Email format validation, type checking
- **API Documentation**: Schemas generate OpenAPI documentation
- **Serialization**: Automatic conversion between database models and JSON

## Containerization

### Multi-Stage Dockerfile

Our Dockerfile demonstrates production best practices:

```dockerfile
# syntax=docker/dockerfile:1.7

# --- builder stage ---
FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /workspace
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN python -m venv /venv && /venv/bin/pip install --no-cache-dir \
    -r requirements.txt

# --- runtime stage ---
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH" \
    PORT=8000 \
    APP_ENV=dev \
    PYTHONPATH="/app"
WORKDIR /app
# Create non-root user
RUN useradd -u 10001 -s /usr/sbin/nologin appuser && \
    mkdir -p /app && chown -R appuser:appuser /app
COPY --from=builder /venv /venv
COPY . /app
RUN python -c "import os, sys, importlib; print('sys.path=', sys.path); \
    importlib.import_module('app'); \
    print(\"Imported 'app' OK, contents:\", os.listdir('/app/app'))"
USER 10001:10001

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Security & Performance Features:**
- **Multi-stage Build**: Smaller final image, build tools not included in runtime
- **Non-root User**: Security best practice, runs with limited privileges
- **Layer Optimization**: Dependencies installed separately for better caching
- **Import Verification**: Ensures the application can be imported successfully

## Kubernetes Configuration

### 1. Database Secret (`k8s/app-db.secret.yaml`)

Secure credential management:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-db-secret
type: Opaque
stringData:
  POSTGRES_USER: appuser
  POSTGRES_PASSWORD: apppass
  POSTGRES_DB: appdb
  DATABASE_URL: postgresql+asyncpg://appuser:apppass@postgres:5432/appdb
```

**Security Notes:**
- In production, use external secret management (e.g., Vault, AWS Secrets Manager)
- Never commit real secrets to version control
- Use `stringData` for base64 encoding automation

### 2. PostgreSQL StatefulSet (`k8s/postgres.statefulset.yaml`)

Stateful database deployment:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 1
  template:
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          envFrom:
            - secretRef:
                name: app-db-secret
          volumeMounts:
            - name: pgdata
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: pgdata
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 1Gi
```

**StatefulSet Benefits:**
- **Persistent Storage**: Data survives pod restarts
- **Stable Network Identity**: Consistent hostname for database connections
- **Ordered Deployment**: Ensures proper startup sequence

### 3. Application Deployment (`k8s/users-api.deployment.yaml`)

Stateless application deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: users-api
spec:
  replicas: 1
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
      containers:
        - name: users-api
          image: users-api
          ports:
            - containerPort: 8000
              name: http
          envFrom:
            - secretRef:
                name: app-db-secret
          readinessProbe:
            httpGet:
              path: /readyz
              port: http
            initialDelaySeconds: 3
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "250m"
              memory: "128Mi"
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
```

**Production Features:**
- **Security Context**: Non-root user, read-only filesystem
- **Health Probes**: Automatic health monitoring
- **Resource Limits**: Prevents resource exhaustion
- **Environment Injection**: Configuration via secrets

### 4. Service Discovery (`k8s/users-api.service.yaml`)

Network abstraction layer:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: users-api
spec:
  type: ClusterIP
  selector:
    app: users-api
  ports:
    - name: http
      port: 8000
      targetPort: http
```

**Service Benefits:**
- **Load Balancing**: Automatic traffic distribution
- **Service Discovery**: Stable DNS name for the application
- **Port Abstraction**: Decouples external and internal ports

## Development Workflow

### Skaffold Configuration (`skaffold.yaml`)

Development workflow automation:

```yaml
apiVersion: skaffold/v4beta11
kind: Config
metadata:
  name: users-api
build:
  local:
    push: false
  artifacts:
    - image: users-api
      context: .
      docker:
        dockerfile: Dockerfile
deploy:
  kubectl:
    manifests:
      - k8s/*.yaml
portForward:
  - resourceType: service
    resourceName: users-api
    port: 8000
    localPort: 8000
```

**Workflow Features:**
- **Hot Reload**: Automatic rebuilds on code changes
- **Local Development**: No need to push to remote registries
- **Port Forwarding**: Easy access to services running in cluster

### Development Commands

```bash
# Start development environment
cd users/
skaffold dev --port-forward

# The above command will:
# 1. Build the Docker image
# 2. Deploy to Kubernetes
# 3. Set up port forwarding
# 4. Watch for file changes
# 5. Automatically rebuild and redeploy on changes
```

## API Endpoints

### Available Endpoints

1. **Health Check**
   ```
   GET / - Basic service information
   GET /healthz - Liveness probe
   GET /readyz - Readiness probe (includes DB check)
   ```

2. **Authentication**
   ```
   POST /auth/register - Register a new user
   POST /auth/login - Login and get access token
   GET /auth/me - Get current user information
   POST /auth/test-token - Test access token validity
   ```

3. **User Management (Admin only)**
   ```
   GET /users - List all users (superuser only)
   GET /users/me - Get current user profile
   PUT /users/me - Update current user profile
   GET /users/{user_id} - Get specific user (superuser only)
   PUT /users/{user_id} - Update specific user (superuser only)
   DELETE /users/{user_id} - Delete user (superuser only)
   ```

4. **Profile Management**
   ```
   GET /profile/me - Get current user's complete profile
   PUT /profile/me - Update current user's profile information
   GET /profile/me/preferences - Get current user's preferences
   PUT /profile/me/preferences - Update current user's preferences
   DELETE /profile/me/avatar - Remove current user's avatar
   GET /profile/{user_id} - Get another user's public profile
   ```

### Usage Examples

#### Authentication Flow
```bash
# Register a new user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "name": "Alice Johnson",
    "password": "secretpassword123"
  }'

# Login to get access token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice@example.com&password=secretpassword123"

# Use the returned access_token in subsequent requests
export TOKEN="your_access_token_here"

# Get current user info
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/auth/me
```

#### Profile Management
```bash
# Get current user's profile
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/profile/me

# Update profile information
curl -X PUT http://localhost:8000/profile/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "I am a software developer passionate about microservices!",
    "location": "San Francisco, CA",
    "website": "https://alice-dev.com",
    "phone": "+1-555-0123"
  }'

# Update user preferences
curl -X PUT http://localhost:8000/profile/me/preferences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "dark",
    "language": "en",
    "timezone": "America/Los_Angeles",
    "notifications_email": true,
    "notifications_sms": false,
    "privacy_public_profile": true
  }'

# Get user preferences
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/profile/me/preferences
```

#### Testing Script
You can also run our comprehensive demo script:
```bash
# Install required dependencies
pip install aiohttp

# Run the demo script
cd /home/super/Documents/QuizAppFull/users
python demo_api.py
```

### API Documentation

FastAPI automatically generates interactive documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Best Practices Demonstrated

### 1. **Security**
- Non-root container execution
- Read-only root filesystem
- Secrets management
- Input validation with Pydantic

### 2. **Reliability**
- Health checks for proper orchestration
- Graceful shutdown handling
- Connection pooling with health checks
- Resource limits and requests

### 3. **Observability**
- Structured logging (uvicorn logs)
- Health endpoints for monitoring
- Clear error messages and HTTP status codes

### 4. **Scalability**
- Stateless application design
- Async/await for better concurrency
- Connection pooling for database efficiency
- Horizontal scaling ready (can increase replicas)

### 5. **Maintainability**
- Modular code structure
- Type hints throughout
- Clear separation of concerns
- Comprehensive documentation

### 6. **Development Experience**
- Hot reload with Skaffold
- Automatic API documentation
- Local development on Kubernetes
- Easy testing with curl/HTTPie

## Next Steps

This foundation supports adding:

1. **Authentication & Authorization**
   - JWT tokens
   - Role-based access control
   - OAuth2 integration

2. **Advanced Database Features**
   - Database migrations with Alembic
   - Advanced queries and relationships
   - Database indexing strategies

3. **Production Readiness**
   - Monitoring with Prometheus
   - Logging aggregation
   - Distributed tracing
   - Circuit breakers

4. **Testing**
   - Unit tests with pytest
   - Integration tests
   - Load testing
   - Contract testing

This microservice demonstrates a solid foundation for building production-ready applications on Kubernetes while following modern development practices.
