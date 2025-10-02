"""Rate limiting middleware using token bucket algorithm."""

import logging
import time
from typing import Optional, Dict, Callable
from collections import defaultdict
import asyncio

from fastapi import Request, HTTPException, status

from kubeagentic.exceptions import RateLimitError

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        async with self.lock:
            now = time.time()
            # Refill tokens based on time passed
            time_passed = now - self.last_update
            self.tokens = min(
                self.capacity,
                self.tokens + time_passed * self.refill_rate
            )
            self.last_update = now

            # Try to consume
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def get_wait_time(self, tokens: int = 1) -> float:
        """
        Get time to wait until tokens are available.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Wait time in seconds
        """
        async with self.lock:
            now = time.time()
            time_passed = now - self.last_update
            current_tokens = min(
                self.capacity,
                self.tokens + time_passed * self.refill_rate
            )
            
            if current_tokens >= tokens:
                return 0.0
            
            tokens_needed = tokens - current_tokens
            return tokens_needed / self.refill_rate


class RateLimiter:
    """Rate limiter with multiple strategies."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None,
        storage: str = "memory",
        redis_url: Optional[str] = None,
        key_prefix: str = "ratelimit:",
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst size (defaults to requests_per_minute)
            storage: Storage backend ('memory' or 'redis')
            redis_url: Redis URL (if using Redis)
            key_prefix: Key prefix for Redis
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or requests_per_minute
        self.storage = storage
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        
        # In-memory storage
        self.buckets: Dict[str, TokenBucket] = {}
        self._redis = None
        
        # Calculate refill rate (tokens per second)
        self.refill_rate = requests_per_minute / 60.0
        
        logger.info(
            f"RateLimiter initialized: {requests_per_minute} req/min, "
            f"burst={self.burst_size}, storage={storage}"
        )

    async def _get_redis(self):
        """Get or create Redis connection."""
        if self._redis is None and self.storage == "redis":
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(
                    self.redis_url or "redis://localhost:6379",
                    encoding="utf-8",
                    decode_responses=True,
                )
                await self._redis.ping()
                logger.info("Redis connection established for rate limiting")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                logger.warning("Falling back to in-memory rate limiting")
                self.storage = "memory"
        return self._redis

    async def check_rate_limit(
        self,
        key: str,
        cost: int = 1,
    ) -> bool:
        """
        Check if request is allowed.
        
        Args:
            key: Identifier (e.g., user_id, IP address)
            cost: Cost in tokens (default 1)
            
        Returns:
            True if allowed, False otherwise
            
        Raises:
            RateLimitError: If rate limit exceeded
        """
        if self.storage == "redis":
            allowed = await self._check_redis(key, cost)
        else:
            allowed = await self._check_memory(key, cost)
        
        if not allowed:
            wait_time = await self.get_wait_time(key, cost)
            raise RateLimitError(
                f"Rate limit exceeded. Try again in {wait_time:.1f} seconds."
            )
        
        return True

    async def _check_memory(self, key: str, cost: int) -> bool:
        """Check rate limit using in-memory storage."""
        if key not in self.buckets:
            self.buckets[key] = TokenBucket(self.burst_size, self.refill_rate)
        
        bucket = self.buckets[key]
        return await bucket.consume(cost)

    async def _check_redis(self, key: str, cost: int) -> bool:
        """Check rate limit using Redis."""
        redis = await self._get_redis()
        if not redis:
            return await self._check_memory(key, cost)
        
        redis_key = f"{self.key_prefix}{key}"
        
        try:
            # Use Redis with sliding window
            now = time.time()
            window_start = now - 60  # 1 minute window
            
            # Remove old entries
            await redis.zremrangebyscore(redis_key, 0, window_start)
            
            # Count requests in window
            count = await redis.zcard(redis_key)
            
            if count < self.requests_per_minute:
                # Add current request
                await redis.zadd(redis_key, {str(now): now})
                await redis.expire(redis_key, 60)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fallback to memory
            return await self._check_memory(key, cost)

    async def get_wait_time(self, key: str, cost: int = 1) -> float:
        """Get time to wait until request is allowed."""
        if self.storage == "memory" and key in self.buckets:
            return await self.buckets[key].get_wait_time(cost)
        return 60.0  # Default 1 minute

    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        if self.storage == "memory" and key in self.buckets:
            del self.buckets[key]
        elif self.storage == "redis":
            redis = await self._get_redis()
            if redis:
                await redis.delete(f"{self.key_prefix}{key}")

    async def close(self):
        """Close connections."""
        if self._redis:
            await self._redis.close()
            logger.info("Rate limiter Redis connection closed")


def create_rate_limiter(
    requests_per_minute: int = 60,
    burst_size: Optional[int] = None,
    storage: str = "memory",
    redis_url: Optional[str] = None,
    get_key: Optional[Callable] = None,
) -> Callable:
    """
    Create rate limiting middleware.
    
    Args:
        requests_per_minute: Maximum requests per minute
        burst_size: Maximum burst size
        storage: Storage backend
        redis_url: Redis URL
        get_key: Function to extract key from request
        
    Returns:
        Middleware function
    """
    limiter = RateLimiter(
        requests_per_minute=requests_per_minute,
        burst_size=burst_size,
        storage=storage,
        redis_url=redis_url,
    )
    
    async def middleware(request: Request, call_next):
        """Rate limiting middleware."""
        # Extract key
        if get_key:
            key = get_key(request)
        else:
            # Default: use client IP
            key = request.client.host if request.client else "unknown"
        
        # Check rate limit
        try:
            await limiter.check_rate_limit(key)
        except RateLimitError as e:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(e),
                headers={"Retry-After": "60"},
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            int(limiter.buckets.get(key, limiter.buckets.get("default", TokenBucket(limiter.burst_size, limiter.refill_rate))).tokens)
            if limiter.storage == "memory" else "N/A"
        )
        
        return response
    
    return middleware


async def rate_limit_dependency(
    request: Request,
    limiter: RateLimiter,
    key_extractor: Optional[Callable] = None,
) -> None:
    """
    FastAPI dependency for rate limiting.
    
    Args:
        request: FastAPI request
        limiter: RateLimiter instance
        key_extractor: Optional function to extract key
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    # Extract key
    if key_extractor:
        key = key_extractor(request)
    else:
        key = request.client.host if request.client else "unknown"
    
    # Check rate limit
    try:
        await limiter.check_rate_limit(key)
    except RateLimitError as e:
        wait_time = await limiter.get_wait_time(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
            headers={
                "Retry-After": str(int(wait_time)),
                "X-RateLimit-Limit": str(limiter.requests_per_minute),
                "X-RateLimit-Reset": str(int(time.time() + wait_time)),
            },
        ) 