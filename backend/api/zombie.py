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
from services.zombie_service import ZombieService

router = APIRouter(prefix="/api/zombie", tags=["Zombie"])


class ScanRequest(BaseModel):
    regions: Optional[List[str]] = None


@router.post("/scan")
async def scan_zombies(request: ScanRequest = None):
    """
    Scan AWS for zombie resources with ML risk predictions
    """
    try:
        service = ZombieService()
        regions = request.regions if request else None
        results = await service.scan(regions=regions)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """
    Get status of zombie hunter service
    """
    return {
        "status": "ready",
        "service": "Zombie Resource Hunter with ML"
    }
