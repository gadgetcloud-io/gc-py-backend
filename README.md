# gc-py-backend

**GadgetCloud Unified Backend** - FastAPI application with JWT authentication and Firestore integration.

## Overview

Single backend service serving all API endpoints with production-ready authentication. Provides a unified REST API for device management, repair booking, and user authentication.

## Architecture

```
┌─────────────────────────────────────┐
│  FastAPI Application                │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │     Auth     │  │  REST APIs  │ │
│  │  /api/auth/* │  │  /api/*     │ │
│  └──────────────┘  └─────────────┘ │
│           │              │          │
│           └──────┬───────┘          │
│                  │                  │
│         ┌────────▼────────┐         │
│         │   Firestore     │         │
│         │   - gc-users    │         │
│         │   - gc-items    │         │
│         │   - gc-repairs  │         │
│         └─────────────────┘         │
└─────────────────────────────────────┘
```

## Features

### Authentication
- **JWT-based authentication** with Secret Manager integration
- **User registration** with bcrypt password hashing
- **User login** with email/password
- **Profile management** (view, update)
- **Password change** functionality
- **Role-based access control** (customer, partner, support, admin)

### REST APIs
- **Items API**: `/api/items/*` - Device/gadget CRUD operations
- **Repairs API**: `/api/repairs/*` - Repair booking management
- **Chat API**: `/api/chat/*` - Disabled (AI features removed)

### Security Features
- Password hashing with bcrypt (10 rounds)
- JWT tokens (24-hour expiration)
- Secret Manager integration for JWT signing key
- Protected routes with Bearer token authentication
- Role-based access control

## Local Development

### Prerequisites
- Python 3.11+
- GCP Project (for Firestore/Storage/Secret Manager)
- JWT signing key in Secret Manager or environment variable

### Setup

```bash
# Clone repository
git clone https://github.com/gadgetcloud-io/gc-py-backend.git
cd gc-py-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (for local development)
export JWT_SECRET_KEY="dev-secret-key-change-in-production"
export GCP_PROJECT="gadgetcloud-prd"
export ENVIRONMENT="development"

# Run locally
uvicorn app.main:app --reload --port 8000
```

### Access API Documentation

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Utility Scripts

Located in `scripts/` directory:

```bash
# Check Firestore data
python scripts/check_firestore.py                    # All collections (uses .env config)
python scripts/check_firestore.py --collection users # Specific collection (shorthand)
python scripts/check_firestore.py --project stg      # Override project

# Supported shorthands:
# Projects: prd, stg, prod, staging, production
# Collections: users, items, repairs, config
```

Located in parent `../scripts/` directory (cross-repository scripts):

```bash
# Start local development (backend + frontend)
bash ../scripts/start-local.sh

# Stop local development
bash ../scripts/stop-local.sh

# Health check
bash ../scripts/health-check.sh

# Clean database
bash ../scripts/cleanup-database.sh local              # Clean all collections
bash ../scripts/cleanup-database.sh local gc-users     # Clean specific collection
bash ../scripts/cleanup-database.sh stg                # Clean staging database
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ENVIRONMENT` | Environment name (development, production) | No | development |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, ERROR) | No | INFO |
| `JWT_SECRET_KEY` | Secret key for JWT signing (fallback) | No | dev-secret-key-change-in-production |
| `GCP_PROJECT` | GCP project ID | Yes | gadgetcloud-prd |
| `FIRESTORE_DATABASE` | Firestore database name | No | (default) |

**Note**: JWT secret is loaded from Secret Manager (`jwt-signing-key`) in production. Environment variable is only used as fallback for local development.

## API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /readiness` - Readiness check with dependency status
- `GET /` - Service info

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/signup` - User registration
- `POST /api/auth/logout` - Logout (audit logging)
- `GET /api/auth/me` - Get current user profile
- `PUT /api/auth/me` - Update user profile
- `POST /api/auth/change-password` - Change password

### Items
- `GET /api/items` - List all items (requires auth)
- `GET /api/items/{id}` - Get item by ID (requires auth)
- `POST /api/items` - Create new item (requires auth)
- `PUT /api/items/{id}` - Update item (requires auth)
- `DELETE /api/items/{id}` - Delete item (requires auth)

### Repairs
- `GET /api/repairs` - List repair bookings (requires auth)
- `POST /api/repairs` - Create repair booking (requires auth)
- `PUT /api/repairs/{id}` - Update repair status (requires auth)
- `DELETE /api/repairs/{id}` - Cancel repair (requires auth)

### Chat (Disabled)
- `POST /api/chat/query` - Returns "AI features disabled" message
- `GET /api/chat/capabilities` - Returns empty capabilities

## Authentication Flow

### User Registration
```bash
POST /api/auth/signup
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "abc123",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "customer",
    "status": "active"
  }
}
```

### User Login
```bash
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": { ... }
}
```

### Using Protected Endpoints
```bash
GET /api/items
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

