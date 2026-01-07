"""
SQLAlchemy models for the Info Hunter application.
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, Index, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class KnowledgeItem(Base):
    """
    Main model for storing programming knowledge and code snippets.
    Represents a single piece of knowledge from various sources.
    """
    __tablename__ = "knowledge_items"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Source information
    source_type = Column(String(50), nullable=False, index=True)  # github, stackexchange, rss, html
    source_name = Column(String(200), nullable=False)  # e.g., "GitHub", "StackOverflow", "Real Python"
    source_url = Column(Text, nullable=False)  # Canonical URL

    # Content
    title = Column(String(500), nullable=False)
    summary = Column(Text)  # Short text summary
    body_text = Column(Text)  # Cleaned explanation text

    # Code snippets stored as JSON array of objects
    # Format: [{"language": "python", "code": "...", "context": "..."}, ...]
    code_snippets = Column(JSON, default=list)

    # Metadata
    tags = Column(ARRAY(String), default=list)
    primary_language = Column(String(100), index=True)  # e.g., "Python", "TypeScript"
    framework = Column(String(100), index=True, nullable=True)  # e.g., "React", "Django"
    author = Column(String(200), nullable=True)
    licence = Column(String(100), nullable=True)

    # Dates
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    found_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Deduplication
    content_hash = Column(String(64), nullable=False)  # SHA-256 hash of content
    dedupe_key = Column(String(500), nullable=False, unique=True, index=True)  # Deterministic key

    # AI-generated fields
    ai_summary = Column(Text, nullable=True)  # AI-generated summary
    ai_tags = Column(ARRAY(String), nullable=True)  # AI-extracted tags
    ai_primary_language = Column(String(100), nullable=True)  # AI-detected primary language
    ai_framework = Column(String(100), nullable=True)  # AI-detected framework
    ai_quality_score = Column(Float, nullable=True)  # Quality score from 0-1
    ai_extracted_at = Column(DateTime(timezone=True), nullable=True)  # When AI enrichment ran
    embedding = Column(JSON, nullable=True)  # Vector embedding as JSON array

    # Indexes for common queries
    __table_args__ = (
        Index('idx_source_type_language', 'source_type', 'primary_language'),
        Index('idx_dedupe_key', 'dedupe_key'),
        Index('idx_published_at', 'published_at'),
    )

    def __repr__(self):
        return f"<KnowledgeItem(id={self.id}, source_type={self.source_type}, title={self.title[:50]}...)>"


class SavedSearch(Base):
    """
    Model for storing saved searches that users can run periodically.
    """
    __tablename__ = "saved_searches"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Search details
    name = Column(String(200), nullable=False)
    query = Column(String(500))  # Search query text
    source_type = Column(String(50), nullable=True)
    primary_language = Column(String(100), nullable=True)
    framework = Column(String(100), nullable=True)
    tags = Column(ARRAY(String), default=list)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    match_count = Column(Integer, default=0)  # Number of matches from last run

    def __repr__(self):
        return f"<SavedSearch(id={self.id}, name={self.name})>"

