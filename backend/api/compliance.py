"""
Compliance Validation API Endpoints
Enhanced with ML Anomaly Detection
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.compliance_service_enhanced import EnhancedComplianceService

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])


class ScanRequest(BaseModel):
    regions: Optional[List[str]] = None
    train_baseline: Optional[bool] = False


@router.post("/scan")
async def scan_compliance(request: ScanRequest = None):
    """
    Scan AWS resources for compliance violations
    Enhanced with ML-powered anomaly detection
    """
    try:
        service = EnhancedComplianceService()
        
        regions = None
        train_baseline = False
        
        if request:
            regions = request.regions
            train_baseline = request.train_baseline
        
        results = await service.scan(regions=regions, train_baseline=train_baseline)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """
    Get status of compliance service
    """
    return {
        "status": "ready",
        "service": "Compliance Validator with ML Anomaly Detection"
    }
