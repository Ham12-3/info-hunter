"""
HTTP client with retry logic and backoff for web scraping.
"""
import requests
from typing import Optional, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging
from app.utils.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=60, window_seconds=60)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout))
)
def fetch_url(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> requests.Response:
    """
    Fetch URL with retry logic and exponential backoff.
    Respects rate limiting per domain.
    
    Args:
        url: URL to fetch
        headers: Optional HTTP headers
        timeout: Request timeout in seconds
        
    Returns:
        Response object
        
    Raises:
        requests.exceptions.RequestException: If all retries fail
    """
    # Wait if rate limited
    rate_limiter.wait_if_needed(url)
    
    # Default headers
    if headers is None:
        headers = {
            "User-Agent": "Info-Hunter/1.0 (Educational Research Tool)"
        }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Record successful request
        rate_limiter.record_request(url)
        
        return response
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request failed for {url}: {e}")
        raise

