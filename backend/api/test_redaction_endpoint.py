"""
Test endpoint to demonstrate redaction in action
"""
from fastapi import APIRouter
from services.llm_postmortem_analyzer import LLMPostMortemAnalyzer

router = APIRouter(prefix="/api/test", tags=["Test"])


@router.get("/redaction-demo")
async def redaction_demo():
    """
    Demonstrate PII/Secrets redaction with mock data
    """
    # Mock error patterns with sensitive data
    mock_patterns = [
        {
            'pattern': 'Database connection failed',
            'count': 15,
            'example': 'ERROR: Connection to postgresql://admin:SuperSecret123@db.prod.com:5432/myapp failed',
            'logs': [
                'User john.doe@company.com attempted login with password=Test123!',
                'API call failed with Bearer eyJhbGc.payload.signature',
                'AWS credentials leaked: AKIAIOSFODNN7EXAMPLE'
            ]
        }
    ]
    
    mock_summary = {
        'total_errors': 15,
        'total_warnings': 30,
        'lookback_hours': 24
    }
    
    analyzer = LLMPostMortemAnalyzer()
    result = analyzer.analyze_logs(mock_patterns, mock_summary)
    
    return {
        'status': 'success',
        'message': 'Demo of PII/Secrets redaction',
        'redaction_stats': result.get('redaction_stats', {}),
        'analysis': result
    }
