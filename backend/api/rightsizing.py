"""
Right-Sizing Analysis API Endpoints
Enhanced with LSTM workload forecasting
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.rightsizing_service_enhanced import EnhancedRightSizingService

router = APIRouter(prefix="/api/rightsizing", tags=["Right-Sizing"])


class AnalyzeRequest(BaseModel):
    regions: Optional[List[str]] = None
    use_lstm: Optional[bool] = True


@router.post("/analyze")
async def analyze_resources(request: AnalyzeRequest = None):
    """
    Analyze EC2 instances for right-sizing opportunities
    Enhanced with LSTM workload forecasting
    """
    try:
        service = EnhancedRightSizingService()
        
        regions = None
        use_lstm = True
        
        if request:
            regions = request.regions
            use_lstm = request.use_lstm
        
        results = await service.analyze(regions=regions, use_lstm=use_lstm)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """
    Get status of right-sizing service
    """
    return {
        "status": "ready",
        "service": "Right-Sizing Analyzer with LSTM Forecasting"
    }
