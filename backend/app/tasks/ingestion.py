"""
Celery tasks for ingestion jobs.
"""
from datetime import datetime
from app.tasks.celery_app import celery_app
from app.db.base import SessionLocal
from app.search.client import get_elasticsearch_client
from app.search.index import ensure_index_exists
from app.ingest.github import GitHubConnector
from app.ingest.stackexchange import StackExchangeConnector
from app.ingest.rss import RSSConnector
from app.db.models import SavedSearch
from app.api.search import search_knowledge_items
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.ingestion.ingest_github')
def ingest_github(**kwargs):
    """
    Celery task to ingest from GitHub.
    
    Args:
        **kwargs: Arguments passed to GitHubConnector.fetch_items()
    """
    logger.info("Starting GitHub ingestion task")
    
    # Ensure index exists
    es_client = get_elasticsearch_client()
    ensure_index_exists()
    
    # Get database session
    db = SessionLocal()
    
    try:
        connector = GitHubConnector()
        stats = connector.ingest(db, es_client, **kwargs)
        logger.info(f"GitHub ingestion completed: {stats}")
        return stats
    except Exception as e:
        logger.error(f"GitHub ingestion failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


@celery_app.task(name='app.tasks.ingestion.ingest_stackexchange')
def ingest_stackexchange(**kwargs):
    """
    Celery task to ingest from Stack Exchange.
    
    Args:
        **kwargs: Arguments passed to StackExchangeConnector.fetch_items()
    """
    logger.info("Starting Stack Exchange ingestion task")
    
    # Ensure index exists
    es_client = get_elasticsearch_client()
    ensure_index_exists()
    
    # Get database session
    db = SessionLocal()
    
    try:
        connector = StackExchangeConnector()
        stats = connector.ingest(db, es_client, **kwargs)
        logger.info(f"Stack Exchange ingestion completed: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Stack Exchange ingestion failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


@celery_app.task(name='app.tasks.ingestion.ingest_rss')
def ingest_rss(**kwargs):
    """
    Celery task to ingest from RSS feeds.
    
    Args:
        **kwargs: Arguments passed to RSSConnector.fetch_items()
    """
    logger.info("Starting RSS ingestion task")
    
    # Ensure index exists
    es_client = get_elasticsearch_client()
    ensure_index_exists()
    
    # Get database session
    db = SessionLocal()
    
    try:
        connector = RSSConnector()
        stats = connector.ingest(db, es_client, **kwargs)
        logger.info(f"RSS ingestion completed: {stats}")
        return stats
    except Exception as e:
        logger.error(f"RSS ingestion failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


@celery_app.task(name='app.tasks.ingestion.run_saved_search_alerts')
def run_saved_search_alerts():
    """
    Celery task to run all saved searches and print new matches to console.
    This is the MVP version - later can be extended to send emails/notifications.
    """
    logger.info("Starting saved search alerts task")
    
    db = SessionLocal()
    
    try:
        saved_searches = db.query(SavedSearch).all()
        logger.info(f"Running {len(saved_searches)} saved searches")
        
        from app.api.search import search_knowledge_items
        
        for saved_search in saved_searches:
            try:
                # Build search query
                search_params = {
                    'q': saved_search.query or '',
                    'source_type': saved_search.source_type,
                    'primary_language': saved_search.primary_language,
                    'framework': saved_search.framework,
                    'tags': saved_search.tags,
                    'page': 1,
                    'size': 10
                }
                
                # Run search
                results = search_knowledge_items(**search_params)
                
                # Update saved search
                saved_search.last_run_at = datetime.utcnow()
                saved_search.match_count = results.get('total', 0)
                db.commit()
                
                # Print results to console (MVP)
                print(f"\n{'='*60}")
                print(f"Saved Search: {saved_search.name}")
                print(f"Query: {saved_search.query or 'N/A'}")
                print(f"Matches: {results.get('total', 0)}")
                print(f"{'='*60}")
                
                for item in results.get('items', [])[:5]:  # Print top 5
                    print(f"\nTitle: {item.get('title')}")
                    print(f"Source: {item.get('source_name')} - {item.get('source_url')}")
                    print(f"Language: {item.get('primary_language', 'N/A')}")
                    print("-" * 60)
                
            except Exception as e:
                logger.error(f"Error running saved search {saved_search.id}: {e}")
                continue
        
        logger.info("Saved search alerts completed")
        
    except Exception as e:
        logger.error(f"Saved search alerts task failed: {e}", exc_info=True)
    finally:
        db.close()

