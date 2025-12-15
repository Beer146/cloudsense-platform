"""
Right-Sizing Recommendation API Endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.rightsizing_service import RightSizingService

router = APIRouter(prefix="/api/rightsizing", tags=["Right-Sizing"])

class AnalysisRequest(BaseModel):
    regions: Optional[List[str]] = None
    days: Optional[int] = 30

@router.post("/analyze")
async def analyze_resources(request: AnalysisRequest = None):
    """
    Analyze resources and generate right-sizing recommendations
    """
    try:
        service = RightSizingService()
        regions = request.regions if request else None
        days = request.days if request else 30
        results = await service.analyze_resources(regions=regions, days=days)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_analysis_status():
    """
    Get status of right-sizing service
    """
    return {
        "status": "ready",
        "service": "Right-Sizing Recommendation Engine"
    }
