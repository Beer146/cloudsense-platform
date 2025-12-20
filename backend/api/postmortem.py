"""
Post-Mortem Analysis API Endpoints
Enhanced with LLM-powered analysis
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.postmortem_service_enhanced import EnhancedPostMortemService

router = APIRouter(prefix="/api/postmortem", tags=["Post-Mortem"])


class AnalyzeRequest(BaseModel):
    lookback_hours: Optional[int] = 24
    use_llm: Optional[bool] = True


@router.post("/analyze")
async def analyze_logs(request: AnalyzeRequest = None):
    """
    Analyze CloudWatch Logs for incidents
    Enhanced with Claude API for intelligent root cause analysis
    """
    try:
        service = EnhancedPostMortemService()
        
        lookback_hours = 24
        use_llm = True
        
        if request:
            lookback_hours = request.lookback_hours
            use_llm = request.use_llm
        
        results = await service.analyze(lookback_hours=lookback_hours, use_llm=use_llm)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """
    Get status of post-mortem service
    """
    return {
        "status": "ready",
        "service": "Post-Mortem Analyzer with LLM Enhancement"
    }
