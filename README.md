# gc-py-backend

**GadgetCloud Unified Backend** - FastAPI application with built-in AI agent layer.

## Overview

Single backend service serving all API endpoints with integrated Claude AI agent orchestration. Replaces the traditional microservices architecture with a simpler, agent-first approach.

## Architecture

```
┌─────────────────────────────────────┐
│  FastAPI Application                │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │  REST APIs   │  │ Agent Layer │ │
│  │  /api/*      │  │ /api/chat   │ │
│  └──────────────┘  └─────────────┘ │
│           │              │          │
│           └──────┬───────┘          │
│                  │                  │
│         ┌────────▼────────┐         │
│         │  Tool Executor  │         │
│         │  - Firestore    │         │
│         │  - Storage      │         │
│         │  - Services     │         │
│         └─────────────────┘         │
└─────────────────────────────────────┘
```

## Features

### Traditional REST APIs
- **Authentication**: `/api/auth/*` - JWT-based auth
- **Items**: `/api/items/*` - Device/gadget CRUD
- **Repairs**: `/api/repairs/*` - Repair booking management

### AI-Powered Features
- **Chat Interface**: `/api/chat/query` - Natural language queries
- **Tool Execution**: Agents can call Firestore, Storage, external APIs
- **Context Awareness**: Maintains conversation context

### Agent Capabilities
- Search devices: "Show me my iPhone"
- Book repairs: "Schedule a screen repair for tomorrow"
- Check status: "What's the status of my repair?"
- Recommendations: "Which device needs warranty renewal?"

## Local Development

### Prerequisites
- Python 3.11+
- GCP Project (for Firestore/Storage)
- Anthropic API Key (for AI features)

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

# Set environment variables
export JWT_SECRET_KEY="your-secret-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export GCP_PROJECT="gadgetcloud-prd"

# Run locally
uvicorn app.main:app --reload --port 8080
```

### Access API Documentation

- **Swagger UI**: http://localhost:8080/api/docs
- **ReDoc**: http://localhost:8080/api/redoc

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ENVIRONMENT` | Environment name (development, production) | No |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, ERROR) | No |
| `JWT_SECRET_KEY` | Secret key for JWT signing | Yes |
| `ANTHROPIC_API_KEY` | Claude API key | Yes (for AI features) |
| `GCP_PROJECT` | GCP project ID | Yes |

## API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /readiness` - Readiness check
- `GET /` - Service info

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/signup` - User signup
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user

### Items (Devices)
- `GET /api/items` - List items
- `GET /api/items/{id}` - Get item details
- `POST /api/items` - Create item
- `PUT /api/items/{id}` - Update item
- `DELETE /api/items/{id}` - Delete item

### Repairs
- `GET /api/repairs` - List repair bookings
- `GET /api/repairs/{id}` - Get repair details
- `POST /api/repairs` - Create repair booking

### AI Chat
- `POST /api/chat/query` - Natural language query
- `GET /api/chat/capabilities` - Get agent capabilities

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_agents.py
```

## Deployment

### Build Docker Image

```bash
# Build
docker build -t gc-py-backend .

# Run locally
docker run -p 8080:8080 \
  -e JWT_SECRET_KEY="your-secret" \
  -e ANTHROPIC_API_KEY="your-key" \
  gc-py-backend
```

### Deploy to Cloud Run

```bash
# Build and push to Artifact Registry
gcloud builds submit --tag asia-south1-docker.pkg.dev/gadgetcloud-prd/gadgetcloud-docker/gc-py-backend:latest

# Deploy to Cloud Run (done via terraform)
cd ../gc-tf-gcp-infra/environments/prd
terraform apply
```

## Project Structure

```
gc-py-backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── routers/                # API endpoint routers
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── items.py            # Items CRUD
│   │   ├── repairs.py          # Repairs management
│   │   ├── chat.py             # AI chat interface
│   │   └── health.py           # Health checks
│   ├── agents/                 # Agent layer
│   │   ├── orchestrator.py     # Main agent orchestrator
│   │   └── tools.py            # Agent tool definitions
│   ├── models/                 # Pydantic models
│   ├── services/               # Business logic
│   └── core/                   # Core configuration
│       ├── config.py           # Settings
│       └── logging_config.py   # Logging setup
├── tests/                      # Test files
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container image definition
└── README.md                   # This file
```

## Agent Development

### Adding New Tools

1. Define tool in `app/agents/tools.py`:
```python
{
    "name": "my_new_tool",
    "description": "What this tool does",
    "input_schema": {
        "type": "object",
        "properties": {
            "param": {"type": "string"}
        }
    }
}
```

2. Implement tool function:
```python
async def _my_new_tool(input: Dict, user_id: str) -> Dict:
    # Tool implementation
    return {"result": "success"}
```

3. Add to `execute_tool()` routing

### Testing Agent Locally

```bash
# Start server
uvicorn app.main:app --reload

# Test chat endpoint
curl -X POST http://localhost:8080/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me my devices"
  }'
```

## Performance

- **Cold Start**: ~2-3 seconds (with min_instances=0)
- **Warm Response**: ~200-500ms (REST APIs)
- **AI Response**: ~2-5 seconds (agent with tool use)
- **Concurrency**: 100 requests/instance

## Cost Estimates

### Production
- Always-on (min_instances=1): ~$30-80/month
- Scale-to-zero (min_instances=0): ~$10-30/month
- Claude API costs: ~$10-50/month (depends on usage)

### Staging
- Scale-to-zero: ~$5-15/month
- Claude API: ~$5-10/month

## Security

- JWT authentication on all endpoints
- Service account for GCP resources
- Secrets stored in Secret Manager
- CORS configured for app domains
- Rate limiting enabled
- Input validation with Pydantic

## Monitoring

- Cloud Logging integration
- Structured logging with correlation IDs
- Health check endpoints for uptime monitoring
- Error tracking and alerting

## Contributing

1. Create feature branch
2. Make changes
3. Add tests
4. Run `pytest` and `ruff check .`
5. Create pull request

## License

Proprietary - GadgetCloud Platform

## Support

For issues or questions, contact the platform team.
