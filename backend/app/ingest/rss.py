"""
RSS connector for ingesting programming blog posts and articles.
Reads RSS feed configuration from YAML and fetches articles.
"""
import feedparser
from typing import List, Dict, Optional
from datetime import datetime
import logging
import yaml
from pathlib import Path
from app.ingest.base import BaseConnector
from app.utils.http_client import fetch_url

logger = logging.getLogger(__name__)


class RSSConnector(BaseConnector):
    """
    Connector for ingesting RSS feeds.
    """
    
    def __init__(self, feeds_config_path: Optional[str] = None):
        """
        Initialize RSS connector.
        
        Args:
            feeds_config_path: Path to YAML file with RSS feed configurations
        """
        super().__init__("RSS Feeds", "rss")
        self.feeds_config_path = feeds_config_path or "feeds.yaml"
        self.feeds = self._load_feeds_config()
    
    def _load_feeds_config(self) -> List[Dict]:
        """
        Load RSS feed configuration from YAML file.
        
        Returns:
            List of feed configuration dictionaries
        """
        try:
            config_path = Path(self.feeds_config_path)
            if not config_path.exists():
                # Create default config if it doesn't exist
                default_config = {
                    'feeds': [
                        {
                            'url': 'https://realpython.com/atom.xml',
                            'name': 'Real Python',
                            'enabled': True
                        },
                        {
                            'url': 'https://dev.to/feed',
                            'name': 'DEV Community',
                            'enabled': True
                        },
                        {
                            'url': 'https://blog.logrocket.com/feed/',
                            'name': 'LogRocket Blog',
                            'enabled': True
                        }
                    ]
                }
                with open(config_path, 'w') as f:
                    yaml.dump(default_config, f, default_flow_style=False)
                logger.info(f"Created default feeds config at {config_path}")
                return default_config['feeds']
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('feeds', [])
                
        except Exception as e:
            logger.error(f"Error loading feeds config: {e}")
            return []
    
    def fetch_items(self, max_items_per_feed: int = 20, **kwargs) -> List[Dict]:
        """
        Fetch items from all configured RSS feeds.
        
        Args:
            max_items_per_feed: Maximum items to fetch per feed
            
        Returns:
            List of raw item dictionaries
        """
        items = []
        
        enabled_feeds = [f for f in self.feeds if f.get('enabled', True)]
        logger.info(f"Processing {len(enabled_feeds)} RSS feeds")
        
        for feed_config in enabled_feeds:
            try:
                feed_url = feed_config['url']
                feed_name = feed_config.get('name', 'Unknown Feed')
                
                logger.info(f"Fetching RSS feed: {feed_name} ({feed_url})")
                feed_items = self._fetch_feed(feed_url, feed_name, max_items_per_feed)
                items.extend(feed_items)
                
            except Exception as e:
                logger.error(f"Error fetching feed {feed_config.get('name')}: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(items)} items from RSS feeds")
        return items
    
    def _fetch_feed(self, feed_url: str, feed_name: str, max_items: int) -> List[Dict]:
        """
        Fetch and parse a single RSS feed.
        
        Args:
            feed_url: RSS feed URL
            feed_name: Human-readable feed name
            max_items: Maximum items to fetch
            
        Returns:
            List of raw item dictionaries
        """
        items = []
        
        try:
            # Fetch feed
            response = fetch_url(feed_url, timeout=30)
            response.raise_for_status()
            
            # Parse feed
            feed = feedparser.parse(response.content)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")
            
            # Process entries
            entries = feed.entries[:max_items]
            
            for entry in entries:
                try:
                    item = self._process_entry(entry, feed_name, feed_url)
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.warning(f"Error processing RSS entry {entry.get('link')}: {e}")
                    continue
            
            return items
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")
            return items
    
    def _process_entry(self, entry, feed_name: str, feed_url: str) -> Optional[Dict]:
        """
        Process an RSS entry into a raw item dictionary.
        
        Args:
            entry: Feed entry from feedparser
            feed_name: Name of the feed
            feed_url: URL of the feed
            
        Returns:
            Raw item dictionary or None if processing fails
        """
        # Get content (prefer content over summary)
        content = entry.get('content')
        if content:
            if isinstance(content, list) and len(content) > 0:
                content = content[0].get('value', '')
            elif isinstance(content, dict):
                content = content.get('value', '')
        
        if not content:
            content = entry.get('summary', '')
        
        # Fetch full article if link is available
        link = entry.get('link', '')
        if link:
            try:
                # Try to fetch full content
                response = fetch_url(link, timeout=30)
                response.raise_for_status()
                content = response.text
            except Exception:
                # Use summary if fetch fails
                pass
        
        # Parse published date
        published_at = None
        if entry.get('published_parsed'):
            try:
                published_at = datetime(*entry.published_parsed[:6])
            except Exception:
                pass
        
        # Extract tags
        tags = []
        if entry.get('tags'):
            tags = [tag.get('term', '') for tag in entry.tags if tag.get('term')]
        
        # Build item
        item = {
            'title': entry.get('title', 'Untitled'),
            'content': content or '',
            'content_type': 'html',
            'source_url': link or feed_url,
            'tags': tags,
            'author': entry.get('author'),
            'published_at': published_at,
            'summary': entry.get('summary', ''),
            'source_name': feed_name,
        }
        
        return item

