"""
Deduplication utilities for knowledge items.
Generates deterministic keys and content hashes.
"""
import hashlib
from typing import List, Dict


def generate_dedupe_key(source_type: str, source_url: str) -> str:
    """
    Generate a deterministic deduplication key from source type and URL.
    
    Args:
        source_type: Type of source (github, stackexchange, rss, etc.)
        source_url: Canonical source URL
        
    Returns:
        Deterministic dedupe key
    """
    # Normalize URL (remove trailing slashes, convert to lowercase)
    normalized_url = source_url.rstrip('/').lower()
    
    # Combine source type and URL
    key_string = f"{source_type}::{normalized_url}"
    
    # Return as-is (short enough) or hash if too long
    if len(key_string) <= 500:
        return key_string
    else:
        # Hash if too long
        return hashlib.sha256(key_string.encode()).hexdigest()


def generate_content_hash(title: str, body_text: str, code_snippets: List[Dict]) -> str:
    """
    Generate SHA-256 hash of content for change detection.
    
    Args:
        title: Item title
        body_text: Body text content
        code_snippets: List of code snippet dictionaries
        
    Returns:
        SHA-256 hash as hex string
    """
    # Combine all content
    content_parts = [title or "", body_text or ""]
    
    # Add code snippets (language + code)
    for snippet in code_snippets or []:
        snippet_str = f"{snippet.get('language', '')}::{snippet.get('code', '')}"
        content_parts.append(snippet_str)
    
    # Join and hash
    content_string = "|||".join(content_parts)
    return hashlib.sha256(content_string.encode()).hexdigest()

