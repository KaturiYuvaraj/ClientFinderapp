import time
from collections import defaultdict
from typing import Optional
from fastapi import HTTPException, status, Request
from app.config import settings

class SlidingWindowRateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.limit = requests_per_minute
        self.window = 60.0  # seconds
        self.requests = defaultdict(list)

    def is_rate_limited(self, identifier: str) -> bool:
        now = time.time()
        timestamps = self.requests[identifier]
        
        # Purge old timestamps outside window
        self.requests[identifier] = [ts for ts in timestamps if now - ts < self.window]
        
        if len(self.requests[identifier]) >= self.limit:
            return True
            
        self.requests[identifier].append(now)
        return False

rate_limiter = SlidingWindowRateLimiter(requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)

def check_rate_limit(request: Request, user_id: Optional[str] = None):
    # Use user_id if authenticated, otherwise client IP
    ident = f"user_{user_id}" if user_id else f"ip_{request.client.host if request.client else 'unknown'}"
    if rate_limiter.is_rate_limited(ident):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {settings.RATE_LIMIT_PER_MINUTE} requests per minute allowed."
        )
