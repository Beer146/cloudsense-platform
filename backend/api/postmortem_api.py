"""
Post-Mortem Generator API Endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path
import traceback

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.postmortem_service import PostMortemService

router = APIRouter(prefix="/api/postmortem", tags=["PostMortem"])


class AnalyzeRequest(BaseModel):
    regions: Optional[List[str]] = None
    lookback_hours: Optional[int] = 24


@router.post("/analyze")
async def analyze_logs(request: AnalyzeRequest = None):
    """
    Analyze CloudWatch Logs and generate post-mortem report
    """
    try:
        service = PostMortemService()
        
        regions = request.regions if request else None
        lookback_hours = request.lookback_hours if request else 24
        
        results = await service.analyze(regions=regions, lookback_hours=lookback_hours)
        return results
    except Exception as e:
        print(f"\n{'='*80}")
        print("ERROR in Post-Mortem Analysis:")
        print(f"{'='*80}")
        print(traceback.format_exc())
        print(f"{'='*80}\n")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """
    Get status of post-mortem service
    """
    return {
        "status": "ready",
        "service": "Post-Mortem Generator"
    }
