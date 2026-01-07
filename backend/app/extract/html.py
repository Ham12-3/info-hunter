"""
HTML extraction utilities.
Extracts code blocks and cleans text from HTML content.
"""
from bs4 import BeautifulSoup
from typing import List, Dict
import re


def extract_code_blocks(html_content: str) -> List[Dict[str, str]]:
    """
    Extracts code blocks from HTML content.
    Looks for <pre><code>, <pre>, and <code> elements.
    
    Args:
        html_content: Raw HTML text
        
    Returns:
        List of dictionaries with 'language', 'code', and 'context' keys
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    code_snippets = []
    
    # Find all code blocks
    # Try <pre><code> first (most common)
    pre_code_blocks = soup.find_all('pre')
    
    for pre in pre_code_blocks:
        code_element = pre.find('code')
        
        if code_element:
            code = code_element.get_text(strip=False)
            # Try to detect language from class names
            classes = code_element.get('class', [])
            language = "text"
            
            # Common patterns: class="language-python", class="python", etc.
            for class_name in classes:
                if 'language-' in class_name:
                    language = class_name.replace('language-', '').lower()
                    break
                elif class_name in ['python', 'javascript', 'java', 'cpp', 'c', 'css', 'html', 
                                     'json', 'xml', 'bash', 'shell', 'sql', 'typescript', 'go', 
                                     'rust', 'php', 'ruby', 'swift', 'kotlin']:
                    language = class_name.lower()
                    break
            
            # Extract context (previous sibling text, up to 200 chars)
            context = ""
            prev_sibling = pre.find_previous_sibling()
            if prev_sibling:
                context_text = prev_sibling.get_text(separator=' ', strip=True)
                # Get last sentence or 150 chars
                sentences = context_text.split('.')
                context = sentences[-1].strip()[:150] if sentences else context_text[:150]
            else:
                # Try parent's previous sibling
                parent = pre.find_parent()
                if parent:
                    prev_parent = parent.find_previous_sibling()
                    if prev_parent:
                        context_text = prev_parent.get_text(separator=' ', strip=True)
                        sentences = context_text.split('.')
                        context = sentences[-1].strip()[:150] if sentences else context_text[:150]
            
            if code.strip():
                code_snippets.append({
                    "language": language,
                    "code": code.strip(),
                    "context": context
                })
    
    # Also check standalone <code> elements (inline code, less priority)
    # But skip if they're inside a <pre> (already captured above)
    standalone_codes = soup.find_all('code')
    for code_elem in standalone_codes:
        # Skip if already inside a <pre>
        if code_elem.find_parent('pre'):
            continue
        
        code = code_elem.get_text(strip=False)
        # Only include if it's a block (has newlines) or relatively long
        if '\n' in code or len(code) > 50:
            classes = code_elem.get('class', [])
            language = "text"
            for class_name in classes:
                if 'language-' in class_name:
                    language = class_name.replace('language-', '').lower()
                    break
            
            context = ""
            prev = code_elem.find_previous_sibling()
            if prev:
                context_text = prev.get_text(separator=' ', strip=True)
                context = context_text[:150]
            
            if code.strip():
                code_snippets.append({
                    "language": language,
                    "code": code.strip(),
                    "context": context
                })
    
    return code_snippets


def clean_html_text(html_content: str) -> str:
    """
    Cleans HTML content to extract plain text, removing boilerplate.
    
    Args:
        html_content: Raw HTML text
        
    Returns:
        Cleaned plain text content
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                         'aside', 'advertisement', 'ads', 'cookie-banner',
                         'social-share', 'comments']):
        element.decompose()
    
    # Remove elements with common boilerplate classes/ids
    boilerplate_selectors = [
        '[class*="nav"]',
        '[class*="menu"]',
        '[class*="footer"]',
        '[class*="header"]',
        '[class*="sidebar"]',
        '[class*="ad"]',
        '[class*="cookie"]',
        '[id*="nav"]',
        '[id*="menu"]',
        '[id*="footer"]',
        '[id*="header"]',
        '[id*="sidebar"]',
        '[id*="ad"]',
    ]
    
    for selector in boilerplate_selectors:
        for elem in soup.select(selector):
            elem.decompose()
    
    # Get text from main content areas first
    main_content = soup.find(['main', 'article', '[role="main"]', '.content', '#content'])
    
    if main_content:
        text = main_content.get_text(separator=' ', strip=True)
    else:
        text = soup.get_text(separator=' ', strip=True)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text


def generate_summary(html_content: str, max_length: int = 300) -> str:
    """
    Generates a short summary from HTML content.
    Uses the first paragraph or meta description.
    
    Args:
        html_content: Raw HTML text
        max_length: Maximum length of summary
        
    Returns:
        Summary text
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try meta description first
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        return meta_desc['content'][:max_length]
    
    # Try Open Graph description
    og_desc = soup.find('meta', attrs={'property': 'og:description'})
    if og_desc and og_desc.get('content'):
        return og_desc['content'][:max_length]
    
    # Get first paragraph from main content
    main_content = soup.find(['main', 'article', '[role="main"]', '.content', '#content'])
    content_source = main_content if main_content else soup
    
    first_paragraph = content_source.find('p')
    if first_paragraph:
        text = first_paragraph.get_text(separator=' ', strip=True)
        if text:
            return text[:max_length]
    
    # Fallback: first max_length chars of cleaned text
    body_text = clean_html_text(html_content)
    return body_text[:max_length] if body_text else ""

