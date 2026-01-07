"""
FastAPI route definitions.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID
import logging

from app.db.base import get_db
from app.db.models import KnowledgeItem, SavedSearch
from app.api.search import search_knowledge_items
from app.api.ask import ask_question
from app.search.client import get_elasticsearch_client
from app.search.index import ensure_index_exists
from app.ingest.github import GitHubConnector
from app.ingest.stackexchange import StackExchangeConnector
from app.ingest.rss import RSSConnector
from app.tasks.ingestion import ingest_github, ingest_stackexchange, ingest_rss
from app.tasks.enrich import enrich_knowledge_item
from app.tasks.embed import embed_knowledge_item
from app.ai.provider import get_ai_provider

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic models for request/response
class SavedSearchCreate(BaseModel):
    name: str
    query: Optional[str] = None
    source_type: Optional[str] = None
    primary_language: Optional[str] = None
    framework: Optional[str] = None
    tags: Optional[List[str]] = None


class SavedSearchResponse(BaseModel):
    id: UUID
    name: str
    query: Optional[str]
    source_type: Optional[str]
    primary_language: Optional[str]
    framework: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime]
    match_count: int
    
    class Config:
        from_attributes = True


class KnowledgeItemResponse(BaseModel):
    id: UUID
    source_type: str
    source_name: str
    source_url: str
    title: str
    summary: Optional[str]
    body_text: str
    code_snippets: List[dict]
    tags: List[str]
    primary_language: Optional[str]
    framework: Optional[str]
    author: Optional[str]
    licence: Optional[str]
    published_at: Optional[datetime]
    found_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/search")
async def search(
    q: Optional[str] = Query(None, description="Search query text"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    primary_language: Optional[str] = Query(None, description="Filter by primary language"),
    framework: Optional[str] = Query(None, description="Filter by framework"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags"),
    from_date: Optional[str] = Query(None, description="Filter by published date (ISO format)"),
    semantic: bool = Query(False, description="Use semantic search (requires embeddings)"),
    hybrid: bool = Query(False, description="Use hybrid search (keyword + semantic)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Results per page"),
):
    """
    Search knowledge items with filters. Supports keyword, semantic, and hybrid search.
    """
    # Parse tags
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
    
    # Generate query embedding if semantic/hybrid search
    query_embedding = None
    if (semantic or hybrid) and q:
        try:
            provider = get_ai_provider()
            if provider.is_available():
                import asyncio
                query_embedding = asyncio.run(provider.generate_embedding(q))
            else:
                raise HTTPException(
                    status_code=400,
                    detail="AI provider not configured. Semantic/hybrid search requires OPENAI_API_KEY or ANTHROPIC_API_KEY."
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating query embedding: {str(e)}")
    
    try:
        results = search_knowledge_items(
            q=q,
            source_type=source_type,
            primary_language=primary_language,
            framework=framework,
            tags=tag_list,
            from_date=from_date,
            semantic=semantic,
            hybrid=hybrid,
            query_embedding=query_embedding,
            page=page,
            size=size
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/{item_id}", response_model=KnowledgeItemResponse)
async def get_knowledge_item(item_id: UUID, db: Session = Depends(get_db)):
    """
    Get a specific knowledge item by ID.
    """
    item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return item


@router.post("/admin/ingest/run")
async def run_ingestion(
    source: str = Query(..., description="Source to ingest: github, stackexchange, or rss"),
    topics: Optional[str] = Query(None, description="For GitHub: comma-separated topics"),
    keyword: Optional[str] = Query(None, description="For GitHub: search keyword"),
    max_repos: int = Query(50, description="For GitHub: maximum repositories"),
    tags: Optional[str] = Query(None, description="For Stack Exchange: comma-separated tags"),
    max_items: int = Query(50, description="Maximum items to fetch"),
    max_items_per_feed: int = Query(20, description="For RSS: items per feed"),
):
    """
    Manually trigger ingestion from a specific source.
    """
    # Ensure index exists
    es_client = get_elasticsearch_client()
    ensure_index_exists()
    
    db = next(get_db())
    
    try:
        if source == "github":
            topic_list = [t.strip() for t in topics.split(',')] if topics else None
            connector = GitHubConnector()
            stats = connector.ingest(
                db, es_client,
                topics=topic_list,
                keyword=keyword,
                max_repos=max_repos
            )
        elif source == "stackexchange":
            tag_list = [t.strip() for t in tags.split(',')] if tags else None
            connector = StackExchangeConnector()
            stats = connector.ingest(
                db, es_client,
                tags=tag_list,
                max_items=max_items
            )
        elif source == "rss":
            connector = RSSConnector()
            stats = connector.ingest(
                db, es_client,
                max_items_per_feed=max_items_per_feed
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown source: {source}")
        
        return {
            "status": "success",
            "source": source,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/saved-searches", response_model=SavedSearchResponse)
async def create_saved_search(
    search: SavedSearchCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new saved search.
    """
    saved_search = SavedSearch(
        name=search.name,
        query=search.query,
        source_type=search.source_type,
        primary_language=search.primary_language,
        framework=search.framework,
        tags=search.tags or []
    )
    
    db.add(saved_search)
    db.commit()
    db.refresh(saved_search)
    
    return saved_search


