"""
Post-Mortem Generator API Endpoints
WITH RATE LIMITING AND COST CONTROLS
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path
import traceback

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.postmortem_service_enhanced import EnhancedPostMortemService
from auth.clerk_auth import get_current_user
from auth.user_service import get_or_create_user

router = APIRouter(prefix="/api/postmortem", tags=["PostMortem"])


class AnalyzeRequest(BaseModel):
    regions: Optional[List[str]] = None
    lookback_hours: Optional[int] = 24


@router.post("/analyze")
async def analyze_logs(
    request: AnalyzeRequest = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze CloudWatch Logs and generate post-mortem report
    WITH RATE LIMITING AND COST CONTROLS
    """
    try:
        user = get_or_create_user(
            clerk_user_id=current_user["user_id"],
            email=current_user.get("email")
        )
        
        service = EnhancedPostMortemService()
        
        lookback_hours = request.lookback_hours if request else 24
        
        # Pass user_id for rate limiting
        results = await service.analyze(lookback_hours=lookback_hours, user_id=user.id)
        return results
    except Exception as e:
        print(f"\n{'='*80}")
        print("ERROR in Post-Mortem Analysis:")
        print(f"{'='*80}")
        print(traceback.format_exc())
        print(f"{'='*80}\n")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/{user_id}")
async def get_usage_stats(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get rate limit and cost usage statistics for a user
    """
    from services.security.rate_limiter import get_rate_limiter
    
    limiter = get_rate_limiter()
    stats = limiter.get_user_stats(user_id)
    
    return {
        'user_id': user_id,
        'usage': stats,
        'limits': {
            'requests_per_hour': limiter.DEFAULT_REQUESTS_PER_HOUR,
            'requests_per_day': limiter.DEFAULT_REQUESTS_PER_DAY,
            'daily_cost_limit_usd': limiter.DEFAULT_DAILY_COST_LIMIT_USD
        }
    }


@router.get("/status")
async def get_status():
    """
    Get status of post-mortem service
    """
    return {
        'status': 'ready',
        'service': 'Post-Mortem Generator with LLM',
        'features': [
            'PII/Secrets Redaction',
            'LLM Output Validation',
            'Rate Limiting',
            'Cost Controls'
        ]
    }
