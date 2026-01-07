"""
Elasticsearch index creation and mapping configuration.
"""
from elasticsearch import Elasticsearch
from app.search.client import get_elasticsearch_client
import logging

logger = logging.getLogger(__name__)

INDEX_NAME = "info_hunter_knowledge"


def get_index_mapping() -> dict:
    """
    Returns the Elasticsearch index mapping for the knowledge items.
    Includes text fields, keyword fields, dates, and autocomplete configuration.
    """
    return {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "source_type": {"type": "keyword"},
                "source_name": {"type": "keyword"},
                "source_url": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "autocomplete": {
                            "type": "text",
                            "analyzer": "autocomplete_analyzer",
                            "search_analyzer": "standard"
                        }
                    }
                },
                "summary": {"type": "text"},
                "body_text": {"type": "text"},
                "code_snippets": {
                    "type": "nested",
                    "properties": {
                        "language": {"type": "keyword"},
                        "code": {"type": "text"},
                        "context": {"type": "text"}
                    }
                },
                "tags": {"type": "keyword"},
                "primary_language": {"type": "keyword"},
                "framework": {"type": "keyword"},
                "author": {"type": "keyword"},
                "licence": {"type": "keyword"},
                "published_at": {"type": "date"},
                "found_at": {"type": "date"},
                "updated_at": {"type": "date"},
                # AI-generated fields
                "ai_summary": {"type": "text"},
                "ai_tags": {"type": "keyword"},
                "ai_primary_language": {"type": "keyword"},
                "ai_framework": {"type": "keyword"},
                "ai_quality_score": {"type": "float"},
                # Embedding vector for semantic search
                "embedding": {
                    "type": "dense_vector",
                    "dims": 1536,  # text-embedding-3-small dimension
                    "index": True,
                    "similarity": "cosine"
                }
            }
        },
        "settings": {
            "analysis": {
                "analyzer": {
                    "autocomplete_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "autocomplete_filter"]
                    }
                },
                "filter": {
                    "autocomplete_filter": {
                        "type": "edge_ngram",
                        "min_gram": 2,
                        "max_gram": 20
                    }
                }
            }
        }
    }


def create_index() -> bool:
    """
    Creates the Elasticsearch index with the configured mapping.
    Returns True if successful, False otherwise.
    """
    es = get_elasticsearch_client()
    
    try:
        # Check if index exists
        if es.indices.exists(index=INDEX_NAME):
            logger.info(f"Index {INDEX_NAME} already exists")
            return True
        
        # Create index with mapping
        mapping = get_index_mapping()
        es.indices.create(index=INDEX_NAME, body=mapping)
        logger.info(f"Successfully created index {INDEX_NAME}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating index {INDEX_NAME}: {e}")
        return False


def delete_index() -> bool:
    """
    Deletes the Elasticsearch index (useful for testing/reset).
    Returns True if successful, False otherwise.
    """
    es = get_elasticsearch_client()
    
    try:
        if es.indices.exists(index=INDEX_NAME):
            es.indices.delete(index=INDEX_NAME)
            logger.info(f"Successfully deleted index {INDEX_NAME}")
            return True
        else:
            logger.info(f"Index {INDEX_NAME} does not exist")
            return True
    except Exception as e:
        logger.error(f"Error deleting index {INDEX_NAME}: {e}")
        return False


def ensure_index_exists() -> bool:
    """
    Ensures the index exists, creating it if necessary.
    Returns True if index exists or was created successfully.
    """
    es = get_elasticsearch_client()
    
    if not es.indices.exists(index=INDEX_NAME):
        return create_index()
    return True

