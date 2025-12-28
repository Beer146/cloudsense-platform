"""
Database models for scans and resources with multi-tenancy support
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    """Represents a user account (from Clerk)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    clerk_user_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, index=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    scans = relationship("Scan", back_populates="user", cascade="all, delete-orphan")
    aws_accounts = relationship("AWSAccount", back_populates="user", cascade="all, delete-orphan")


class AWSAccount(Base):
    """Represents a user's AWS account"""
    __tablename__ = "aws_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    account_name = Column(String)
    aws_account_id = Column(String)
    role_arn = Column(String, nullable=True)
    access_key_encrypted = Column(String, nullable=True)
    secret_key_encrypted = Column(String, nullable=True)
    regions = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="aws_accounts")


class Scan(Base):
    """Represents a scan operation"""
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    aws_account_id = Column(Integer, ForeignKey("aws_accounts.id"), nullable=True)
    
    scan_type = Column(String)
    status = Column(String)
    regions = Column(JSON)
    total_resources = Column(Integer)
    total_cost = Column(Float)
    total_savings = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Float, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="scans")
    zombies = relationship("ZombieResource", back_populates="scan", cascade="all, delete-orphan")
    recommendations = relationship("RightSizingRecommendation", back_populates="scan", cascade="all, delete-orphan")
    violations = relationship("ComplianceViolation", back_populates="scan", cascade="all, delete-orphan")


class ZombieResource(Base):
    """Represents a zombie resource found in a scan"""
    __tablename__ = "zombie_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    
    resource_type = Column(String)
    resource_id = Column(String, index=True)
    name = Column(String)
    region = Column(String)
    status = Column(String)
    reason = Column(String)
    instance_type = Column(String, nullable=True)
    monthly_cost = Column(Float)
    details = Column(JSON)
    
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_note = Column(String, nullable=True)
    
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
    strategy = Column(String)
    reason = Column(String)
    current_monthly_cost = Column(Float)
    recommended_monthly_cost = Column(Float)
    monthly_savings = Column(Float)
    annual_savings = Column(Float)
    cpu_metrics = Column(JSON)
    
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_note = Column(String, nullable=True)
    
    scan = relationship("Scan", back_populates="recommendations")


class ComplianceViolation(Base):
    """Represents a compliance violation found in a scan"""
    __tablename__ = "compliance_violations"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    
    resource_type = Column(String)
    resource_id = Column(String, index=True)
    resource_name = Column(String, nullable=True)
    violation = Column(String)
    severity = Column(String)
    description = Column(String)
    remediation = Column(String)
    
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_note = Column(String, nullable=True)
    
    scan = relationship("Scan", back_populates="violations")
