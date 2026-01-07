"""
Markdown extraction utilities.
Extracts code blocks and surrounding text from Markdown content.
"""
import re
from typing import List, Dict, Tuple
import markdown
from bs4 import BeautifulSoup


def extract_code_blocks(markdown_content: str) -> List[Dict[str, str]]:
    """
    Extracts fenced code blocks from Markdown content.
    
    Args:
        markdown_content: Raw Markdown text
        
    Returns:
        List of dictionaries with 'language', 'code', and 'context' keys
    """
    code_snippets = []
    
    # Pattern to match fenced code blocks (```language\ncode\n```)
    # Also matches ```\ncode\n``` (no language)
    pattern = r'```(\w+)?\n(.*?)```'
    
    matches = re.finditer(pattern, markdown_content, re.DOTALL)
    
    for match in matches:
        language = match.group(1) or "text"
        code = match.group(2).strip()
        
        # Extract context (text before the code block, up to 200 chars)
        start_pos = match.start()
        context_start = max(0, start_pos - 200)
        context_text = markdown_content[context_start:start_pos].strip()
        
        # Clean context: remove markdown syntax, get last few sentences
        if context_text:
            # Convert markdown to plain text for context
            context_clean = BeautifulSoup(
                markdown.markdown(context_text[-300:]), 
                'html.parser'
            ).get_text()
            # Get last sentence or last 150 chars
            sentences = context_clean.split('.')
            context = sentences[-1].strip()[:150] if sentences else context_clean[:150]
        else:
            context = ""
        
        if code:  # Only add non-empty code blocks
            code_snippets.append({
                "language": language.lower(),
                "code": code,
                "context": context
            })
    
    return code_snippets


def extract_body_text(markdown_content: str) -> str:
    """
    Extracts and cleans body text from Markdown, removing code blocks.
    
    Args:
        markdown_content: Raw Markdown text
        
    Returns:
        Cleaned plain text content
    """
    # Remove fenced code blocks
    content_without_blocks = re.sub(r'```[\s\S]*?```', '', markdown_content)
    
    # Remove inline code (but keep the text around it)
    content_without_inline = re.sub(r'`[^`]+`', '', content_without_blocks)
    
    # Convert markdown to HTML then to plain text
    html = markdown.markdown(content_without_inline)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script, style, and other non-content elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer']):
        element.decompose()
    
    # Get text and clean up whitespace
    text = soup.get_text(separator=' ', strip=True)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text


def generate_summary(markdown_content: str, max_length: int = 300) -> str:
    """
    Generates a short summary from Markdown content.
    Uses the first paragraph or first max_length characters.
    
    Args:
        markdown_content: Raw Markdown text
        max_length: Maximum length of summary
        
    Returns:
        Summary text
    """
    # Remove code blocks first
    content_without_blocks = re.sub(r'```[\s\S]*?```', '', markdown_content)
    
    # Get first paragraph
    paragraphs = content_without_blocks.split('\n\n')
    
    for paragraph in paragraphs:
        # Skip headers and empty paragraphs
        if paragraph.strip() and not paragraph.strip().startswith('#'):
            # Convert to plain text
            html = markdown.markdown(paragraph)
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
            if text:
                # Return first paragraph, truncated if needed
                return text[:max_length]
    
    # Fallback: return first max_length chars of body text
    body_text = extract_body_text(markdown_content)
    return body_text[:max_length] if body_text else ""

