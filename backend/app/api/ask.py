"""
Ask endpoint implementation - RAG-style question answering with citations.
"""
import json
import logging
from typing import Optional, List, Dict, Any
from app.api.search import search_knowledge_items
from app.ai.provider import get_ai_provider
from app.ai.prompts import get_ask_prompt
from app.ai.schemas import AskResponse
from app.ai.rate_limit import openai_rate_limiter, anthropic_rate_limiter
from app.config import settings

logger = logging.getLogger(__name__)


async def ask_question(
    question: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: int = 5,
    semantic: bool = True
) -> Dict[str, Any]:
    """
    Answer a question using RAG (Retrieval-Augmented Generation).
    
    Args:
        question: User's question
        filters: Optional search filters (source_type, primary_language, etc.)
        top_k: Number of items to retrieve
        semantic: Use semantic search (requires embeddings)
        
    Returns:
        Dictionary with answer, citations, and matched items
    """
    # Get AI provider
    provider = get_ai_provider()
    if not provider.is_available():
        raise ValueError("AI provider not configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY.")
    
    filters = filters or {}
    
    # Generate query embedding for semantic search
    query_embedding = None
    if semantic:
        try:
            query_embedding = await provider.generate_embedding(question)
        except Exception as e:
            logger.warning(f"Failed to generate query embedding: {e}. Falling back to keyword search.")
            semantic = False
    
    # Retrieve relevant items
    search_results = search_knowledge_items(
        q=question,
        source_type=filters.get('source_type'),
        primary_language=filters.get('primary_language'),
        framework=filters.get('framework'),
        tags=filters.get('tags'),
        semantic=semantic,
        hybrid=True if semantic else False,
        query_embedding=query_embedding,
        page=1,
        size=top_k
    )
    
    items = search_results.get('items', [])
    
    if not items:
        return {
            "answer": "I couldn't find any relevant information to answer your question. Please try rephrasing or adjusting your search filters.",
            "confidence": 0.0,
            "citations": [],
            "matched_items": []
        }
    
    # Build prompt with context
    prompt = get_ask_prompt(question, items)
    
    # Generate answer
    try:
        # Apply rate limiting
        rate_limiter = openai_rate_limiter if settings.ai_provider.lower() == "openai" else anthropic_rate_limiter
        await rate_limiter.acquire()
        
        response_text = await provider.generate_text(
            prompt,
            system_prompt="You are a helpful programming assistant that answers questions using provided sources. Always cite your sources.",
            temperature=0.3,
            max_tokens=1000
        )
        
        # Parse JSON response
        response_text = response_text.strip()
        if response_text.startswith('```'):
            # Remove markdown code blocks
            lines = response_text.split('\n')
            response_text = '\n'.join([l for l in lines if not l.strip().startswith('```')])
        
        answer_data = json.loads(response_text)
        answer_obj = AskResponse(**answer_data)
        
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse AI response: {e}")
        logger.error(f"Response text: {response_text[:500]}")
        # Fallback answer
        answer_obj = AskResponse(
            answer="I found relevant information, but encountered an error formatting the response.",
            confidence=0.5
        )
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        raise
    
    # Build citations
    citations = []
    for idx, item in enumerate(items, 1):
        citations.append({
            "number": idx,
            "title": item.get('title', 'Untitled'),
            "source_url": item.get('source_url', ''),
            "source_name": item.get('source_name', ''),
            "id": item.get('id', '')
        })
    
    return {
        "answer": answer_obj.answer,
        "confidence": answer_obj.confidence,
        "citations": citations,
        "matched_items": items[:top_k]  # Include full items for reference
    }

