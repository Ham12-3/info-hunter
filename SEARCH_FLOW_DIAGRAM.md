# Search Flow - Actual Implementation Process

## 🔍 Regular Search Flow (Keyword Search)

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: USER TYPES IN FRONTEND                                  │
│ File: frontend/app/page.tsx (line 66-85)                        │
│                                                                  │
│ User enters: "async python" in search box                       │
│ Clicks "Search" button                                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: FRONTEND BUILDS HTTP REQUEST                            │
│ File: frontend/app/page.tsx (line 73-83)                        │
│                                                                  │
│ const params = new URLSearchParams({                            │
│   q: "async python",                                            │
│   page: "1",                                                    │
│   size: "20"                                                    │
│ })                                                              │
│                                                                  │
│ fetch("http://localhost:8000/search?q=async+python&page=1&...") │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼ HTTP GET Request
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: FASTAPI ROUTE HANDLER                                   │
│ File: backend/app/api/routes.py (line 79-129)                   │
│                                                                  │
│ @router.get("/search")                                          │
│ async def search(                                               │
│   q: Optional[str] = "async python"                            │
│   page: int = 1                                                 │
│   size: int = 20                                                │
│ )                                                               │
│                                                                  │
│ → Parses query parameters                                       │
│ → Calls search_knowledge_items()                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: BUILD ELASTICSEARCH QUERY                               │
│ File: backend/app/api/search.py (line 14-135)                   │
│                                                                  │
│ build_search_query(                                             │
│   q="async python",                                             │
│   page=1,                                                       │
│   size=20                                                       │
│ )                                                               │
│                                                                  │
│ Creates Elasticsearch query:                                    │
│ {                                                               │
│   "query": {                                                    │
│     "bool": {                                                   │
│       "must": [{                                                │
│         "multi_match": {                                        │
│           "query": "async python",                              │
│           "fields": ["title^3", "body_text",                    │
│                      "code_snippets.code"]                      │
│         }                                                       │
│       }]                                                        │
│     }                                                           │
│   },                                                            │
│   "from": 0,  # (page-1) * size                                │
│   "size": 20,                                                   │
│   "sort": [{"published_at": "desc"}, "_score"],                │
│   "highlight": {                                                │
│     "fields": {"title": {}, "body_text": {...}}                │
│   }                                                             │
│ }                                                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: EXECUTE ELASTICSEARCH QUERY                             │
│ File: backend/app/api/search.py (line 159-175)                  │
│                                                                  │
│ es = get_elasticsearch_client()  # Gets ES client               │
│                                                                  │
│ response = es.search(                                           │
│   index="info_hunter_knowledge",                                │
│   body=search_request                                           │
│ )                                                               │
│                                                                  │
│ Elasticsearch searches index and returns:                       │
│ {                                                               │
│   "hits": {                                                     │
│     "total": {"value": 42},                                     │
│     "hits": [                                                   │
│       {                                                         │
│         "_id": "uuid-123",                                      │
│         "_score": 15.3,                                         │
│         "_source": {                                            │
│           "title": "Async Python Tutorial",                    │
│           "body_text": "...",                                   │
│           "code_snippets": [...],                               │
│           "source_url": "https://..."                           │
│         },                                                      │
│         "highlight": {                                          │
│           "title": ["<em>Async</em> Python Tutorial"],         │
│           "body_text": ["... <em>async</em> await ..."]        │
│         }                                                       │
│       },                                                        │
│       ... 19 more items ...                                     │
│     ]                                                           │
│   }                                                             │
│ }                                                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: FORMAT RESULTS                                          │
│ File: backend/app/api/search.py (line 176-200)                  │
│                                                                  │
│ items = []                                                      │
│ for hit in response['hits']['hits']:                            │
│   source = hit['_source']                                       │
│   source['highlight'] = hit.get('highlight')                    │
│   source['_score'] = hit['_score']                              │
│   items.append(source)                                          │
│                                                                  │
│ return {                                                        │
│   "items": items,  # Array of 20 knowledge items                │
│   "total": 42,                                                  │
│   "page": 1,                                                    │
│   "size": 20,                                                   │
│   "total_pages": 3                                              │
│ }                                                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼ JSON Response
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: FRONTEND RECEIVES & DISPLAYS                            │
│ File: frontend/app/page.tsx (line 84-85, 207-382)               │
│                                                                  │
│ const data = await response.json()                              │
│ setResults(data)  # Stores in React state                       │
│                                                                  │
│ → Renders results using JSX:                                    │
│   - Maps through results.items                                  │
│   - Shows title (with highlights)                               │
│   - Shows summary                                               │
│   - Shows code snippets preview                                 │
│   - Shows tags, language badges                                 │
│   - Shows source link                                           │
│   - Link to detail page                                         │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 Semantic/Hybrid Search Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1-3: Same as above (user types, frontend sends request)   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4A: GENERATE QUERY EMBEDDING (if semantic/hybrid)          │
│ File: backend/app/api/routes.py (line 100-114)                  │
│                                                                  │
│ if (semantic or hybrid) and q:                                  │
│   provider = get_ai_provider()  # OpenAI or Anthropic          │
│   query_embedding = asyncio.run(                                │
│     provider.generate_embedding("async python")                 │
│   )                                                             │
│                                                                  │
│ → Calls OpenAI API:                                             │
│   POST https://api.openai.com/v1/embeddings                     │
│   Body: {"model": "text-embedding-3-small",                    │
│          "input": "async python"}                               │
│                                                                  │
│ Returns: [0.123, -0.456, 0.789, ...]  (1536 numbers)          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4B: BUILD VECTOR QUERY                                     │
│ File: backend/app/api/search.py (line 48-65)                    │
│                                                                  │
│ if semantic:                                                    │
│   vector_query = {                                              │
│     "script_score": {                                           │
│       "query": {"match_all": {}},                               │
│       "script": {                                               │
│         "source": "cosineSimilarity(params.query_vector,        │
│                                      'embedding') + 1.0",       │
│         "params": {"query_vector": [0.123, -0.456, ...]}       │
│       }                                                         │
│     }                                                           │
│   }                                                             │
│   must_clauses.append(vector_query)                             │
│                                                                  │
│ if hybrid:                                                      │
│   should_clauses.append(keyword_query)                          │
│   should_clauses.append(vector_query)                           │
│   # Combines both scores                                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: EXECUTE ELASTICSEARCH VECTOR SEARCH                     │
│                                                                  │
│ Elasticsearch:                                                  │
│ 1. Computes cosine similarity for each document's embedding     │
│ 2. Scores documents based on vector similarity                  │
│ 3. (If hybrid) Combines with keyword match scores               │
│ 4. Returns top matches                                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼ (Same as regular search - format & display)
```

## 🤖 Ask Feature Flow (RAG)

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: USER ASKS QUESTION                                      │
│ File: frontend/app/page.tsx (line 83-107)                       │
│                                                                  │
│ User types: "How do I handle async errors in Python?"          │
│ Clicks "Ask" button                                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: FRONTEND SENDS POST REQUEST                             │
│ File: frontend/app/page.tsx (line 91-95)                        │
│                                                                  │
│ axios.post("http://localhost:8000/ask", {                       │
│   question: "How do I handle async errors in Python?",         │
│   top_k: 5,                                                     │
│   semantic: true                                                │
│ })                                                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼ HTTP POST
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: FASTAPI ASK ENDPOINT                                    │
│ File: backend/app/api/routes.py (line 238-250)                  │
│                                                                  │
│ @router.post("/ask")                                            │
│ async def ask(request: AskRequest)                              │
│   → Calls ask_question() function                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4A: GENERATE QUERY EMBEDDING                               │
│ File: backend/app/api/ask.py (line 42-49)                       │
│                                                                  │
│ provider = get_ai_provider()                                    │
│ query_embedding = await provider.generate_embedding(            │
│   "How do I handle async errors in Python?"                    │
│ )                                                               │
│                                                                  │
│ → Vector: [0.234, -0.123, 0.567, ...] (1536 dimensions)       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4B: RETRIEVE RELEVANT ITEMS (Hybrid Search)                │
│ File: backend/app/api/ask.py (line 52-63)                       │
│                                                                  │
│ search_results = search_knowledge_items(                        │
│   q="How do I handle async errors in Python?",                 │
│   semantic=True,                                                │
│   hybrid=True,                                                  │
│   query_embedding=[0.234, -0.123, ...],                        │
│   page=1,                                                       │
│   size=5  # top_k                                               │
│ )                                                               │
│                                                                  │
│ → Returns 5 most relevant knowledge items                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: BUILD RAG PROMPT                                        │
│ File: backend/app/ai/prompts.py (line 34-84)                    │
│                                                                  │
│ get_ask_prompt(question, context_items)                         │
│                                                                  │
│ Creates prompt:                                                 │
│ """                                                            │
│ Answer the following question using ONLY the provided sources. │
│                                                                 │
│ Question: How do I handle async errors in Python?              │
│                                                                 │
│ Sources:                                                        │
│ --- Source 1 ---                                                │
│ Title: Python Async Error Handling                             │
│ Source: Stack Overflow                                          │
│ URL: https://stackoverflow.com/...                              │
│                                                                 │
│ [Body text from item 1...]                                      │
│ ```python                                                       │
│ async def example():                                            │
│   try:                                                          │
│     await some_async()                                          │
│   except Exception as e:                                        │
│     print(e)                                                    │
│ ```                                                             │
│                                                                 │
│ --- Source 2 ---                                                │
│ ... (items 2-5)                                                 │
│                                                                 │
│ Provide JSON: {"answer": "...", "confidence": 0.85}            │
│ """                                                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: RATE LIMIT CHECK                                        │
│ File: backend/app/api/ask.py (line 81-82)                       │
│                                                                  │
│ await rate_limiter.acquire()  # Waits if at limit              │
│ # Tracks: 60 requests/minute for OpenAI                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: CALL AI TO GENERATE ANSWER                              │
│ File: backend/app/api/ask.py (line 84-89)                       │
│ File: backend/app/ai/provider.py (line 37-54)                   │
│                                                                  │
│ OpenAI Provider:                                                │
│ POST https://api.openai.com/v1/chat/completions                │
│ {                                                               │
│   "model": "gpt-4o-mini",                                       │
│   "messages": [                                                 │
│     {"role": "system", "content": "You are a helpful..."},     │
│     {"role": "user", "content": prompt}                         │
│   ],                                                            │
│   "temperature": 0.3,                                           │
│   "max_tokens": 1000,                                           │
│   "response_format": {"type": "json_object"}                    │
│ }                                                               │
│                                                                  │
│ Returns:                                                        │
│ {                                                               │
│   "answer": "To handle async errors in Python:\n                │
│              • Use try/except blocks [1]\n                      │
│              • await the async call inside try [1]\n            │
│              • Handle specific exceptions [2]",                 │
│   "confidence": 0.92                                            │
│ }                                                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: PARSE & VALIDATE RESPONSE                               │
│ File: backend/app/api/ask.py (line 91-108)                      │
│                                                                  │
│ answer_data = json.loads(response_text)                         │
│ answer_obj = AskResponse(**answer_data)  # Pydantic validation  │
│                                                                  │
│ # Build citations                                               │
│ citations = []                                                  │
│ for idx, item in enumerate(items, 1):                           │
│   citations.append({                                            │
│     "number": idx,                                              │
│     "title": item['title'],                                     │
│     "source_url": item['source_url'],                           │
│     "source_name": item['source_name']                          │
│   })                                                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼ JSON Response
┌─────────────────────────────────────────────────────────────────┐
│ STEP 9: FRONTEND DISPLAYS ANSWER                                │
│ File: frontend/app/page.tsx (line 96-103, 183-206)              │
│                                                                  │
│ setAskResult(response.data)                                     │
│                                                                  │
│ Renders:                                                        │
│ - Answer text with citations [1], [2] as superscript           │
│ - Confidence score: "92%"                                       │
│ - Sources list with clickable links                             │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 Data Flow Summary

### Keyword Search (Fast, No AI):
```
User Input → FastAPI → Elasticsearch Query → Results → Frontend
Time: ~100-500ms
```

### Semantic Search (Requires Embeddings):
```
User Input → Generate Embedding (AI API) → Vector Search → Results → Frontend
Time: ~1-3 seconds (AI embedding call adds latency)
```

### Hybrid Search (Best of Both):
```
User Input → Generate Embedding → 
  ┌→ Keyword Match Score
  └→ Vector Similarity Score
  → Combined Ranking → Results → Frontend
Time: ~1-3 seconds
```

### Ask Feature (Full RAG):
```
Question → Embedding → Hybrid Search (top 5) → 
  Build Prompt with Context → AI Generation → 
  Parse Answer → Add Citations → Frontend
Time: ~3-8 seconds (multiple AI calls)
```

## 🔑 Key Files & Functions

| Action | File | Function/Method |
|--------|------|----------------|
| Frontend search | `frontend/app/page.tsx` | `search()` (line 66) |
| API route | `backend/app/api/routes.py` | `search()` (line 79) |
| Query builder | `backend/app/api/search.py` | `build_search_query()` (line 14) |
| ES search | `backend/app/api/search.py` | `search_knowledge_items()` (line 138) |
| Embedding gen | `backend/app/ai/provider.py` | `generate_embedding()` (line 44) |
| Ask endpoint | `backend/app/api/routes.py` | `ask()` (line 238) |
| RAG logic | `backend/app/api/ask.py` | `ask_question()` (line 17) |
| AI prompt | `backend/app/ai/prompts.py` | `get_ask_prompt()` (line 34) |

This shows the actual code execution path from user input to displayed results!

