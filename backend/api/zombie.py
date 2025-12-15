"""
Zombie Resource Hunter API Endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.zombie_service import ZombieHunterService

router = APIRouter(prefix="/api/zombie", tags=["Zombie Hunter"])

class ScanRequest(BaseModel):
    regions: Optional[List[str]] = None

@router.post("/scan")
async def run_zombie_scan(request: ScanRequest = None):
    """
    Run zombie resource scan across AWS regions
    """
    try:
        service = ZombieHunterService()
        regions = request.regions if request else None
        results = await service.run_scan(regions=regions)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_scan_status():
    """
    Get status of zombie hunter service
    """
    return {
        "status": "ready",
        "service": "Zombie Resource Hunter"
    }
