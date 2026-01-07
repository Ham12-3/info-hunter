"""
Pydantic schemas for validating AI-generated JSON responses.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


class CodeSnippetEnrichment(BaseModel):
    """Enrichment data for a single code snippet."""
    intent: str = Field(..., description="What this code snippet demonstrates")
    dependencies: List[str] = Field(default_factory=list, description="Required libraries/packages")
    pitfalls: List[str] = Field(default_factory=list, description="Common mistakes or gotchas")


class KnowledgeItemEnrichment(BaseModel):
    """Expected JSON structure from AI enrichment."""
    summary: str = Field(..., max_length=500, description="Concise summary")
    tags: List[str] = Field(..., min_items=0, max_items=15, description="Relevant tags")
    primary_language: Optional[str] = Field(None, description="Detected programming language")
    framework: Optional[str] = Field(None, description="Detected framework")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score 0-1")
    code_snippets: List[CodeSnippetEnrichment] = Field(default_factory=list, description="Enrichment for each code snippet")
    
    @validator('tags')
    def validate_tags(cls, v):
        """Ensure tags are lowercase and clean."""
        return [tag.lower().strip().replace(' ', '-') for tag in v if tag.strip()]


class AskResponse(BaseModel):
    """Expected JSON structure from ask endpoint."""
    answer: str = Field(..., description="Answer with citations")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")

