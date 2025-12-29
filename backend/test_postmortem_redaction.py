"""
Test post-mortem redaction in action
"""
from services.llm_postmortem_analyzer import LLMPostMortemAnalyzer

# Mock error patterns with sensitive data
error_patterns = [
    {
        'pattern': 'Database connection failed',
        'count': 15,
        'example': 'ERROR: Connection to postgresql://admin:SuperSecret123@db.prod.com:5432/myapp failed',
        'logs': [
            'User john.doe@company.com attempted login with password=Test123!',
            'API call failed with token: Bearer eyJhbGc.payload.signature',
            'AWS Key leaked: AKIAIOSFODNN7EXAMPLE'
        ]
    },
    {
        'pattern': 'Authentication error',
        'count': 8,
        'example': 'Failed auth for user admin@internal.com with api_key=sk_live_51H7xK2L3M4N5'
    }
]

log_summary = {
    'total_errors': 23,
    'total_warnings': 45,
    'lookback_hours': 24
}

print("=" * 80)
print("TESTING POST-MORTEM REDACTION")
print("=" * 80)

print("\n📋 Original error patterns (WITH SECRETS):")
for pattern in error_patterns:
    print(f"\n  Pattern: {pattern['pattern']}")
    print(f"  Example: {pattern['example']}")
    if 'logs' in pattern:
        for log in pattern['logs'][:2]:
            print(f"    - {log}")

print("\n" + "=" * 80)
print("REDACTION IN ACTION")
print("=" * 80)

try:
    analyzer = LLMPostMortemAnalyzer()
    
    # This will redact automatically
    print("\nCalling analyzer.analyze_logs()...")
    result = analyzer.analyze_logs(error_patterns, log_summary)
    
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    if 'redaction_stats' in result:
        print(f"\n🔒 Redaction Summary:")
        for redaction_type, count in result['redaction_stats'].items():
            print(f"   {redaction_type}: {count} instances")
    
    print(f"\n📊 Analysis:")
    print(f"   Executive Summary: {result.get('executive_summary', 'N/A')[:150]}...")
    print(f"   Root Causes: {len(result.get('root_causes', []))}")
    print(f"   Recommendations: {len(result.get('recommendations', []))}")
    print(f"   Severity: {result.get('severity_assessment', 'N/A')}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