@router.get("/saved-searches", response_model=List[SavedSearchResponse])
async def list_saved_searches(db: Session = Depends(get_db)):
    """
    List all saved searches.
    """
    searches = db.query(SavedSearch).all()
    return searches


@router.post("/alerts/run")
async def run_alerts():
    """
    Manually trigger saved search alerts (for testing).
    Prints results to console in MVP.
    """
    from app.tasks.ingestion import run_saved_search_alerts
    
    # Run synchronously for manual trigger
    run_saved_search_alerts()
    
    return {"status": "completed", "message": "Alerts printed to console/logs"}


class AskRequest(BaseModel):
    """Request model for /ask endpoint."""
    question: str
    filters: Optional[Dict[str, Any]] = None
    top_k: int = 5
    semantic: bool = True


@router.post("/ask")
async def ask(
    request: AskRequest = Body(...)
):
    """
    Answer a question using RAG (Retrieval-Augmented Generation).
    Retrieves relevant knowledge items and generates an answer with citations.
    """
    provider = get_ai_provider()
    if not provider.is_available():
        raise HTTPException(
            status_code=400,
            detail="AI provider not configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY."
        )
    
    try:
        result = await ask_question(
            question=request.question,
            filters=request.filters,
            top_k=request.top_k,
            semantic=request.semantic
        )
        return result
    except Exception as e:
        logger.error(f"Error in /ask endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/ai/enrich")
async def admin_enrich(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of items to enqueue"),
    db: Session = Depends(get_db)
):
    """
    Enqueue enrichment jobs for knowledge items missing AI extraction.
    """
    provider = get_ai_provider()
    if not provider.is_available():
        raise HTTPException(
            status_code=400,
            detail="AI provider not configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY."
        )
    
    # Find items without AI enrichment
    items = db.query(KnowledgeItem).filter(
        KnowledgeItem.ai_extracted_at.is_(None)
    ).limit(limit).all()
    
    if not items:
        return {
            "status": "no_items",
            "message": "No items found that need enrichment",
            "enqueued": 0
        }
    
    # Enqueue enrichment tasks
    enqueued = 0
    for item in items:
        try:
            enrich_knowledge_item.delay(str(item.id))
            enqueued += 1
        except Exception as e:
            logger.error(f"Error enqueueing enrichment for item {item.id}: {e}")
    
    return {
        "status": "success",
        "enqueued": enqueued,
        "total_found": len(items)
    }


@router.post("/admin/ai/embed")
async def admin_embed(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of items to enqueue"),
    db: Session = Depends(get_db)
):
    """
    Enqueue embedding jobs for knowledge items missing embeddings.
    """
    provider = get_ai_provider()
    if not provider.is_available():
        raise HTTPException(
            status_code=400,
            detail="AI provider not configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY."
        )
    
    # Find items without embeddings
    items = db.query(KnowledgeItem).filter(
        KnowledgeItem.embedding.is_(None)
    ).limit(limit).all()
    
    if not items:
        return {
            "status": "no_items",
            "message": "No items found that need embeddings",
            "enqueued": 0
        }
    
    # Enqueue embedding tasks
    enqueued = 0
    for item in items:
        try:
            embed_knowledge_item.delay(str(item.id))
            enqueued += 1
        except Exception as e:
            logger.error(f"Error enqueueing embedding for item {item.id}: {e}")
    
    return {
        "status": "success",
        "enqueued": enqueued,
        "total_found": len(items)
    }


# Include router in main app
def include_routes(app):
    """Include all routes in the FastAPI app."""
    app.include_router(router, tags=["api"])

