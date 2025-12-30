"""
Right-Sizing Analysis API Endpoints
Enhanced with LSTM workload forecasting AND multi-metric analysis
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.rightsizing_service_enhanced import EnhancedRightSizingService
from services.rightsizing_service_multimetric import MultiMetricRightSizingService
from auth.clerk_auth import get_current_user
from auth.user_service import get_or_create_user

router = APIRouter(prefix="/api/rightsizing", tags=["Right-Sizing"])


class AnalyzeRequest(BaseModel):
    regions: Optional[List[str]] = None
    use_lstm: Optional[bool] = True
    use_multimetric: Optional[bool] = False  # NEW: Enable production-grade analysis


@router.post("/analyze")
async def analyze_resources(
    request: AnalyzeRequest = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze EC2 instances for right-sizing opportunities
    
    Modes:
    - use_lstm=True: LSTM workload forecasting (default)
    - use_multimetric=True: Production-grade multi-metric analysis (CPU, Network, Disk, Burst Credits)
    """
    try:
        user = get_or_create_user(
            clerk_user_id=current_user["user_id"],
            email=current_user.get("email")
        )
        
        regions = None
        use_lstm = True
        use_multimetric = False
        
        if request:
            regions = request.regions
            use_lstm = request.use_lstm
            use_multimetric = request.use_multimetric
        
        # Choose service based on mode
        if use_multimetric:
            print("🔬 Using PRODUCTION-GRADE multi-metric analysis...")
            service = MultiMetricRightSizingService()
            results = await service.analyze(regions=regions, user_id=user.id)
        else:
            print("🤖 Using LSTM-enhanced analysis...")
            service = EnhancedRightSizingService()
            results = await service.analyze(regions=regions, use_lstm=use_lstm, user_id=user.id)
        
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
        "service": "Right-Sizing Analyzer with LSTM + Multi-Metric Analysis",
        "modes": {
            "lstm": "LSTM workload forecasting",
            "multimetric": "Production-grade (CPU, Network, Disk, Burst Credits, P95/P99)"
        }
    }
