"""
Zombie Resource Hunter API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path
import traceback

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.zombie_service import ZombieService
from auth.clerk_auth import get_current_user
from auth.user_service import get_or_create_user

router = APIRouter(prefix="/api/zombie", tags=["Zombie"])


class ScanRequest(BaseModel):
    regions: Optional[List[str]] = None


@router.post("/scan")
async def scan_zombies(
    request: ScanRequest = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Scan AWS for zombie resources with ML risk predictions
    Requires authentication
    """
    try:
        print(f"=== ZOMBIE SCAN START ===")
        print(f"Current user received: {current_user}")
        
        user = get_or_create_user(
            clerk_user_id=current_user["user_id"],
            email=current_user.get("email")
        )
        
        print(f"User ID: {user.id}")
        
        service = ZombieService()
        regions = request.regions if request else None
        results = await service.scan(regions=regions, user_id=user.id)
        
        print(f"=== ZOMBIE SCAN COMPLETE ===")
        return results
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"ERROR in zombie scan endpoint:")
        print(f"{'='*80}")
        print(traceback.format_exc())
        print(f"{'='*80}\n")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Get status of zombie hunter service"""
    return {
        "status": "ready",
        "service": "Zombie Resource Hunter with ML"
    }
