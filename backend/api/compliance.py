"""
Compliance Validator API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.compliance_service_enhanced import EnhancedComplianceService
from auth.clerk_auth import get_current_user
from auth.user_service import get_or_create_user

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])


class ScanRequest(BaseModel):
    regions: Optional[List[str]] = None
    train_baseline: Optional[bool] = False


@router.post("/scan")
async def scan_compliance(
    request: ScanRequest = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Scan AWS resources for compliance violations with ML anomaly detection
    """
    try:
        user = get_or_create_user(
            clerk_user_id=current_user["user_id"],
            email=current_user.get("email")
        )
        
        service = EnhancedComplianceService()
        regions = request.regions if request else None
        train_baseline = request.train_baseline if request else False
        
        results = await service.scan(regions=regions, train_baseline=train_baseline, user_id=user.id)
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
        "service": "Compliance Validator with ML"
    }
