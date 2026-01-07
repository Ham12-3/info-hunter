# Database Migration Notes

## AI Features Migration

After updating the codebase with AI features, you need to create and run a database migration to add the new columns.

### Generate Migration

```bash
docker-compose exec backend alembic revision --autogenerate -m "Add AI enrichment columns"
```

This will create a migration file in `backend/alembic/versions/` that adds:

- `ai_summary` (Text, nullable)
- `ai_tags` (ARRAY(String), nullable)
- `ai_primary_language` (String(100), nullable)
- `ai_framework` (String(100), nullable)
- `ai_quality_score` (Float, nullable)
- `ai_extracted_at` (DateTime(timezone=True), nullable)
- `embedding` (JSON, nullable)

### Apply Migration

```bash
docker-compose exec backend alembic upgrade head
```

### Verify

Check that the columns were added:

```bash
docker-compose exec postgres psql -U infohunter -d infohunter_db -c "\d knowledge_items"
```

You should see the new AI columns listed.

