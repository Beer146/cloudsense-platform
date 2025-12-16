"""
Insights API Endpoint
Provides aggregated insights across all services
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add models to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Scan, ZombieResource, RightSizingRecommendation, ComplianceViolation, get_db

router = APIRouter(prefix="/api/insights", tags=["Insights"])


@router.get("/summary")
async def get_insights_summary(db: Session = Depends(get_db)):
    """Get comprehensive insights across all services"""
    try:
        # Get latest scans
        latest_zombie = db.query(Scan).filter(Scan.scan_type == 'zombie').order_by(desc(Scan.timestamp)).first()
        latest_rightsizing = db.query(Scan).filter(Scan.scan_type == 'rightsizing').order_by(desc(Scan.timestamp)).first()
        latest_compliance = db.query(Scan).filter(Scan.scan_type == 'compliance').order_by(desc(Scan.timestamp)).first()
        
        # Get previous scans for comparison (30 days ago)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        prev_zombie = db.query(Scan).filter(
            Scan.scan_type == 'zombie',
            Scan.timestamp < thirty_days_ago
        ).order_by(desc(Scan.timestamp)).first()
        
        prev_compliance = db.query(Scan).filter(
            Scan.scan_type == 'compliance',
            Scan.timestamp < thirty_days_ago
        ).order_by(desc(Scan.timestamp)).first()
        
        # Calculate health scores (0-100)
        cost_score = calculate_cost_score(latest_zombie)
        rightsizing_score = calculate_rightsizing_score(latest_rightsizing)
        security_score = calculate_security_score(latest_compliance)
        overall_score = (cost_score + rightsizing_score + security_score) / 3
        
        # Calculate trends
        zombie_trend = calculate_trend(latest_zombie, prev_zombie, 'total_cost')
        compliance_trend = calculate_trend(latest_compliance, prev_compliance, 'total_resources')
        
        # Get top recommendations
        recommendations = get_top_recommendations(
            db, latest_zombie, latest_rightsizing, latest_compliance
        )
        
        return {
            "status": "success",
            "overall_health": {
                "score": round(overall_score, 1),
                "breakdown": {
                    "cost_efficiency": round(cost_score, 1),
                    "right_sizing": round(rightsizing_score, 1),
                    "security": round(security_score, 1)
                }
            },
            "current_state": {
                "monthly_waste": latest_zombie.total_cost if latest_zombie else 0,
                "annual_savings_opportunity": latest_rightsizing.total_savings if latest_rightsizing else 0,
                "critical_violations": get_critical_violations_count(db, latest_compliance),
                "total_violations": latest_compliance.total_resources if latest_compliance else 0
            },
            "trends_30d": {
                "zombie_cost": {
                    "current": latest_zombie.total_cost if latest_zombie else 0,
                    "previous": prev_zombie.total_cost if prev_zombie else 0,
                    "change": zombie_trend,
                    "improving": zombie_trend < 0
                },
                "compliance": {
                    "current": latest_compliance.total_resources if latest_compliance else 0,
                    "previous": prev_compliance.total_resources if prev_compliance else 0,
                    "change": compliance_trend,
                    "improving": compliance_trend < 0
                }
            },
            "top_recommendations": recommendations,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def calculate_cost_score(scan):
    """Calculate cost efficiency score (0-100, higher is better)"""
    if not scan:
        return 100  # No scan = no data = assume perfect
    
    # Score based on monthly waste
    # $0 = 100, $50 = 75, $100 = 50, $200+ = 0
    monthly_cost = scan.total_cost
    
    if monthly_cost == 0:
        return 100
    elif monthly_cost < 10:
        return 95
    elif monthly_cost < 50:
        return 85 - (monthly_cost - 10) * 0.5
    elif monthly_cost < 100:
        return 70 - (monthly_cost - 50) * 0.4
    elif monthly_cost < 200:
        return 50 - (monthly_cost - 100) * 0.5
    else:
        return max(0, 50 - (monthly_cost - 200) * 0.1)


def calculate_rightsizing_score(scan):
    """Calculate right-sizing score (0-100, higher is better)"""
    if not scan:
        return 100  # No scan = no data = assume perfect
    
    # Score based on number of recommendations
    # 0 recommendations = 100 (perfectly sized)
    # 1-5 = 80-90, 6-10 = 60-80, 10+ = <60
    recommendations = scan.total_resources
    
    if recommendations == 0:
        return 100
    elif recommendations <= 5:
        return 90 - (recommendations * 2)
    elif recommendations <= 10:
        return 70 - ((recommendations - 5) * 2)
    else:
        return max(30, 60 - (recommendations - 10))


def calculate_security_score(scan):
    """Calculate security score (0-100, higher is better)"""
    if not scan:
        return 100  # No scan = assume compliant
    
    # Score heavily penalizes critical violations
    violations = scan.total_resources
    
    if violations == 0:
        return 100
    elif violations <= 2:
        return 90 - (violations * 5)
    elif violations <= 5:
        return 75 - ((violations - 2) * 8)
    elif violations <= 10:
        return 50 - ((violations - 5) * 5)
    else:
        return max(0, 30 - (violations - 10) * 2)


def calculate_trend(current_scan, previous_scan, field):
    """Calculate change between two scans"""
    if not current_scan:
        return 0
    
    current_value = getattr(current_scan, field, 0)
    
    if not previous_scan:
        return current_value  # No comparison available
    
    previous_value = getattr(previous_scan, field, 0)
    
    return current_value - previous_value


def get_critical_violations_count(db, compliance_scan):
    """Get count of critical violations from latest scan"""
    if not compliance_scan:
        return 0
    
    critical_count = db.query(ComplianceViolation).filter(
        ComplianceViolation.scan_id == compliance_scan.id,
        ComplianceViolation.severity == 'critical'
    ).count()
    
    return critical_count


def get_top_recommendations(db, zombie_scan, rightsizing_scan, compliance_scan):
    """Generate top 5 actionable recommendations"""
    recommendations = []
    
    # Critical security violations (highest priority)
    if compliance_scan:
        critical_violations = db.query(ComplianceViolation).filter(
            ComplianceViolation.scan_id == compliance_scan.id,
            ComplianceViolation.severity == 'critical'
        ).limit(2).all()
        
        for violation in critical_violations:
            recommendations.append({
                "priority": 1,
                "type": "security",
                "title": f"Fix critical security violation",
                "description": violation.description,
                "impact": "High security risk",
                "effort": "5-10 minutes",
                "action": violation.remediation
            })
    
    # High-value zombies
    if zombie_scan:
        expensive_zombies = db.query(ZombieResource).filter(
            ZombieResource.scan_id == zombie_scan.id
        ).order_by(desc(ZombieResource.monthly_cost)).limit(2).all()
        
        for zombie in expensive_zombies:
            recommendations.append({
                "priority": 2,
                "type": "cost",
                "title": f"Terminate zombie {zombie.resource_type}",
                "description": f"{zombie.resource_id} - {zombie.reason}",
                "impact": f"Save ${zombie.monthly_cost:.2f}/month",
                "effort": "2 minutes",
                "action": f"Terminate {zombie.resource_id}"
            })
    
    # Top right-sizing opportunities
    if rightsizing_scan:
        top_savings = db.query(RightSizingRecommendation).filter(
            RightSizingRecommendation.scan_id == rightsizing_scan.id
        ).order_by(desc(RightSizingRecommendation.monthly_savings)).limit(2).all()
        
        for rec in top_savings:
            recommendations.append({
                "priority": 3,
                "type": "optimization",
                "title": f"Downsize {rec.current_type}",
                "description": f"{rec.instance_id} → {rec.recommended_type}",
                "impact": f"Save ${rec.monthly_savings:.2f}/month",
                "effort": "10 minutes",
                "action": f"Resize instance to {rec.recommended_type}"
            })
    
    # Sort by priority and return top 5
    recommendations.sort(key=lambda x: x['priority'])
    return recommendations[:5]
