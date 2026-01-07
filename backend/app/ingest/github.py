"""
GitHub connector for ingesting README files from repositories.
Uses GitHub REST API to search repositories and fetch README content.
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime
import logging
from app.ingest.base import BaseConnector
from app.config import settings
from app.utils.http_client import fetch_url

logger = logging.getLogger(__name__)


class GitHubConnector(BaseConnector):
    """
    Connector for ingesting GitHub repository README files.
    """
    
    def __init__(self):
        super().__init__("GitHub", "github")
        self.api_base = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Info-Hunter/1.0"
        }
        
        # Add token if available (for higher rate limits)
        if settings.github_token:
            self.headers["Authorization"] = f"token {settings.github_token}"
    
    def fetch_items(self, topics: Optional[List[str]] = None, keyword: Optional[str] = None, 
                   max_repos: int = 50, **kwargs) -> List[Dict]:
        """
        Fetch repositories and their README files.
        
        Args:
            topics: List of topics to search for (e.g., ['python', 'machine-learning'])
            keyword: Keyword to search in repository name/description
            max_repos: Maximum number of repositories to fetch
            
        Returns:
            List of raw item dictionaries
        """
        items = []
        
        try:
            # Build search query
            query_parts = []
            
            if topics:
                topic_query = " ".join([f"topic:{topic}" for topic in topics])
                query_parts.append(topic_query)
            
            if keyword:
                query_parts.append(keyword)
            
            if not query_parts:
                query_parts.append("stars:>100")  # Default: popular repos
            
            query = " ".join(query_parts)
            
            # Search repositories
            search_url = f"{self.api_base}/search/repositories"
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": min(max_repos, 100)  # GitHub API limit is 100
            }
            
            logger.info(f"Searching GitHub repositories: {query}")
            response = fetch_url(search_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            repos = data.get('items', [])[:max_repos]
            logger.info(f"Found {len(repos)} repositories")
            
            # Fetch README for each repository
            for repo in repos:
                try:
                    repo_data = self._fetch_repo_readme(repo)
                    if repo_data:
                        items.append(repo_data)
                except Exception as e:
                    logger.warning(f"Error fetching README for {repo.get('full_name')}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(items)} README files")
            return items
            
        except Exception as e:
            logger.error(f"Error fetching GitHub items: {e}", exc_info=True)
            return items
    
    def _fetch_repo_readme(self, repo: Dict) -> Optional[Dict]:
        """
        Fetch README content for a repository.
        
        Args:
            repo: Repository dictionary from GitHub API
            
        Returns:
            Raw item dictionary or None if README not found
        """
        repo_name = repo['full_name']
        readme_url = f"{self.api_base}/repos/{repo_name}/readme"
        
        try:
            response = fetch_url(readme_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            readme_data = response.json()
            
            # Decode base64 content
            import base64
            content_encoded = readme_data.get('content', '')
            content = base64.b64decode(content_encoded).decode('utf-8')
            
            # Extract metadata
            language = repo.get('language', '').lower() if repo.get('language') else None
            topics = repo.get('topics', [])
            
            # Detect framework from topics or description
            framework = None
            description = (repo.get('description') or '').lower()
            for fw in ['react', 'django', 'flask', 'express', 'spring', 'rails', 'vue', 'angular']:
                if fw in description or fw in topics:
                    framework = fw.capitalize()
                    break
            
            # Build item
            item = {
                'title': f"{repo_name}: {repo.get('description', 'No description')}",
                'content': content,
                'content_type': 'markdown',
                'source_url': repo['html_url'],
                'tags': topics,
                'primary_language': language,
                'framework': framework,
                'author': repo.get('owner', {}).get('login'),
                'licence': repo.get('license', {}).get('key') if repo.get('license') else None,
                'published_at': datetime.fromisoformat(repo['created_at'].replace('Z', '+00:00')) if repo.get('created_at') else None,
                'summary': repo.get('description'),
                # Additional metadata
                'github_stars': repo.get('stargazers_count', 0),
                'github_forks': repo.get('forks_count', 0),
            }
            
            return item
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # README not found, skip
                return None
            raise

