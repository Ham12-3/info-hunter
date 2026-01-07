# Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available for Docker

## Step-by-Step Setup

### 1. Start All Services

```bash
# Start services (this will take a few minutes the first time)
docker-compose up -d

# Wait for services to be healthy, then check status
docker-compose ps
```

All services should show "Up" status. If any service is not running, check logs:

```bash
docker-compose logs <service-name>
```

### 2. Verify Services Are Running

```bash
# Check backend health
curl http://localhost:8000/health

# Should return: {"status":"healthy","service":"info-hunter-api","version":"1.0.0"}
```

### 3. Initialize Database

```bash
# Generate migration (this will detect the new AI columns)
docker-compose exec backend alembic revision --autogenerate -m "Initial migration with AI support"

# Apply migration
docker-compose exec backend alembic upgrade head
```

### 4. Create Elasticsearch Index

```bash
docker-compose exec backend python scripts/create_index.py
```

### 5. Rebuild Backend Container (Ensures All Dependencies Installed)

The AI dependencies (openai, anthropic) are already in `requirements.txt` and will be automatically installed during the Docker build. To ensure everything is up to date:

```bash
# Rebuild backend container (installs all dependencies from requirements.txt)
docker-compose build backend

# Restart backend service
docker-compose up -d backend
```

**Note**: The Dockerfile runs as a non-root user to avoid pip warnings. All dependencies are installed to the user's local directory.

### 6. (Optional) Configure AI Features

Create `backend/.env` file:

```env
# AI Configuration (optional but recommended)
OPENAI_API_KEY=sk-your-key-here
AI_PROVIDER=openai
```

Without AI keys, the app will work but AI features will be disabled.

### 7. Ingest Some Data

```bash
# Ingest from GitHub
curl -X POST "http://localhost:8000/admin/ingest/run?source=github&topics=python&max_repos=5"

# Ingest from Stack Exchange
curl -X POST "http://localhost:8000/admin/ingest/run?source=stackexchange&tags=python&max_items=10"
```

### 8. (Optional) Run AI Enrichment

```bash
# Enrich items with AI metadata
curl -X POST "http://localhost:8000/admin/ai/enrich?limit=10"

# Generate embeddings for semantic search
curl -X POST "http://localhost:8000/admin/ai/embed?limit=10"
```

### 9. Access the Application

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Backend Service Not Running

```bash
# Check backend logs
docker-compose logs backend

# Common issues:
# - Database not ready: wait a bit longer for postgres to start
# - Port already in use: stop other services using ports 8000, 5432, 6379, 9200, 3000
```

### Database Connection Errors

```bash
# Check postgres is running
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### Elasticsearch Errors

```bash
# Check Elasticsearch logs
docker-compose logs elasticsearch

# Common issue: Out of memory
# Solution: Increase Docker memory limit or reduce ES heap size in docker-compose.yml
```

## Common Commands

```bash
# View all logs
docker-compose logs -f

# Restart a specific service
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove volumes (clears all data)
docker-compose down -v

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend
```

