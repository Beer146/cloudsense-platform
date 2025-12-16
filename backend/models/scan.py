"""
Database models for scans and resources
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Scan(Base):
    """Represents a scan operation"""
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_type = Column(String)  # 'zombie', 'rightsizing', or 'compliance'
    status = Column(String)  # 'success' or 'error'
    regions = Column(JSON)  # List of regions scanned
    total_resources = Column(Integer)
    total_cost = Column(Float)
    total_savings = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Float, nullable=True)
    
    # Relationships
    zombies = relationship("ZombieResource", back_populates="scan", cascade="all, delete-orphan")
    recommendations = relationship("RightSizingRecommendation", back_populates="scan", cascade="all, delete-orphan")
    violations = relationship("ComplianceViolation", back_populates="scan", cascade="all, delete-orphan")


class ZombieResource(Base):
    """Represents a zombie resource found in a scan"""
    __tablename__ = "zombie_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    
    resource_type = Column(String)  # EC2, EBS, RDS, ELB
    resource_id = Column(String, index=True)
    name = Column(String)
    region = Column(String)
    status = Column(String)  # stopped, unattached, idle, etc.
    reason = Column(String)
    instance_type = Column(String, nullable=True)
    monthly_cost = Column(Float)
    details = Column(JSON)  # Additional metadata
    
    # Resolution tracking
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_note = Column(String, nullable=True)
    
    # Relationship
    scan = relationship("Scan", back_populates="zombies")


class RightSizingRecommendation(Base):
    """Represents a right-sizing recommendation"""
    __tablename__ = "rightsizing_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    
    instance_id = Column(String, index=True)
    name = Column(String)
    region = Column(String)
    current_type = Column(String)
    recommended_type = Column(String)
    strategy = Column(String)  # downsize, family_switch, etc.
    reason = Column(String)
    current_monthly_cost = Column(Float)
    recommended_monthly_cost = Column(Float)
    monthly_savings = Column(Float)
    annual_savings = Column(Float)
    cpu_metrics = Column(JSON)  # CPU utilization data
    
    # Resolution tracking
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_note = Column(String, nullable=True)
    
    # Relationship
    scan = relationship("Scan", back_populates="recommendations")


class ComplianceViolation(Base):
    """Represents a compliance violation found in a scan"""
    __tablename__ = "compliance_violations"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    
    resource_type = Column(String)  # S3, RDS, SecurityGroup, EC2
    resource_id = Column(String, index=True)
    resource_name = Column(String, nullable=True)
    violation = Column(String)  # Type of violation
    severity = Column(String)  # critical, high, medium, low
    description = Column(String)
    remediation = Column(String)
    
    # Resolution tracking
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_note = Column(String, nullable=True)
    
    # Relationship
    scan = relationship("Scan", back_populates="violations")
