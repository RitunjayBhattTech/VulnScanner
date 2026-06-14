import asyncio
import time
import logging
from contextlib import asynccontextmanager

from backend.config import settings

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter implementation.
    Tokens are replenished at max_rate per second.
    burst defines the maximum number of tokens in the bucket.
    """

    def __init__(self, max_rate: int = None, burst: int = None):
        self.max_rate = max_rate or settings.MAX_SCAN_RATE
        self.burst = burst or self.max_rate
        self.tokens = float(self.burst)
        self.last_refill = time.monotonic()
        self._semaphore = asyncio.Semaphore(1)

    def _refill(self):
        """Replenish tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(float(self.burst), self.tokens + elapsed * self.max_rate)
        self.last_refill = now

    async def acquire(self, tokens: float = 1.0) -> float:
        """
        Acquire tokens from the bucket.
        Returns the wait time in seconds (0 if no wait needed).
        """
        async with self._semaphore:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0
            else:
                wait_time = (tokens - self.tokens) / self.max_rate
                self.tokens = 0.0
                return wait_time

    @asynccontextmanager
    async def limit(self, tokens: float = 1.0):
        """Async context manager that waits for rate limit capacity."""
        wait_time = await self.acquire(tokens)
        if wait_time > 0:
            logger.debug(f"Rate limiter waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        yield


# Global rate limiter instance
global_rate_limiter = TokenBucketRateLimiter()