"""
Unit tests for Markdown extraction utilities.
"""
import pytest
from app.extract.markdown import extract_code_blocks, extract_body_text, generate_summary


def test_extract_code_blocks_basic():
    """Test extraction of basic fenced code blocks."""
    markdown = """
Here is some explanation.

```python
def hello():
    print("Hello, World!")
```

More text here.
"""
    blocks = extract_code_blocks(markdown)
    
    assert len(blocks) == 1
    assert blocks[0]["language"] == "python"
    assert "def hello()" in blocks[0]["code"]
    assert "print" in blocks[0]["code"]


def test_extract_code_blocks_multiple():
    """Test extraction of multiple code blocks."""
    markdown = """
First code:

```javascript
const x = 5;
```

Second code:

```python
x = 5
```
"""
    blocks = extract_code_blocks(markdown)
    
    assert len(blocks) == 2
    assert blocks[0]["language"] == "javascript"
    assert blocks[1]["language"] == "python"


def test_extract_code_blocks_no_language():
    """Test extraction of code blocks without language specification."""
    markdown = """
```
some code here
```
"""
    blocks = extract_code_blocks(markdown)
    
    assert len(blocks) == 1
    assert blocks[0]["language"] == "text"
    assert "some code here" in blocks[0]["code"]


def test_extract_body_text():
    """Test extraction of body text without code blocks."""
    markdown = """
# Title

This is some text.

```python
code here
```

More text after code.
"""
    body = extract_body_text(markdown)
    
    assert "code here" not in body
    assert "This is some text" in body
    assert "More text after code" in body


def test_generate_summary():
    """Test summary generation from Markdown."""
    markdown = """
# Article Title

This is the first paragraph that should be used as a summary.
It contains important information.

More paragraphs here...
"""
    summary = generate_summary(markdown)
    
    assert len(summary) <= 300
    assert "first paragraph" in summary.lower()


def test_extract_code_blocks_with_context():
    """Test that context is captured before code blocks."""
    markdown = """
Before the code block, we have this explanation text
that provides context about what the code does.

```python
x = 1
```
"""
    blocks = extract_code_blocks(markdown)
    
    assert len(blocks) == 1
    assert blocks[0]["context"]  # Should have some context
    assert "explanation" in blocks[0]["context"].lower() or "context" in blocks[0]["context"].lower()

