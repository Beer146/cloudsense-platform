"""
Compliance Validator Service
Wrapper for the compliance scanner
"""
import sys
from pathlib import Path
from datetime import datetime
import yaml
import time

# Add compliance-validator scripts to Python path
scripts_path = Path(__file__).parent.parent.parent / "scripts" / "compliance-validator"
sys.path.insert(0, str(scripts_path))

# Import compliance scanners using absolute import after path is set
import importlib.util

# Load scanners module from compliance-validator
scanners_path = scripts_path / "scanners"
s3_spec = importlib.util.spec_from_file_location("compliance_s3_scanner", scanners_path / "s3_scanner.py")
s3_module = importlib.util.module_from_spec(s3_spec)
s3_spec.loader.exec_module(s3_module)
S3ComplianceScanner = s3_module.S3ComplianceScanner

rds_spec = importlib.util.spec_from_file_location("compliance_rds_scanner", scanners_path / "rds_scanner.py")
rds_module = importlib.util.module_from_spec(rds_spec)
rds_spec.loader.exec_module(rds_module)
RDSComplianceScanner = rds_module.RDSComplianceScanner

sg_spec = importlib.util.spec_from_file_location("compliance_sg_scanner", scanners_path / "sg_scanner.py")
sg_module = importlib.util.module_from_spec(sg_spec)
sg_spec.loader.exec_module(sg_module)
SecurityGroupScanner = sg_module.SecurityGroupScanner

ec2_spec = importlib.util.spec_from_file_location("compliance_ec2_scanner", scanners_path / "ec2_scanner.py")
ec2_module = importlib.util.module_from_spec(ec2_spec)
ec2_spec.loader.exec_module(ec2_module)
EC2ComplianceScanner = ec2_module.EC2ComplianceScanner

# Import database models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Scan, ComplianceViolation


class ComplianceService:
    def __init__(self):
        self.config_path = scripts_path / "config.yaml"
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return {
                'aws': {'regions': ['us-east-1', 'us-west-2']},
                'rules': {
                    's3': {'require_encryption': True, 'block_public_access': True},
                    'rds': {'require_encryption': True, 'block_public_access': True, 'require_backup': True},
                    'security_groups': {'sensitive_ports': [22, 3389, 3306, 5432]},
                    'ec2': {'required_tags': ['Environment', 'Owner'], 'require_encryption': True}
                }
            }
    
    def _scan_compliance(self, regions):
        """Run compliance scans"""
        all_violations = []
        
        for region in regions:
            print(f"Scanning {region}...")
            
            # S3 (only from us-east-1)
            if region == 'us-east-1':
                try:
                    s3_scanner = S3ComplianceScanner(region, self.config)
                    s3_violations = s3_scanner.scan()
                    all_violations.extend(s3_violations)
                except Exception as e:
                    print(f"S3 scan error: {e}")
            
            # RDS
            try:
                rds_scanner = RDSComplianceScanner(region, self.config)
                rds_violations = rds_scanner.scan()
                all_violations.extend(rds_violations)
            except Exception as e:
                print(f"RDS scan error: {e}")
            
            # Security Groups
            try:
                sg_scanner = SecurityGroupScanner(region, self.config)
                sg_violations = sg_scanner.scan()
                all_violations.extend(sg_violations)
            except Exception as e:
                print(f"SG scan error: {e}")
            
            # EC2
            try:
                ec2_scanner = EC2ComplianceScanner(region, self.config)
                ec2_violations = ec2_scanner.scan()
                all_violations.extend(ec2_violations)
            except Exception as e:
                print(f"EC2 scan error: {e}")
        
        return all_violations
    
    def _save_to_database(self, scan_regions, violations, duration):
        """Save compliance scan results to database"""
        from models.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Create scan record
            scan = Scan(
                scan_type='compliance',
                status='success',
                regions=scan_regions,
                total_resources=len(violations),
                total_cost=0,
                total_savings=0,
                duration_seconds=duration
            )
            db.add(scan)
            db.flush()
            
            # Create violation records and collect their IDs
            violation_records = []
            for violation in violations:
                violation_record = ComplianceViolation(
                    scan_id=scan.id,
                    resource_type=violation.get('resource_type', 'unknown'),
                    resource_id=violation.get('resource_id', 'unknown'),
                    resource_name=violation.get('resource_name'),
                    violation=violation.get('violation', 'unknown'),
                    severity=violation.get('severity', 'medium'),
                    description=violation.get('description', ''),
                    remediation=violation.get('remediation', '')
                )
                db.add(violation_record)
                violation_records.append(violation_record)
            
            db.commit()
            
            # Refresh to get IDs
            for record in violation_records:
                db.refresh(record)
            
            print(f"✅ Saved compliance scan to database (Scan ID: {scan.id})")
            return scan.id, violation_records
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error saving to database: {e}")
            return None, []
        finally:
            db.close()
    
    async def run_scan(self, regions: list = None):
        """Run compliance scan"""
        start_time = time.time()
        
        try:
            scan_regions = regions or self.config['aws']['regions']
            
            # Scan for violations
            violations = self._scan_compliance(scan_regions)
            
            print(f"\nTotal violations found: {len(violations)}")
            
            # Group by severity
            critical = [v for v in violations if v.get('severity') == 'critical']
            high = [v for v in violations if v.get('severity') == 'high']
            medium = [v for v in violations if v.get('severity') == 'medium']
            low = [v for v in violations if v.get('severity') == 'low']
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Save to database and get violation records with IDs
            scan_id, violation_records = self._save_to_database(scan_regions, violations, duration)
            
            # Add database IDs to violations for response
            violations_with_ids = []
            for i, violation in enumerate(violations):
                violation_with_id = violation.copy()
                if i < len(violation_records):
                    violation_with_id['id'] = violation_records[i].id
                    violation_with_id['resolved'] = violation_records[i].resolved
                    violation_with_id['resolved_at'] = violation_records[i].resolved_at.isoformat() if violation_records[i].resolved_at else None
                    violation_with_id['resolved_note'] = violation_records[i].resolved_note
                violations_with_ids.append(violation_with_id)
            
            # Format response
            results = {
                "status": "success",
                "scan_id": scan_id,
                "regions_scanned": scan_regions,
                "total_violations": len(violations),
                "by_severity": {
                    "critical": len(critical),
                    "high": len(high),
                    "medium": len(medium),
                    "low": len(low)
                },
                "by_type": {
                    "s3": len([v for v in violations if v.get('resource_type') == 'S3']),
                    "rds": len([v for v in violations if v.get('resource_type') == 'RDS']),
                    "security_group": len([v for v in violations if v.get('resource_type') == 'SecurityGroup']),
                    "ec2": len([v for v in violations if v.get('resource_type') == 'EC2'])
                },
                "violations": violations_with_ids,  # Now includes database IDs!
                "scan_timestamp": datetime.utcnow().isoformat() + "Z",
                "duration_seconds": duration
            }
            
            return results
            
        except Exception as e:
            print(f"Compliance scan error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e)
            }
