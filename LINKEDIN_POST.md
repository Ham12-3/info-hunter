# LinkedIn Post - Info Hunter Application

---

I just finished building Info Hunter, a search engine that aggregates programming knowledge from across the web.

The problem? Developers waste hours jumping between GitHub, Stack Overflow, and documentation sites to find answers. Info Hunter solves this by collecting code snippets and explanations from multiple sources and making them searchable in one place.

Here's what it does:

It scrapes and indexes content from GitHub READMEs, Stack Overflow answers, and programming blog feeds. Everything gets stored in PostgreSQL and indexed in Elasticsearch for fast retrieval.

The search is smart. You can do keyword searches, semantic searches using AI embeddings, or hybrid searches that combine both approaches. There's even an "Ask" feature that uses RAG to answer questions with citations.

Behind the scenes, it uses AI to enrich content with better summaries, tags, and quality scores. The whole thing runs on FastAPI with Celery for background jobs, and the frontend is built with Next.js and a sleek glassmorphism design.

The architecture is clean: proper API connectors, rate limiting, retry logic, and full attribution. Nothing is scraped without permission; it uses official APIs where possible.

Built with Python, TypeScript, Elasticsearch, and Docker. The UI features smooth animations and a modern glassmorphic design.

The full codebase is open source and available on GitHub. Feel free to check it out, star it if you find it useful, or contribute if you'd like to help improve it.

GitHub: [your-repo-url-here]

If you're interested in seeing how it works or want to discuss the tech stack, drop me a message.

#WebDevelopment #Python #NextJS #AI #SoftwareEngineering #FullStackDevelopment #Elasticsearch #OpenAI #MachineLearning #OpenSource

---

