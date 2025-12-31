"""
Tests for Rate Limiter
"""
import time
from rate_limiter import RateLimiter


def test_rate_limit_hourly():
    """Test hourly rate limiting"""
    limiter = RateLimiter()
    user_id = 1
    
    # Allow first 10 requests (default limit)
    for i in range(10):
        allowed, reason = limiter.check_rate_limit(user_id)
        assert allowed, f"Request {i+1} should be allowed"
        limiter.record_request(user_id, input_tokens=100, output_tokens=50)
    
    # 11th request should be blocked
    allowed, reason = limiter.check_rate_limit(user_id)
    assert not allowed, "11th request should be rate limited"
    assert "Hourly rate limit exceeded" in reason
    
    print("✅ Hourly rate limit test passed")


def test_cost_tracking():
    """Test cost calculation and tracking"""
    limiter = RateLimiter()
    user_id = 2
    
    # Record request with known token counts
    input_tokens = 1000
    output_tokens = 500
    
    limiter.record_request(user_id, input_tokens=input_tokens, output_tokens=output_tokens)
    
    # Calculate expected cost
    expected_input_cost = (input_tokens / 1_000_000) * limiter.COST_PER_MILLION_INPUT_TOKENS
    expected_output_cost = (output_tokens / 1_000_000) * limiter.COST_PER_MILLION_OUTPUT_TOKENS
    expected_total = expected_input_cost + expected_output_cost
    
    stats = limiter.get_user_stats(user_id)
    
    assert stats['total_input_tokens'] == input_tokens
    assert stats['total_output_tokens'] == output_tokens
    assert abs(stats['total_cost_usd'] - expected_total) < 0.0001
    
    print(f"✅ Cost tracking test passed")
    print(f"   Input: {input_tokens} tokens = ${expected_input_cost:.4f}")
    print(f"   Output: {output_tokens} tokens = ${expected_output_cost:.4f}")
    print(f"   Total: ${expected_total:.4f}")


def test_user_stats():
    """Test user statistics retrieval"""
    limiter = RateLimiter()
    user_id = 3
    
    # Make 5 requests
    for i in range(5):
        limiter.record_request(user_id, input_tokens=1000, output_tokens=500)
    
    stats = limiter.get_user_stats(user_id)
    
    assert stats['requests_last_hour'] == 5
    assert stats['requests_last_day'] == 5
    assert stats['total_input_tokens'] == 5000
    assert stats['total_output_tokens'] == 2500
    
    print("✅ User stats test passed")
    print(f"   Stats: {stats}")


def test_cost_limit():
    """Test daily cost limit enforcement"""
    limiter = RateLimiter()
    user_id = 4
    
    # Set a low cost limit for testing
    cost_limit = 0.01  # $0.01
    
    # Make expensive request
    limiter.record_request(user_id, input_tokens=100000, output_tokens=50000)
    
    # Check if cost limit is exceeded
    allowed, reason = limiter.check_cost_limit(user_id, daily_cost_limit_usd=cost_limit)
    
    assert not allowed, "Should exceed cost limit"
    assert "cost limit exceeded" in reason.lower()
    
    print("✅ Cost limit test passed")
    print(f"   {reason}")


if __name__ == '__main__':
    print("="*80)
    print("RATE LIMITER TESTS")
    print("="*80)
    
    test_rate_limit_hourly()
    print()
    test_cost_tracking()
    print()
    test_user_stats()
    print()
    test_cost_limit()
    
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED!")
    print("="*80)
