"""
Rate limiting utilities for per-domain rate limiting.
Tracks request counts per domain and enforces limits.
"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple rate limiter that tracks requests per domain.
    Enforces maximum requests per time window.
    """
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)  # domain -> list of request timestamps
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return "unknown"
    
    def can_make_request(self, url: str) -> Tuple[bool, float]:
        """
        Check if a request can be made for the given URL.
        
        Args:
            url: URL to check
            
        Returns:
            Tuple of (can_make_request, wait_seconds)
        """
        domain = self._get_domain(url)
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests outside the window
        self.requests[domain] = [
            ts for ts in self.requests[domain]
            if ts > window_start
        ]
        
        # Check if under limit
        if len(self.requests[domain]) < self.max_requests:
            return True, 0.0
        
        # Calculate wait time until oldest request expires
        if self.requests[domain]:
            oldest_request = min(self.requests[domain])
            wait_until = oldest_request + timedelta(seconds=self.window_seconds)
            wait_seconds = max(0, (wait_until - now).total_seconds())
            return False, wait_seconds
        
        return True, 0.0
    
    def record_request(self, url: str):
        """Record that a request was made for the given URL."""
        domain = self._get_domain(url)
        self.requests[domain].append(datetime.now())
    
    def wait_if_needed(self, url: str):
        """
        Check rate limit and wait if necessary.
        
        Args:
            url: URL to check
        """
        can_request, wait_seconds = self.can_make_request(url)
        if not can_request:
            logger.info(f"Rate limit reached for {self._get_domain(url)}, waiting {wait_seconds:.2f}s")
            import time
            time.sleep(wait_seconds)

