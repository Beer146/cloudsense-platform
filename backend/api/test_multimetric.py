"""
Test endpoint for multi-metric analysis (no auth required)
"""
from fastapi import APIRouter
from services.rightsizing_service_multimetric import MultiMetricRightSizingService

router = APIRouter(prefix="/api/test", tags=["Test"])


@router.get("/multimetric-demo")
async def multimetric_demo():
    """
    Demonstrate multi-metric right-sizing analysis
    """
    service = MultiMetricRightSizingService()
    results = await service.analyze(user_id=1)
    return results
