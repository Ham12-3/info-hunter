"""
Unit tests for language detection utilities.
"""
import pytest
from app.extract.language_detect import detect_language_from_code, normalize_language_name


def test_detect_language_python():
    """Test Python language detection."""
    code = """
def hello():
    print("Hello, World!")
"""
    lang = detect_language_from_code(code)
    assert lang == "python"


def test_detect_language_javascript():
    """Test JavaScript language detection."""
    code = """
function hello() {
    console.log("Hello");
}
"""
    lang = detect_language_from_code(code)
    assert lang == "javascript"


def test_detect_language_with_hint():
    """Test language detection with filename hint."""
    code = "some code"
    lang = detect_language_from_code(code, hint="test.py")
    assert lang == "python"


def test_detect_language_sql():
    """Test SQL language detection."""
    code = """
SELECT * FROM users
WHERE id = 1
"""
    lang = detect_language_from_code(code)
    assert lang == "sql"


def test_normalize_language_name():
    """Test language name normalization."""
    assert normalize_language_name("JavaScript") == "javascript"
    assert normalize_language_name("js") == "javascript"
    assert normalize_language_name("py") == "python"
    assert normalize_language_name("c++") == "cpp"
    assert normalize_language_name("unknown") == "unknown"

