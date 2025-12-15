"""
Scan History API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import sys
from pathlib import Path

# Add models to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Scan, ZombieResource, RightSizingRecommendation, get_db

router = APIRouter(prefix="/api/history", tags=["History"])


@router.get("/scans")
async def get_all_scans(
    scan_type: str = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get scan history
    
    Args:
        scan_type: Filter by 'zombie' or 'rightsizing' (optional)
        limit: Number of scans to return (default: 10)
    """
    try:
        query = db.query(Scan)
        
        if scan_type:
            query = query.filter(Scan.scan_type == scan_type)
        
        scans = query.order_by(Scan.timestamp.desc()).limit(limit).all()
        
        return {
            "status": "success",
            "count": len(scans),
            "scans": [
                {
                    "id": scan.id,
                    "scan_type": scan.scan_type,
                    "status": scan.status,
                    "regions": scan.regions,
                    "total_resources": scan.total_resources,
                    "total_cost": scan.total_cost,
                    "total_savings": scan.total_savings,
                    "timestamp": scan.timestamp.isoformat(),
                    "duration_seconds": scan.duration_seconds
                }
                for scan in scans
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scans/{scan_id}")
async def get_scan_details(scan_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific scan"""
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        result = {
            "id": scan.id,
            "scan_type": scan.scan_type,
            "status": scan.status,
            "regions": scan.regions,
            "total_resources": scan.total_resources,
            "total_cost": scan.total_cost,
            "total_savings": scan.total_savings,
            "timestamp": scan.timestamp.isoformat(),
            "duration_seconds": scan.duration_seconds
        }
        
        # Add type-specific details
        if scan.scan_type == 'zombie':
            zombies = db.query(ZombieResource).filter(
                ZombieResource.scan_id == scan_id
            ).all()
            
            result["zombies"] = [
                {
                    "resource_type": z.resource_type,
                    "resource_id": z.resource_id,
                    "name": z.name,
                    "region": z.region,
                    "status": z.status,
                    "reason": z.reason,
                    "instance_type": z.instance_type,
                    "monthly_cost": z.monthly_cost,
                    "details": z.details
                }
                for z in zombies
            ]
        
        elif scan.scan_type == 'rightsizing':
            recommendations = db.query(RightSizingRecommendation).filter(
                RightSizingRecommendation.scan_id == scan_id
            ).all()
            
            result["recommendations"] = [
                {
                    "instance_id": r.instance_id,
                    "name": r.name,
                    "region": r.region,
                    "current_type": r.current_type,
                    "recommended_type": r.recommended_type,
                    "strategy": r.strategy,
                    "reason": r.reason,
                    "monthly_savings": r.monthly_savings,
                    "annual_savings": r.annual_savings,
                    "cpu_metrics": r.cpu_metrics
                }
                for r in recommendations
            ]
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get overall statistics across all scans"""
    try:
        total_scans = db.query(Scan).count()
        zombie_scans = db.query(Scan).filter(Scan.scan_type == 'zombie').count()
        rightsizing_scans = db.query(Scan).filter(Scan.scan_type == 'rightsizing').count()
        
        total_zombies_found = db.query(ZombieResource).count()
        total_recommendations = db.query(RightSizingRecommendation).count()
        
        # Calculate total potential savings
        zombie_savings = db.query(Scan).filter(
            Scan.scan_type == 'zombie'
        ).all()
        total_zombie_cost = sum([s.total_cost or 0 for s in zombie_savings])
        
        rightsizing_savings = db.query(Scan).filter(
            Scan.scan_type == 'rightsizing'
        ).all()
        total_rightsizing_savings = sum([s.total_savings or 0 for s in rightsizing_savings])
        
        return {
            "status": "success",
            "stats": {
                "total_scans": total_scans,
                "zombie_scans": zombie_scans,
                "rightsizing_scans": rightsizing_scans,
                "total_zombies_found": total_zombies_found,
                "total_recommendations": total_recommendations,
                "total_monthly_waste": total_zombie_cost,
                "total_annual_savings_potential": total_rightsizing_savings
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/scans/{scan_id}")
async def delete_scan(scan_id: int, db: Session = Depends(get_db)):
    """Delete a scan and all associated data"""
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        db.delete(scan)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Scan {scan_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
