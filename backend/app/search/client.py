"""
Elasticsearch client setup and connection management.
"""
from elasticsearch import Elasticsearch
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Global Elasticsearch client instance
es_client: Elasticsearch = None


def get_elasticsearch_client() -> Elasticsearch:
    """
    Get or create Elasticsearch client instance.
    Returns a singleton client for the application.
    """
    global es_client
    if es_client is None:
        es_client = Elasticsearch(
            [settings.elasticsearch_url],
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
        # Test connection
        try:
            if es_client.ping():
                logger.info(f"Connected to Elasticsearch at {settings.elasticsearch_url}")
            else:
                logger.error("Failed to connect to Elasticsearch")
        except Exception as e:
            logger.error(f"Error connecting to Elasticsearch: {e}")
    return es_client

