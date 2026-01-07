"""
Search API endpoint implementation.
Provides Elasticsearch query building and result formatting.
"""
from typing import Optional, List
from elasticsearch import Elasticsearch
from app.search.client import get_elasticsearch_client
from app.search.index import INDEX_NAME
import logging

logger = logging.getLogger(__name__)


def build_search_query(q: Optional[str] = None, source_type: Optional[str] = None,
                      primary_language: Optional[str] = None, framework: Optional[str] = None,
                      tags: Optional[List[str]] = None, from_date: Optional[str] = None,
                      semantic: bool = False, hybrid: bool = False, query_embedding: Optional[List[float]] = None,
                      page: int = 1, size: int = 20) -> dict:
    """
    Build Elasticsearch query with filters and search terms.
    
    Args:
        q: Search query text
        source_type: Filter by source type
        primary_language: Filter by primary language
        framework: Filter by framework
        tags: Filter by tags (list)
        from_date: Filter by published date (ISO format)
        page: Page number (1-based)
        size: Results per page
        
    Returns:
        Elasticsearch query dictionary
    """
    must_clauses = []
    filter_clauses = []
    should_clauses = []
    
    # Semantic search (vector similarity)
    if semantic or hybrid:
        if query_embedding:
            vector_query = {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": query_embedding}
                    }
                }
            }
            if semantic and not hybrid:
                # Pure semantic search
                must_clauses.append(vector_query)
            elif hybrid:
                # Hybrid: combine keyword and vector
                should_clauses.append(vector_query)
        else:
            logger.warning("Semantic/hybrid search requested but no query embedding provided")
    
    # Keyword/text search query
    if q:
        keyword_query = {
            "multi_match": {
                "query": q,
                "fields": ["title^3", "title.autocomplete^2", "body_text", "code_snippets.code"],
                "type": "best_fields",
                "fuzziness": "AUTO"
            }
        }
        if semantic and not hybrid:
            # Pure semantic - skip keyword
            pass
        elif hybrid:
            # Hybrid: add keyword to should_clauses
            should_clauses.append(keyword_query)
        else:
            # Pure keyword
            must_clauses.append(keyword_query)
    elif not semantic:
        # Match all if no query and not semantic
        must_clauses.append({"match_all": {}})
    
    # Filters
    if source_type:
        filter_clauses.append({"term": {"source_type": source_type}})
    
    if primary_language:
        filter_clauses.append({"term": {"primary_language": primary_language.lower()}})
    
    if framework:
        filter_clauses.append({"term": {"framework": framework.lower()}})
    
    if tags:
        filter_clauses.append({"terms": {"tags": tags}})
    
    if from_date:
        filter_clauses.append({"range": {"published_at": {"gte": from_date}}})
    
    # Build query
    query = {
        "bool": {}
    }
    
    if must_clauses:
        query["bool"]["must"] = must_clauses
    
    if should_clauses:
        query["bool"]["should"] = should_clauses
        query["bool"]["minimum_should_match"] = 1 if hybrid else 0
    
    if filter_clauses:
        query["bool"]["filter"] = filter_clauses
    
    # Build full search request
    search_request = {
        "query": query,
        "from": (page - 1) * size,
        "size": size,
        "sort": [
            {"published_at": {"order": "desc", "missing": "_last"}},
            "_score"
        ]
    }
    
    # Add highlighting if there's a text query
    if q:
        search_request["highlight"] = {
            "fields": {
                "title": {},
                "body_text": {"fragment_size": 150, "number_of_fragments": 2},
                "code_snippets.code": {"fragment_size": 200, "number_of_fragments": 1}
            }
        }
    
    return search_request


def search_knowledge_items(q: Optional[str] = None, source_type: Optional[str] = None,
                          primary_language: Optional[str] = None, framework: Optional[str] = None,
                          tags: Optional[List[str]] = None, from_date: Optional[str] = None,
                          semantic: bool = False, hybrid: bool = False, query_embedding: Optional[List[float]] = None,
                          page: int = 1, size: int = 20) -> dict:
    """
    Search knowledge items using Elasticsearch.
    
    Args:
        q: Search query text
        source_type: Filter by source type
        primary_language: Filter by primary language
        framework: Filter by framework
        tags: Filter by tags (list)
        from_date: Filter by published date (ISO format)
        page: Page number (1-based)
        size: Results per page
        
    Returns:
        Dictionary with search results
    """
    es = get_elasticsearch_client()
    
    try:
        # Build query
        search_request = build_search_query(
            q=q, source_type=source_type, primary_language=primary_language,
            framework=framework, tags=tags, from_date=from_date,
            semantic=semantic, hybrid=hybrid, query_embedding=query_embedding,
            page=page, size=size
        )
        
        # Execute search (Elasticsearch 8.x accepts body parameter)
        response = es.search(index=INDEX_NAME, body=search_request)
        
        # Format results
        hits = response.get('hits', {})
        total = hits.get('total', {}).get('value', 0) if isinstance(hits.get('total'), dict) else hits.get('total', 0)
        
        items = []
        for hit in hits.get('hits', []):
            source = hit['_source']
            
            # Add highlights if present
            if 'highlight' in hit:
                source['highlight'] = hit['highlight']
            
            # Add score
            source['_score'] = hit.get('_score', 0)
            
            items.append(source)
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'size': size,
            'total_pages': (total + size - 1) // size
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise

