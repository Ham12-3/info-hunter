# Info Hunter

Info Hunter is a full-stack application that aggregates and searches programming knowledge and code snippets from various sources including GitHub, Stack Overflow, and RSS feeds. It provides fast search capabilities powered by Elasticsearch and a modern web interface built with Next.js.

## Features

- **Multi-source aggregation**: Collects programming information from:
  - GitHub repositories (README files)
  - Stack Exchange Q&A sites (Stack Overflow, etc.)
  - RSS feeds from programming blogs
- **Smart code extraction**: Extracts code blocks and surrounding context from Markdown and HTML
- **Fast search**: Elasticsearch-powered search with filters for source type, language, framework, and tags
  - **Keyword search**: Traditional full-text search
  - **Semantic search**: Vector-based similarity search using AI embeddings
  - **Hybrid search**: Combines keyword and semantic search for best results
- **AI-powered enrichment**: Automatically generates summaries, tags, and quality scores
- **Ask feature**: Get AI-generated answers to questions with citations
- **Deduplication**: Automatic deduplication and change detection to avoid storing duplicates
- **Saved searches**: Save search queries and receive alerts on new matches
- **Attribution**: Always stores source URL, author, and license information

## Architecture

### Backend
- **FastAPI**: RESTful API with async support
- **PostgreSQL**: Canonical storage for knowledge items and saved searches
- **Elasticsearch 8.x**: Full-text search and filtering
- **Celery + Redis**: Background job processing for ingestion
- **SQLAlchemy + Alembic**: Database ORM and migrations

### Frontend
- **Next.js 14** (App Router): Modern React framework
- **Tailwind CSS**: Utility-first CSS framework
- **TypeScript**: Type-safe development

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local frontend development)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd info-hunter
```

### 2. Start Services with Docker Compose

```bash
# Start all services in detached mode
docker-compose up -d

# Check if services are running
docker-compose ps

# View logs if there are issues
docker-compose logs backend
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Elasticsearch (port 9200)
- Backend API (port 8000)
- Celery worker
- Celery beat (scheduler)
- Frontend (port 3000)

**Note**: The first startup may take a few minutes as Docker downloads images and builds containers. Wait until all services show as "Up" before proceeding.

### 3. Initialize Database

```bash
# Create database migrations
docker-compose exec backend alembic revision --autogenerate -m "Initial migration"

# Run migrations
docker-compose exec backend alembic upgrade head
```

### 4. Create Elasticsearch Index

```bash
docker-compose exec backend python scripts/create_index.py
```

### 5. Run Initial Ingestion (Optional)

Ingest some data to get started:

```bash
# Ingest from GitHub
curl -X POST "http://localhost:8000/admin/ingest/run?source=github&topics=python,javascript&max_repos=10"

# Ingest from Stack Exchange
curl -X POST "http://localhost:8000/admin/ingest/run?source=stackexchange&tags=python,javascript&max_items=20"

# Ingest from RSS feeds
curl -X POST "http://localhost:8000/admin/ingest/run?source=rss&max_items_per_feed=10"
```

### 6. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Elasticsearch**: http://localhost:9200

## Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```env
DATABASE_URL=postgresql://infohunter:infohunter_dev@postgres:5432/infohunter_db
REDIS_URL=redis://redis:6379/0
ELASTICSEARCH_URL=http://elasticsearch:9200
ENVIRONMENT=development

# Optional: For higher API rate limits
GITHUB_TOKEN=your_github_token_here
STACKEXCHANGE_KEY=your_stackexchange_key_here
```

### RSS Feed Configuration

Edit `backend/feeds.yaml` to add or remove RSS feeds:

```yaml
feeds:
  - url: https://realpython.com/atom.xml
    name: Real Python
    enabled: true
  # Add more feeds...
```

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Run the API server
uvicorn app.main:app --reload

# Run Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Run Celery beat
celery -A app.tasks.celery_app beat --loglevel=info

# Run tests
pytest
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## API Endpoints

### Search

```
GET /search?q=query&source_type=github&primary_language=Python&page=1&size=20
GET /search?q=query&semantic=true  # Semantic search
GET /search?q=query&hybrid=true    # Hybrid search (keyword + semantic)
```

### Get Knowledge Item

```
GET /knowledge/{id}
```

### Manual Ingestion

```
POST /admin/ingest/run?source=github&topics=python&max_repos=50
POST /admin/ingest/run?source=stackexchange&tags=python&max_items=50
POST /admin/ingest/run?source=rss&max_items_per_feed=20
```

### Ask (AI Question Answering)

```
POST /ask
Body: {
  "question": "How do I handle async errors in Python?",
  "top_k": 5,
  "semantic": true,
  "filters": {"primary_language": "Python"}
}
```

### AI Admin Endpoints

```
POST /admin/ai/enrich?limit=50  # Enqueue enrichment jobs
POST /admin/ai/embed?limit=50   # Enqueue embedding jobs
```

### Saved Searches

```
GET /saved-searches
POST /saved-searches
POST /alerts/run
```

See the interactive API documentation at http://localhost:8000/docs for full details.

## Example Queries

### Search for Python async code

```
GET /search?q=async await&primary_language=Python
```

### Find React hooks examples from GitHub

```
GET /search?q=useState useEffect&source_type=github&framework=React
```

### Search Stack Overflow for error solutions

```
GET /search?q=ImportError&source_type=stackexchange&primary_language=Python
```

## Scheduled Tasks

Celery Beat runs the following scheduled tasks:

- **GitHub ingestion**: Daily at midnight
- **Stack Exchange ingestion**: Daily at midnight
- **RSS ingestion**: Hourly
- **Saved search alerts**: Daily at 6 AM

## Data Model

### KnowledgeItem

- `id`: UUID primary key
- `source_type`: github, stackexchange, rss, or html
- `source_name`: Human-readable source name
- `source_url`: Canonical URL
- `title`: Item title
- `summary`: Short summary
- `body_text`: Cleaned explanation text
- `code_snippets`: Array of `{language, code, context}` objects
- `tags`: Array of tag strings
- `primary_language`: Detected programming language
- `framework`: Detected framework (optional)
- `author`: Author name (optional)
- `licence`: License identifier (optional)
- `published_at`: Publication date (optional)
- `content_hash`: SHA-256 hash for change detection
- `dedupe_key`: Deterministic key for deduplication

## Testing

Run backend tests:

```bash
cd backend
pytest
```

## Troubleshooting

### Elasticsearch won't start

If Elasticsearch fails to start due to memory limits, you may need to increase Docker memory allocation or adjust the JVM heap size in `docker-compose.yml`.

### Database connection errors

Ensure PostgreSQL is healthy:

```bash
docker-compose ps postgres
docker-compose logs postgres
```

### Celery tasks not running

Check Celery worker and beat logs:

```bash
docker-compose logs celery-worker
docker-compose logs celery-beat
```

## License

This project is provided as-is for educational purposes. Please respect the licenses and terms of service of the sources you're aggregating from.

## Contributing

This is an MVP implementation. Future enhancements could include:

- User authentication and personal saved searches
- Email notifications for saved search alerts
- Advanced search operators
- Code snippet syntax highlighting improvements
- More data sources
- Analytics and usage tracking
