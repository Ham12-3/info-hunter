"""
Rate limiting utilities for AI API calls.
Implements token bucket or simple rate limiting for AI providers.
"""
import time
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AIRateLimiter:
    """
    Simple rate limiter for AI API calls.
    Tracks requests and enforces maximum requests per time window.
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
        self.requests: list[float] = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait if necessary to stay within rate limits."""
        async with self.lock:
            now = time.time()
            window_start = now - self.window_seconds
            
            # Remove old requests outside the window
            self.requests = [req_time for req_time in self.requests if req_time > window_start]
            
            # Check if we can make a request
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return
            
            # Calculate wait time
            if self.requests:
                oldest_request = min(self.requests)
                wait_until = oldest_request + self.window_seconds
                wait_seconds = max(0, wait_until - now)
                
                if wait_seconds > 0:
                    logger.info(f"Rate limit reached, waiting {wait_seconds:.2f}s")
                    await asyncio.sleep(wait_seconds)
                    # Retry after waiting
                    return await self.acquire()
            
            self.requests.append(time.time())


# Global rate limiter instances
openai_rate_limiter = AIRateLimiter(max_requests=60, window_seconds=60)  # 60 req/min
anthropic_rate_limiter = AIRateLimiter(max_requests=50, window_seconds=60)  # 50 req/min

