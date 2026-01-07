"""
Celery tasks for AI enrichment of knowledge items.
"""
import json
import logging
from datetime import datetime
from app.tasks.celery_app import celery_app
from app.db.base import SessionLocal
from app.db.models import KnowledgeItem
from app.ai.provider import get_ai_provider
from app.ai.prompts import get_enrichment_prompt
from app.ai.schemas import KnowledgeItemEnrichment
from app.search.client import get_elasticsearch_client
from app.search.index import INDEX_NAME
from app.ai.rate_limit import openai_rate_limiter, anthropic_rate_limiter
from app.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.enrich.enrich_knowledge_item', bind=True, max_retries=3)
def enrich_knowledge_item(self, item_id: str):
    """
    Enrich a knowledge item with AI-generated metadata.
    
    Args:
        item_id: UUID of the knowledge item to enrich
    """
    db = SessionLocal()
    
    try:
        # Get the item
        item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
        if not item:
            logger.error(f"Knowledge item {item_id} not found")
            return {"status": "error", "message": "Item not found"}
        
        # Check if already enriched recently (optional: skip if enriched in last 24h)
        # if item.ai_extracted_at and (datetime.utcnow() - item.ai_extracted_at).days < 1:
        #     logger.info(f"Item {item_id} already enriched recently, skipping")
        #     return {"status": "skipped", "reason": "Already enriched"}
        
        # Get AI provider
        provider = get_ai_provider()
        if not provider.is_available():
            logger.error("No AI provider configured")
            return {"status": "error", "message": "AI provider not configured"}
        
        # Apply rate limiting
        rate_limiter = openai_rate_limiter if settings.ai_provider.lower() == "openai" else anthropic_rate_limiter
        
        # Build item dict for prompt
        item_dict = {
            'title': item.title,
            'body_text': item.body_text or '',
            'code_snippets': item.code_snippets or []
        }
        
        # Generate prompt
        prompt = get_enrichment_prompt(item_dict)
        
        # Call AI (with retry logic)
        start_time = datetime.utcnow()
        
        try:
            import asyncio
            
            # Create or get event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Rate limit
            if loop.is_running():
                # If loop is already running, we need to use a different approach
                # For Celery, we'll skip rate limiting if loop is running (edge case)
                pass
            else:
                loop.run_until_complete(rate_limiter.acquire())
            
            # Generate enrichment
            response_text = loop.run_until_complete(
                provider.generate_text(prompt, temperature=0.3, max_tokens=2000)
            )
            
            latency = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"AI enrichment completed in {latency:.2f}s for item {item_id}")
            
        except Exception as e:
            logger.error(f"AI API error for item {item_id}: {e}")
            raise self.retry(exc=e, countdown=60)  # Retry after 60s
        
        # Parse and validate JSON
        try:
            # Extract JSON from response (handle markdown code blocks)
            response_text = response_text.strip()
            if response_text.startswith('```'):
                # Remove markdown code blocks
                lines = response_text.split('\n')
                response_text = '\n'.join([l for l in lines if not l.strip().startswith('```')])
            
            enrichment_data = json.loads(response_text)
            enrichment = KnowledgeItemEnrichment(**enrichment_data)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse AI response for item {item_id}: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return {"status": "error", "message": f"Failed to parse AI response: {str(e)}"}
        
        # Update code snippets with enrichment data
        updated_snippets = []
        for idx, snippet in enumerate(item.code_snippets or []):
            snippet_dict = dict(snippet)
            if idx < len(enrichment.code_snippets):
                snippet_enrichment = enrichment.code_snippets[idx]
                snippet_dict['intent'] = snippet_enrichment.intent
                snippet_dict['dependencies'] = snippet_enrichment.dependencies
                snippet_dict['pitfalls'] = snippet_enrichment.pitfalls
            updated_snippets.append(snippet_dict)
        
        # Update item with AI fields
        item.ai_summary = enrichment.summary
        item.ai_tags = enrichment.tags
        item.ai_primary_language = enrichment.primary_language
        item.ai_framework = enrichment.framework
        item.ai_quality_score = enrichment.quality_score
        item.ai_extracted_at = datetime.utcnow()
        item.code_snippets = updated_snippets
        
        db.commit()
        
        # Re-index in Elasticsearch
        try:
            es = get_elasticsearch_client()
            doc = {
                "id": str(item.id),
                "source_type": item.source_type,
                "source_name": item.source_name,
                "source_url": item.source_url,
                "title": item.title,
                "summary": item.summary,
                "ai_summary": item.ai_summary,
                "body_text": item.body_text,
                "code_snippets": item.code_snippets or [],
                "tags": item.tags or [],
                "ai_tags": item.ai_tags or [],
                "primary_language": item.primary_language,
                "ai_primary_language": item.ai_primary_language,
                "framework": item.framework,
                "ai_framework": item.ai_framework,
                "author": item.author,
                "licence": item.licence,
                "published_at": item.published_at.isoformat() if item.published_at else None,
                "found_at": item.found_at.isoformat() if item.found_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            }
            
            es.index(index=INDEX_NAME, id=str(item.id), body=doc)
            logger.info(f"Re-indexed item {item_id} with AI enrichment")
            
        except Exception as e:
            logger.error(f"Error re-indexing item {item_id}: {e}")
        
        return {
            "status": "success",
            "item_id": str(item_id),
            "latency_seconds": latency
        }
        
    except Exception as e:
        logger.error(f"Error enriching item {item_id}: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()

