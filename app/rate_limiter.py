import time
import logging
from typing import Dict, Optional
from functools import wraps
from collections import defaultdict
from app.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.clients: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client"""
        now = time.time()
        
        # Remove old timestamps
        self.clients[client_id] = [
            ts for ts in self.clients[client_id]
            if now - ts < self.period
        ]
        
        # Check if limit exceeded
        if len(self.clients[client_id]) >= self.calls:
            return False
        
        # Record this request
        self.clients[client_id].append(now)
        return True
    
    def get_remaining(self, client_id: str) -> int:
        """Get remaining calls for client"""
        now = time.time()
        self.clients[client_id] = [
            ts for ts in self.clients[client_id]
            if now - ts < self.period
        ]
        return max(0, self.calls - len(self.clients[client_id]))
    
    def get_reset_time(self, client_id: str) -> Optional[int]:
        """Get reset time (unix timestamp)"""
        if not self.clients[client_id]:
            return None
        oldest = min(self.clients[client_id])
        return int(oldest + self.period)


# Global rate limiter instance
rate_limiter = RateLimiter(
    calls=settings.rate_limit_calls,
    period=settings.rate_limit_period
)
