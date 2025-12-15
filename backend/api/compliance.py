"""
Compliance Validator API Endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.compliance_service import ComplianceService

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])

class ScanRequest(BaseModel):
    regions: Optional[List[str]] = None

@router.post("/scan")
async def run_compliance_scan(request: ScanRequest = None):
    """
    Run compliance scan across AWS resources
    """
    try:
        service = ComplianceService()
        regions = request.regions if request else None
        results = await service.run_scan(regions=regions)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_scan_status():
    """
    Get status of compliance service
    """
    return {
        "status": "ready",
        "service": "Compliance-as-Code Validator"
    }
