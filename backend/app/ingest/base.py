"""
Base class for ingestion connectors.
Provides common functionality for all connectors.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from app.db.models import KnowledgeItem
from app.extract.markdown import extract_code_blocks as extract_md_blocks, extract_body_text as extract_md_text, generate_summary as generate_md_summary
from app.extract.html import extract_code_blocks as extract_html_blocks, clean_html_text, generate_summary as generate_html_summary
from app.extract.language_detect import detect_language_from_code, normalize_language_name
from app.utils.dedupe import generate_dedupe_key, generate_content_hash
from app.utils.http_client import fetch_url
from bs4 import BeautifulSoup
import hashlib
import logging

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """
    Abstract base class for all ingestion connectors.
    Provides common methods for processing and storing knowledge items.
    """
    
    def __init__(self, source_name: str, source_type: str):
        """
        Initialize connector.
        
        Args:
            source_name: Human-readable source name
            source_type: Source type identifier (github, stackexchange, rss, etc.)
        """
        self.source_name = source_name
        self.source_type = source_type
    
    @abstractmethod
    def fetch_items(self, **kwargs) -> List[Dict]:
        """
        Fetch items from the source.
        Must be implemented by subclasses.
        
        Returns:
            List of raw item dictionaries
        """
        pass
    
    def process_item(self, raw_item: Dict) -> Optional[KnowledgeItem]:
        """
        Process a raw item into a KnowledgeItem model.
        
        Args:
            raw_item: Raw item dictionary from fetch_items()
            
        Returns:
            KnowledgeItem instance or None if processing fails
        """
        try:
            # Extract content based on source type
            content = raw_item.get('content', '')
            content_type = raw_item.get('content_type', 'html')  # html or markdown
            
            # Extract code blocks
            if content_type == 'markdown':
                code_snippets = extract_md_blocks(content)
                body_text = extract_md_text(content)
                summary = generate_md_summary(content)
            else:
                code_snippets = extract_html_blocks(content)
                body_text = clean_html_text(content)
                summary = generate_html_summary(content)
            
            # Improve language detection for code snippets
            for snippet in code_snippets:
                detected_lang = detect_language_from_code(
                    snippet['code'],
                    hint=snippet.get('language')
                )
                snippet['language'] = normalize_language_name(detected_lang)
            
            # Determine primary language (most common in snippets)
            primary_language = None
            if code_snippets:
                languages = [s['language'] for s in code_snippets if s['language'] != 'text']
                if languages:
                    # Most common language
                    primary_language = max(set(languages), key=languages.count)
            
            # Generate dedupe key and content hash
            source_url = raw_item['source_url']
            dedupe_key = generate_dedupe_key(self.source_type, source_url)
            content_hash = generate_content_hash(
                raw_item.get('title', ''),
                body_text,
                code_snippets
            )
            
            # Create KnowledgeItem
            item = KnowledgeItem(
                source_type=self.source_type,
                source_name=self.source_name,
                source_url=source_url,
                title=raw_item.get('title', 'Untitled'),
                summary=summary or raw_item.get('summary'),
                body_text=body_text,
                code_snippets=code_snippets,
                tags=raw_item.get('tags', []),
                primary_language=primary_language,
                framework=raw_item.get('framework'),
                author=raw_item.get('author'),
                licence=raw_item.get('licence'),
                published_at=raw_item.get('published_at'),
                content_hash=content_hash,
                dedupe_key=dedupe_key
            )
            
            return item
            
        except Exception as e:
            logger.error(f"Error processing item: {e}", exc_info=True)
            return None
    
    def ingest(self, db_session, search_client, **kwargs) -> Dict[str, int]:
        """
        Main ingestion method: fetch, process, store, and index items.
        
        Args:
            db_session: SQLAlchemy database session
            search_client: Elasticsearch client
            **kwargs: Arguments passed to fetch_items()
            
        Returns:
            Dictionary with counts: {'fetched': N, 'processed': M, 'stored': K, 'indexed': L}
        """
        stats = {'fetched': 0, 'processed': 0, 'stored': 0, 'indexed': 0, 'skipped': 0}
        
        try:
            # Fetch raw items
            raw_items = self.fetch_items(**kwargs)
            stats['fetched'] = len(raw_items)
            
            logger.info(f"Fetched {stats['fetched']} items from {self.source_name}")
            
            # Process each item
            for raw_item in raw_items:
                try:
                    # Process into KnowledgeItem
                    item = self.process_item(raw_item)
                    if not item:
                        continue
                    
                    stats['processed'] += 1
                    
                    # Check if item exists (by dedupe_key)
                    existing = db_session.query(KnowledgeItem).filter(
                        KnowledgeItem.dedupe_key == item.dedupe_key
                    ).first()
                    
                    if existing:
                        # Check if content changed
                        if existing.content_hash == item.content_hash:
                            # No changes, skip
                            stats['skipped'] += 1
                            continue
                        else:
                            # Update existing
                            for key, value in item.__dict__.items():
                                if key != 'id' and not key.startswith('_'):
                                    setattr(existing, key, value)
                            item = existing
                            stats['stored'] += 1
                    else:
                        # New item
                        db_session.add(item)
                        stats['stored'] += 1
                    
                    db_session.commit()
                    
                    # Index in Elasticsearch
                    self._index_item(search_client, item)
                    stats['indexed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing item {raw_item.get('source_url')}: {e}")
                    db_session.rollback()
                    continue
            
            logger.info(f"Ingestion complete for {self.source_name}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error during ingestion from {self.source_name}: {e}", exc_info=True)
            db_session.rollback()
            return stats
    
    def _index_item(self, search_client, item: KnowledgeItem):
        """
        Index a KnowledgeItem in Elasticsearch.
        
        Args:
            search_client: Elasticsearch client
            item: KnowledgeItem to index
        """
        try:
            from app.search.index import INDEX_NAME
            
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
                "embedding": item.embedding,  # Include embedding if present
            }
            
            search_client.index(
                index=INDEX_NAME,
                id=str(item.id),
                document=doc
            )
            
        except Exception as e:
            logger.error(f"Error indexing item {item.id}: {e}")

