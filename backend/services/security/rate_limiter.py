"""
Rate Limiting and Cost Control Service
Prevents excessive Claude API usage and tracks costs
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict
import threading


class RateLimiter:
    """
    Rate limiter with cost tracking for Claude API calls
    
    Features:
    - Per-user request limits (hourly/daily)
    - Token usage tracking
    - Cost estimation
    - Graceful degradation
    """
    
    # Anthropic pricing (as of Dec 2024)
    # Claude Sonnet 4: $3 per million input tokens, $15 per million output tokens
    COST_PER_MILLION_INPUT_TOKENS = 3.0
    COST_PER_MILLION_OUTPUT_TOKENS = 15.0
    
    # Default limits (can be overridden per user)
    DEFAULT_REQUESTS_PER_HOUR = 10
    DEFAULT_REQUESTS_PER_DAY = 50
    DEFAULT_DAILY_COST_LIMIT_USD = 10.0  # $10/day max
    
    def __init__(self):
        # Track requests per user
        self._user_requests = defaultdict(list)  # user_id -> [timestamp, timestamp, ...]
        
        # Track token usage per user
        self._user_tokens = defaultdict(lambda: {'input': 0, 'output': 0})
        
        # Track costs per user
        self._user_costs = defaultdict(float)
        
        # Thread lock for thread-safety
        self._lock = threading.Lock()
        
        print("✅ Rate Limiter initialized")
        print(f"   Default limits: {self.DEFAULT_REQUESTS_PER_HOUR}/hour, {self.DEFAULT_REQUESTS_PER_DAY}/day")
        print(f"   Daily cost limit: ${self.DEFAULT_DAILY_COST_LIMIT_USD}")
    
    def check_rate_limit(
        self, 
        user_id: int,
        requests_per_hour: Optional[int] = None,
        requests_per_day: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user has exceeded rate limits
        
        Args:
            user_id: User ID
            requests_per_hour: Custom hourly limit (optional)
            requests_per_day: Custom daily limit (optional)
            
        Returns:
            (allowed: bool, reason: Optional[str])
            - (True, None) if allowed
            - (False, "reason") if rate limited
        """
        with self._lock:
            now = time.time()
            
            # Use custom limits or defaults
            hourly_limit = requests_per_hour or self.DEFAULT_REQUESTS_PER_HOUR
            daily_limit = requests_per_day or self.DEFAULT_REQUESTS_PER_DAY
            
            # Get user's request history
            user_history = self._user_requests[user_id]
            
            # Clean old requests (older than 24 hours)
            cutoff_time = now - 86400  # 24 hours
            user_history[:] = [ts for ts in user_history if ts > cutoff_time]
            
            # Count requests in last hour
            hour_ago = now - 3600
            requests_last_hour = sum(1 for ts in user_history if ts > hour_ago)
            
            # Count requests in last day
            requests_last_day = len(user_history)
            
            # Check hourly limit
            if requests_last_hour >= hourly_limit:
                return False, f"Hourly rate limit exceeded ({requests_last_hour}/{hourly_limit}). Try again in {int((3600 - (now - min([ts for ts in user_history if ts > hour_ago]))) / 60)} minutes."
            
            # Check daily limit
            if requests_last_day >= daily_limit:
                return False, f"Daily rate limit exceeded ({requests_last_day}/{daily_limit}). Resets at midnight UTC."
            
            return True, None
    
    def check_cost_limit(self, user_id: int, daily_cost_limit_usd: Optional[float] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if user has exceeded daily cost limit
        
        Returns:
            (allowed: bool, reason: Optional[str])
        """
        with self._lock:
            cost_limit = daily_cost_limit_usd or self.DEFAULT_DAILY_COST_LIMIT_USD
            
            # Get today's cost
            today_cost = self._get_today_cost(user_id)
            
            if today_cost >= cost_limit:
                return False, f"Daily cost limit exceeded (${today_cost:.2f}/${cost_limit:.2f}). Resets at midnight UTC."
            
            return True, None
    
    def record_request(self, user_id: int, input_tokens: int = 0, output_tokens: int = 0):
        """
        Record a successful API request with token usage
        
        Args:
            user_id: User ID
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
        """
        with self._lock:
            # Record timestamp
            self._user_requests[user_id].append(time.time())
            
            # Record token usage
            self._user_tokens[user_id]['input'] += input_tokens
            self._user_tokens[user_id]['output'] += output_tokens
            
            # Calculate and record cost
            cost = self._calculate_cost(input_tokens, output_tokens)
            self._user_costs[user_id] += cost
            
            print(f"   📊 Usage recorded for user {user_id}:")
            print(f"      Input tokens: {input_tokens}")
            print(f"      Output tokens: {output_tokens}")
            print(f"      Cost: ${cost:.4f}")
    
    def get_user_stats(self, user_id: int) -> Dict:
        """
        Get usage statistics for a user
        
        Returns:
            {
                'requests_last_hour': int,
                'requests_last_day': int,
                'total_input_tokens': int,
                'total_output_tokens': int,
                'total_cost_usd': float,
                'today_cost_usd': float
            }
        """
        with self._lock:
            now = time.time()
            hour_ago = now - 3600
            
            user_history = self._user_requests[user_id]
            
            # Clean old requests
            cutoff_time = now - 86400
            user_history[:] = [ts for ts in user_history if ts > cutoff_time]
            
            requests_last_hour = sum(1 for ts in user_history if ts > hour_ago)
            requests_last_day = len(user_history)
            
            tokens = self._user_tokens[user_id]
            
            return {
                'requests_last_hour': requests_last_hour,
                'requests_last_day': requests_last_day,
                'total_input_tokens': tokens['input'],
                'total_output_tokens': tokens['output'],
                'total_cost_usd': self._user_costs[user_id],
                'today_cost_usd': self._get_today_cost(user_id)
            }
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD for token usage"""
        input_cost = (input_tokens / 1_000_000) * self.COST_PER_MILLION_INPUT_TOKENS
        output_cost = (output_tokens / 1_000_000) * self.COST_PER_MILLION_OUTPUT_TOKENS
        return input_cost + output_cost
    
    def _get_today_cost(self, user_id: int) -> float:
        """
        Get cost for today only
        Note: In production, this should query a database with date filtering
        For now, we'll use total cost as a simplification
        """
        # TODO: Implement proper daily cost tracking with database
        return self._user_costs[user_id]
    
    def reset_daily_stats(self, user_id: int):
        """Reset daily statistics (called at midnight UTC in production)"""
        with self._lock:
            # Reset request history older than 24h
            now = time.time()
            cutoff = now - 86400
            self._user_requests[user_id][:] = [ts for ts in self._user_requests[user_id] if ts > cutoff]


# Global rate limiter instance (singleton)
_rate_limiter_instance = None

def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance"""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter()
    return _rate_limiter_instance
