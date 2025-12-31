"""
Test rate limiting integration with post-mortem analyzer
"""
from services.llm_postmortem_analyzer import LLMPostMortemAnalyzer

print("="*80)
print("RATE LIMITING INTEGRATION TEST")
print("="*80)

# Mock data
mock_patterns = [{
    'pattern': 'Test error',
    'count': 5,
    'example': 'ERROR: Test error occurred'
}]

mock_summary = {
    'total_errors': 5,
    'total_warnings': 0,
    'lookback_hours': 24
}

analyzer = LLMPostMortemAnalyzer()
user_id = 999  # Test user

print(f"\n🧪 Testing rate limits for user {user_id}...")
print(f"   Default limit: 10 requests/hour\n")

# Make 10 requests (should all succeed)
for i in range(10):
    print(f"Request {i+1}/10...", end=" ")
    result = analyzer.analyze_logs_with_rate_limiting(mock_patterns, mock_summary, user_id)
    
    if result.get('rate_limit_exceeded'):
        print(f"❌ FAILED - Rate limited at request {i+1}")
        break
    else:
        print("✅ Allowed")

# 11th request should be rate limited
print(f"\nRequest 11 (should be rate limited)...", end=" ")
result = analyzer.analyze_logs_with_rate_limiting(mock_patterns, mock_summary, user_id)

if result.get('rate_limit_exceeded'):
    print("✅ CORRECTLY RATE LIMITED")
    print(f"   Reason: {result.get('rate_limit_reason')}")
    print(f"   Fallback mode: {result.get('fallback_mode')}")
else:
    print("❌ FAILED - Should have been rate limited")

# Check usage stats
from services.security.rate_limiter import get_rate_limiter
limiter = get_rate_limiter()
stats = limiter.get_user_stats(user_id)

print(f"\n📊 Usage Statistics:")
print(f"   Requests last hour: {stats['requests_last_hour']}")
print(f"   Requests last day: {stats['requests_last_day']}")
print(f"   Total cost: ${stats['total_cost_usd']:.4f}")

print("\n" + "="*80)
print("✅ RATE LIMITING INTEGRATION TEST COMPLETE!")
print("="*80)
