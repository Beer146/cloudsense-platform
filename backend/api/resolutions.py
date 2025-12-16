"""
Resolution Tracking API
Mark issues as resolved and track fixes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import sys
from pathlib import Path

# Add models to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import ZombieResource, RightSizingRecommendation, ComplianceViolation, get_db

router = APIRouter(prefix="/api/resolutions", tags=["Resolutions"])


class ResolveRequest(BaseModel):
    note: Optional[str] = None


@router.post("/zombie/{zombie_id}/resolve")
async def resolve_zombie(zombie_id: int, request: ResolveRequest, db: Session = Depends(get_db)):
    """Mark a zombie resource as resolved"""
    try:
        zombie = db.query(ZombieResource).filter(ZombieResource.id == zombie_id).first()
        
        if not zombie:
            raise HTTPException(status_code=404, detail="Zombie resource not found")
        
        zombie.resolved = True
        zombie.resolved_at = datetime.utcnow()
        zombie.resolved_note = request.note
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Zombie {zombie.resource_id} marked as resolved",
            "resolved_at": zombie.resolved_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rightsizing/{rec_id}/resolve")
async def resolve_recommendation(rec_id: int, request: ResolveRequest, db: Session = Depends(get_db)):
    """Mark a right-sizing recommendation as resolved"""
    try:
        rec = db.query(RightSizingRecommendation).filter(
            RightSizingRecommendation.id == rec_id
        ).first()
        
        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        rec.resolved = True
        rec.resolved_at = datetime.utcnow()
        rec.resolved_note = request.note
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Recommendation for {rec.instance_id} marked as resolved",
            "resolved_at": rec.resolved_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/{violation_id}/resolve")
async def resolve_violation(violation_id: int, request: ResolveRequest, db: Session = Depends(get_db)):
    """Mark a compliance violation as resolved"""
    try:
        violation = db.query(ComplianceViolation).filter(
            ComplianceViolation.id == violation_id
        ).first()
        
        if not violation:
            raise HTTPException(status_code=404, detail="Violation not found")
        
        violation.resolved = True
        violation.resolved_at = datetime.utcnow()
        violation.resolved_note = request.note
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Violation on {violation.resource_id} marked as resolved",
            "resolved_at": violation.resolved_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/{violation_id}/unresolve")
async def unresolve_violation(violation_id: int, db: Session = Depends(get_db)):
    """Unmark a violation (if it came back)"""
    try:
        violation = db.query(ComplianceViolation).filter(
            ComplianceViolation.id == violation_id
        ).first()
        
        if not violation:
            raise HTTPException(status_code=404, detail="Violation not found")
        
        violation.resolved = False
        violation.resolved_at = None
        violation.resolved_note = None
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Violation on {violation.resource_id} marked as unresolved"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_resolution_stats(db: Session = Depends(get_db)):
    """Get resolution statistics"""
    try:
        # Count resolved items
        resolved_zombies = db.query(ZombieResource).filter(ZombieResource.resolved == True).count()
        resolved_recommendations = db.query(RightSizingRecommendation).filter(
            RightSizingRecommendation.resolved == True
        ).count()
        resolved_violations = db.query(ComplianceViolation).filter(
            ComplianceViolation.resolved == True
        ).count()
        
        # Count unresolved items
        unresolved_zombies = db.query(ZombieResource).filter(ZombieResource.resolved == False).count()
        unresolved_recommendations = db.query(RightSizingRecommendation).filter(
            RightSizingRecommendation.resolved == False
        ).count()
        unresolved_violations = db.query(ComplianceViolation).filter(
            ComplianceViolation.resolved == False
        ).count()
        
        return {
            "status": "success",
            "resolved": {
                "zombies": resolved_zombies,
                "recommendations": resolved_recommendations,
                "violations": resolved_violations,
                "total": resolved_zombies + resolved_recommendations + resolved_violations
            },
            "unresolved": {
                "zombies": unresolved_zombies,
                "recommendations": unresolved_recommendations,
                "violations": unresolved_violations,
                "total": unresolved_zombies + unresolved_recommendations + unresolved_violations
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
