"""
Celery tasks for generating embeddings for knowledge items.
"""
import logging
from datetime import datetime
from app.tasks.celery_app import celery_app
from app.db.base import SessionLocal
from app.db.models import KnowledgeItem
from app.ai.provider import get_ai_provider
from app.search.client import get_elasticsearch_client
from app.search.index import INDEX_NAME
from app.ai.rate_limit import openai_rate_limiter
from app.config import settings

logger = logging.getLogger(__name__)


def build_embedding_text(item: KnowledgeItem) -> str:
    """
    Build text representation of item for embedding.
    Combines title, summary, body, and code snippets.
    """
    parts = []
    
    if item.title:
        parts.append(f"Title: {item.title}")
    
    if item.ai_summary:
        parts.append(f"Summary: {item.ai_summary}")
    elif item.summary:
        parts.append(f"Summary: {item.summary}")
    
    if item.body_text:
        # Truncate body text to avoid token limits
        body = item.body_text[:2000]
        parts.append(f"Content: {body}")
    
    # Add code snippets (limit to first 3)
    code_snippets = item.code_snippets or []
    for snippet in code_snippets[:3]:
        lang = snippet.get('language', '')
        code = snippet.get('code', '')[:500]  # Truncate long code
        parts.append(f"Code ({lang}): {code}")
    
    return "\n\n".join(parts)


@celery_app.task(name='app.tasks.embed.embed_knowledge_item', bind=True, max_retries=3)
def embed_knowledge_item(self, item_id: str):
    """
    Generate embedding for a knowledge item and store in Elasticsearch.
    
    Args:
        item_id: UUID of the knowledge item to embed
    """
    db = SessionLocal()
    
    try:
        # Get the item
        item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
        if not item:
            logger.error(f"Knowledge item {item_id} not found")
            return {"status": "error", "message": "Item not found"}
        
        # Get AI provider
        provider = get_ai_provider()
        if not provider.is_available():
            logger.error("No AI provider configured")
            return {"status": "error", "message": "AI provider not configured"}
        
        # Build text for embedding
        embedding_text = build_embedding_text(item)
        
        if not embedding_text.strip():
            logger.warning(f"Item {item_id} has no text for embedding")
            return {"status": "skipped", "reason": "No text content"}
        
        # Generate embedding
        start_time = datetime.utcnow()
        
        try:
            import asyncio
            
            # Create or get event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Rate limit (always use OpenAI for embeddings)
            if not loop.is_running():
                loop.run_until_complete(openai_rate_limiter.acquire())
            
            # Generate embedding
            embedding = loop.run_until_complete(provider.generate_embedding(embedding_text))
            
            latency = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Embedding generated in {latency:.2f}s for item {item_id}")
            
        except Exception as e:
            logger.error(f"Embedding API error for item {item_id}: {e}")
            raise self.retry(exc=e, countdown=60)
        
        # Store embedding in database (as JSON)
        item.embedding = embedding
        db.commit()
        
        # Update Elasticsearch with embedding
        try:
            es = get_elasticsearch_client()
            
            # Get existing document or create update
            update_body = {
                "doc": {
                    "embedding": embedding
                },
                "doc_as_upsert": True
            }
            
            es.update(index=INDEX_NAME, id=str(item.id), body=update_body)
            logger.info(f"Updated Elasticsearch with embedding for item {item_id}")
            
        except Exception as e:
            logger.error(f"Error updating Elasticsearch embedding for item {item_id}: {e}")
            # Don't fail the task if ES update fails
        
        return {
            "status": "success",
            "item_id": str(item_id),
            "embedding_dim": len(embedding),
            "latency_seconds": latency
        }
        
    except Exception as e:
        logger.error(f"Error embedding item {item_id}: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()