Response:
[
  {
    "id": "item1",
    "name": "iPhone 13",
    "brand": "Apple",
    "category": "phone",
    "status": "active"
  }
]
```

## Deployment

### Build Docker Image
```bash
docker build -t gcr.io/gadgetcloud-prd/gc-py-backend:latest .
```

### Push to Artifact Registry
```bash
docker push gcr.io/gadgetcloud-prd/gc-py-backend:latest
```

### Deploy to Cloud Run
```bash
gcloud run deploy gc-py-backend \
  --image gcr.io/gadgetcloud-prd/gc-py-backend:latest \
  --region asia-south1 \
  --project gadgetcloud-prd \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT=gadgetcloud-prd,ENVIRONMENT=production \
  --min-instances 1 \
  --max-instances 100 \
  --memory 512Mi \
  --cpu 1
```

## Project Structure

```
gc-py-backend/
├── app/
│   ├── core/
│   │   ├── config.py           # Configuration with Secret Manager
│   │   ├── security.py         # JWT and password utilities
│   │   └── logging_config.py   # Logging setup
│   ├── routers/
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── items.py            # Items CRUD
│   │   ├── repairs.py          # Repairs management
│   │   ├── chat.py             # Chat (disabled)
│   │   └── health.py           # Health checks
│   ├── services/
│   │   └── user_service.py     # Firestore user management
│   ├── agents/                 # Legacy (AI removed)
│   └── main.py                 # FastAPI app
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container image
└── README.md                   # This file
```

## Firestore Collections

### gc-users
```json
{
  "id": "auto-generated",
  "email": "user@example.com",
  "passwordHash": "bcrypt-hashed-password",
  "name": "John Doe",
  "role": "customer",
  "status": "active",
  "createdAt": "2025-01-01T00:00:00Z",
  "updatedAt": "2025-01-01T00:00:00Z"
}
```

**Indexes:**
- email ASC, status ASC

### gc-items
```json
{
  "id": "auto-generated",
  "userId": "user-id-reference",
  "name": "iPhone 13",
  "brand": "Apple",
  "category": "phone",
  "status": "active",
  "purchaseDate": "2024-01-01T00:00:00Z",
  "warrantyExpiry": "2025-01-01T00:00:00Z",
  "serialNumber": "ABC123",
  "createdAt": "2024-12-01T00:00:00Z",
  "updatedAt": "2024-12-01T00:00:00Z"
}
```

**Indexes:**
- userId ASC, createdAt DESC
- category ASC, status ASC, updatedAt DESC

### gc-repairs
```json
{
  "id": "auto-generated",
  "itemId": "item-id-reference",
  "userId": "user-id-reference",
  "issueDescription": "Cracked screen",
  "status": "pending",
  "estimatedCost": 150.00,
  "actualCost": null,
  "scheduledDate": "2025-01-15T10:00:00Z",
  "completedDate": null,
  "createdAt": "2025-01-10T00:00:00Z",
  "updatedAt": "2025-01-10T00:00:00Z"
}
```

**Indexes:**
- userId ASC, status ASC, createdAt DESC
- itemId ASC, createdAt DESC

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Lint
ruff check .

# Type checking
mypy .
```

## Security Considerations

### Production Checklist
- ✅ JWT secrets loaded from Secret Manager
- ✅ Passwords hashed with bcrypt
- ✅ HTTPS enforced (Cloud Run)
- ✅ CORS configured for known origins
- ⚠️ Rate limiting (TODO)
- ⚠️ Request validation (Pydantic - partial)
- ⚠️ SQL injection prevention (N/A - using Firestore)

### Security Best Practices
1. Never commit secrets to git
2. Use Secret Manager for sensitive data
3. Enable Cloud Run authentication for internal services
4. Implement rate limiting for public endpoints
5. Regular security audits
6. Keep dependencies updated

## Migration from Microservices

This unified backend replaces the following deprecated microservices:
- ❌ gc-py-proxy (API gateway)
- ❌ gc-py-authorizer (Auth service)
- ❌ gc-py-items (Items service)
- ❌ gc-py-common-config (Config service)

Benefits of unified architecture:
- Simpler deployment (1 service vs 4)
- Lower costs (~$150-300/month savings)
- Easier debugging
- Faster development
- Single source of truth

## Support

- **Repository**: https://github.com/gadgetcloud-io/gc-py-backend
- **Documentation**: See architecture.md in gc-tf-gcp-infra
- **Issues**: Create GitHub issue for bugs or feature requests

## License

Proprietary - GadgetCloud Platform
