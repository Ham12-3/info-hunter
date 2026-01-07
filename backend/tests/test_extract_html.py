"""
Unit tests for HTML extraction utilities.
"""
import pytest
from app.extract.html import extract_code_blocks, clean_html_text, generate_summary


def test_extract_code_blocks_pre_code():
    """Test extraction of code blocks from <pre><code> elements."""
    html = """
    <p>Some explanation text.</p>
    <pre><code class="language-python">
def hello():
    print("Hello")
    </code></pre>
    <p>More text.</p>
    """
    blocks = extract_code_blocks(html)
    
    assert len(blocks) == 1
    assert blocks[0]["language"] == "python"
    assert "def hello()" in blocks[0]["code"]


def test_extract_code_blocks_class_detection():
    """Test language detection from class names."""
    html = """
    <pre><code class="language-javascript">
    const x = 5;
    </code></pre>
    """
    blocks = extract_code_blocks(html)
    
    assert len(blocks) == 1
    assert blocks[0]["language"] == "javascript"


def test_clean_html_text():
    """Test cleaning of HTML to extract plain text."""
    html = """
    <html>
    <head><title>Test</title></head>
    <body>
    <nav>Navigation</nav>
    <main>
    <p>This is important content.</p>
    <p>More content here.</p>
    </main>
    <footer>Footer text</footer>
    </body>
    </html>
    """
    text = clean_html_text(html)
    
    assert "important content" in text
    assert "Navigation" not in text
    assert "Footer text" not in text


def test_generate_summary_meta_description():
    """Test summary generation from meta description."""
    html = """
    <html>
    <head>
    <meta name="description" content="This is the meta description.">
    </head>
    <body>
    <p>Body content here.</p>
    </body>
    </html>
    """
    summary = generate_summary(html)
    
    assert "meta description" in summary.lower()


def test_extract_code_blocks_multiple():
    """Test extraction of multiple code blocks."""
    html = """
    <pre><code class="python">code1</code></pre>
    <pre><code class="javascript">code2</code></pre>
    """
    blocks = extract_code_blocks(html)
    
    assert len(blocks) >= 2
    languages = [b["language"] for b in blocks]
    assert "python" in languages
    assert "javascript" in languages

