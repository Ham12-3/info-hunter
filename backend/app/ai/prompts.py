"""
Prompt templates for AI enrichment tasks.
All prompts are designed to produce JSON output that can be validated with Pydantic.
"""
from typing import Dict, Any


def get_enrichment_prompt(item: Dict[str, Any]) -> str:
    """
    Generate prompt for enriching a knowledge item.
    Returns a prompt that instructs the model to output JSON.
    """
    title = item.get('title', '')
    body_text = item.get('body_text', '')
    code_snippets = item.get('code_snippets', [])
    
    # Build code snippets text
    code_text = ""
    for idx, snippet in enumerate(code_snippets[:5], 1):  # Limit to 5 snippets
        lang = snippet.get('language', 'unknown')
        code = snippet.get('code', '')[:500]  # Truncate long code
        context = snippet.get('context', '')
        code_text += f"\n--- Code Snippet {idx} ({lang}) ---\n"
        if context:
            code_text += f"Context: {context}\n"
        code_text += f"{code}\n"
    
    prompt = f"""Analyze the following programming knowledge item and extract structured information.

Title: {title}

Content:
{body_text[:2000]}

{code_text if code_text else "No code snippets present."}

Please provide a JSON response with the following structure:
{{
    "summary": "A concise 2-3 sentence summary of what this knowledge item teaches",
    "tags": ["tag1", "tag2", "tag3"],
    "primary_language": "Python" or null,
    "framework": "React" or null,
    "quality_score": 0.85,
    "code_snippets": [
        {{
            "intent": "What this code snippet demonstrates",
            "dependencies": ["library1", "library2"],
            "pitfalls": ["common mistake", "gotcha"]
        }}
    ]
}}

Rules:
- summary: Maximum 300 characters, clear and informative
- tags: 3-8 relevant tags (lowercase, hyphenated if needed)
- primary_language: Detected programming language or null
- framework: Detected framework/library or null if none
- quality_score: Float between 0.0 and 1.0 indicating content quality (consider clarity, completeness, accuracy)
- code_snippets: Array matching the input snippets, each with intent, dependencies, and pitfalls
- Dependencies: List actual libraries/packages needed
- Pitfalls: List common mistakes or gotchas when using this code

Output ONLY valid JSON, no markdown, no explanations."""

    return prompt


def get_ask_prompt(question: str, context_items: list[Dict[str, Any]]) -> str:
    """
    Generate prompt for answering a question using retrieved context.
    """
    # Build context from retrieved items
    context_parts = []
    for idx, item in enumerate(context_items, 1):
        context_parts.append(f"""
--- Source {idx} ---
Title: {item.get('title', '')}
Source: {item.get('source_name', '')}
URL: {item.get('source_url', '')}

{item.get('body_text', '')[:1000]}

Code snippets:
""")
        for snippet in item.get('code_snippets', [])[:2]:
            context_parts.append(f"```{snippet.get('language', '')}\n{snippet.get('code', '')[:300]}\n```\n")
    
    context_text = "\n".join(context_parts)
    
    prompt = f"""Answer the following question using ONLY the provided sources. 
Every claim must be backed by at least one source citation.

Question: {question}

Sources:
{context_text}

Provide your answer as a JSON object with this structure:
{{
    "answer": "Your answer with bullet points. Use [1], [2], etc. for citations.",
    "confidence": 0.85
}}

Rules:
- Answer must be clear and concise
- Use bullet points for clarity
- Every factual claim must include a citation like [1], [2]
- Citations refer to the source numbers above
- Confidence is a float 0.0-1.0 indicating how confident you are in the answer
- If the sources don't contain enough information, say so explicitly
- Maximum 500 words

Output ONLY valid JSON, no markdown, no explanations."""

    return prompt

