"""
Unit tests for AI enrichment functionality.
"""
import pytest
from app.ai.schemas import KnowledgeItemEnrichment, CodeSnippetEnrichment
from app.ai.prompts import get_enrichment_prompt


def test_code_snippet_enrichment_schema():
    """Test CodeSnippetEnrichment Pydantic schema."""
    snippet = CodeSnippetEnrichment(
        intent="Demonstrates async/await pattern",
        dependencies=["asyncio"],
        pitfalls=["Forgetting to await", "Blocking in async function"]
    )
    
    assert snippet.intent == "Demonstrates async/await pattern"
    assert "asyncio" in snippet.dependencies
    assert len(snippet.pitfalls) == 2


def test_knowledge_item_enrichment_schema():
    """Test KnowledgeItemEnrichment Pydantic schema."""
    enrichment = KnowledgeItemEnrichment(
        summary="This article explains async programming in Python",
        tags=["python", "async", "await"],
        primary_language="Python",
        framework=None,
        quality_score=0.85,
        code_snippets=[
            CodeSnippetEnrichment(
                intent="Basic async function",
                dependencies=["asyncio"],
                pitfalls=[]
            )
        ]
    )
    
    assert enrichment.primary_language == "Python"
    assert enrichment.quality_score == 0.85
    assert len(enrichment.tags) == 3
    assert len(enrichment.code_snippets) == 1


def test_enrichment_prompt_generation():
    """Test enrichment prompt generation from item dict."""
    item = {
        'title': 'Async Python Guide',
        'body_text': 'This guide explains async programming...',
        'code_snippets': [
            {
                'language': 'python',
                'code': 'async def hello():\n    print("Hello")',
                'context': 'Example async function'
            }
        ]
    }
    
    prompt = get_enrichment_prompt(item)
    
    assert 'Async Python Guide' in prompt
    assert 'python' in prompt
    assert 'async def' in prompt
    assert 'JSON' in prompt  # Should request JSON output


def test_tag_normalization():
    """Test that tags are normalized to lowercase."""
    enrichment = KnowledgeItemEnrichment(
        summary="Test",
        tags=["Python", "JavaScript", "React.js"],
        quality_score=0.8,
        code_snippets=[]
    )
    
    # Tags should be normalized by validator
    assert all(tag.islower() or '-' in tag for tag in enrichment.tags)


def test_quality_score_validation():
    """Test quality score range validation."""
    # Valid scores
    enrichment = KnowledgeItemEnrichment(
        summary="Test",
        tags=[],
        quality_score=0.5,
        code_snippets=[]
    )
    assert enrichment.quality_score == 0.5
    
    # Should raise for invalid scores
    with pytest.raises(Exception):
        KnowledgeItemEnrichment(
            summary="Test",
            tags=[],
            quality_score=1.5,  # Out of range
            code_snippets=[]
        )

