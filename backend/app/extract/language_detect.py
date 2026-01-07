"""
Language detection utilities for code snippets.
Provides best-guess language detection when not explicitly specified.
"""
from typing import Optional


# Common file extensions and their languages
LANGUAGE_PATTERNS = {
    'python': ['.py', 'python'],
    'javascript': ['.js', '.jsx', 'javascript', 'js'],
    'typescript': ['.ts', '.tsx', 'typescript', 'ts'],
    'java': ['.java', 'java'],
    'cpp': ['.cpp', '.cc', '.cxx', 'cpp', 'c++'],
    'c': ['.c', 'c'],
    'go': ['.go', 'go', 'golang'],
    'rust': ['.rs', 'rust'],
    'php': ['.php', 'php'],
    'ruby': ['.rb', 'ruby'],
    'swift': ['.swift', 'swift'],
    'kotlin': ['.kt', 'kotlin'],
    'scala': ['.scala', 'scala'],
    'html': ['.html', '.htm', 'html'],
    'css': ['.css', 'css'],
    'sql': ['.sql', 'sql'],
    'json': ['.json', 'json'],
    'xml': ['.xml', 'xml'],
    'yaml': ['.yaml', '.yml', 'yaml', 'yml'],
    'bash': ['.sh', '.bash', 'bash', 'shell', 'sh'],
    'powershell': ['.ps1', 'powershell', 'ps1'],
    'dockerfile': ['dockerfile', 'docker'],
    'markdown': ['.md', '.markdown', 'md', 'markdown'],
}


def detect_language_from_code(code: str, hint: Optional[str] = None) -> str:
    """
    Attempts to detect the programming language from code content.
    Uses heuristics and common patterns.
    
    Args:
        code: The code snippet
        hint: Optional hint (like file extension or class name)
        
    Returns:
        Detected language name (lowercase) or 'text' if unknown
    """
    code_lower = code.lower().strip()
    
    # Check hint first (from filename, class, etc.)
    if hint:
        hint_lower = hint.lower().strip('.').strip()
        for lang, patterns in LANGUAGE_PATTERNS.items():
            if any(pattern == hint_lower or hint_lower.endswith(pattern) for pattern in patterns):
                return lang
    
    # Heuristic detection based on code patterns
    # Python
    if any(pattern in code_lower[:200] for pattern in ['def ', 'import ', 'from ', 'if __name__', 'print(']):
        if 'def ' in code_lower or 'import ' in code_lower:
            return 'python'
    
    # JavaScript/TypeScript
    if any(pattern in code_lower[:200] for pattern in ['function ', 'const ', 'let ', 'var ', '=>', 'console.log']):
        if 'export ' in code_lower or 'require(' in code_lower:
            return 'javascript'
        if 'interface ' in code_lower or ': string' in code_lower or ': number' in code_lower:
            return 'typescript'
        return 'javascript'
    
    # Java
    if 'public class' in code_lower or 'public static void main' in code_lower or 'package ' in code_lower:
        return 'java'
    
    # C/C++
    if '#include' in code_lower:
        if any(pattern in code_lower for pattern in ['std::', 'namespace ', 'cout', 'using namespace']):
            return 'cpp'
        return 'c'
    
    # Go
    if 'package main' in code_lower or 'func main()' in code_lower or 'import (' in code_lower:
        return 'go'
    
    # Rust
    if 'fn main()' in code_lower and 'let ' in code_lower or 'use ' in code_lower:
        return 'rust'
    
    # SQL
    if any(pattern in code_lower[:200] for pattern in ['select ', 'from ', 'where ', 'insert into', 'create table']):
        return 'sql'
    
    # HTML
    if code_lower.strip().startswith('<!doctype') or code_lower.strip().startswith('<html'):
        return 'html'
    
    # JSON
    if (code_lower.strip().startswith('{') or code_lower.strip().startswith('[')) and '"' in code_lower:
        try:
            import json
            json.loads(code)
            return 'json'
        except:
            pass
    
    # CSS
    if '{' in code_lower and ':' in code_lower and any(char in code_lower for char in [';', '}', '@media']):
        return 'css'
    
    # Bash/Shell
    if code_lower.startswith('#!/bin/') or code_lower.startswith('#!/usr/bin/'):
        return 'bash'
    
    # Default
    return 'text'


def normalize_language_name(lang: str) -> str:
    """
    Normalizes language names to a standard format.
    
    Args:
        lang: Raw language name/identifier
        
    Returns:
        Normalized language name (lowercase, standard spelling)
    """
    if not lang:
        return 'text'
    
    lang_lower = lang.lower().strip()
    
    # Direct matches
    for standard_name, patterns in LANGUAGE_PATTERNS.items():
        if lang_lower in patterns:
            return standard_name
    
    # Common aliases
    alias_map = {
        'js': 'javascript',
        'ts': 'typescript',
        'py': 'python',
        'rb': 'ruby',
        'sh': 'bash',
        'shell': 'bash',
        'golang': 'go',
        'c++': 'cpp',
        'c#': 'csharp',
    }
    
    return alias_map.get(lang_lower, lang_lower)

