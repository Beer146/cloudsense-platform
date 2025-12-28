"""
Enhanced Compliance Service with ML-Powered Anomaly Detection
Built-in compliance rules + ML anomaly detection
"""
import boto3
from datetime import datetime
import time
import sys
from pathlib import Path
import yaml

# Import ML anomaly detector
from services.ml_anomaly_detector import AnomalyDetector

# Import database models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Scan, ComplianceViolation


class EnhancedComplianceService:
    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        # Load config if exists
        config_path = Path(__file__).parent.parent.parent / "scripts" / "compliance" / "config.yaml"
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path):
        """Load configuration or use defaults"""
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Default config
            return {
                'aws': {
                    'regions': ['us-east-1', 'us-west-2']
                },
                'required_tags': ['Environment', 'Owner'],
                'security_groups': {
                    'forbidden_ports': [22, 3389, 3306, 5432]
                }
            }
    
    def _check_ec2_compliance(self, instance, region):
        """Check EC2 instance for compliance violations"""
        violations = []
        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
        instance_id = instance['InstanceId']
        instance_name = tags.get('Name', 'Unnamed')
        
        # Check for required tags
        for required_tag in self.config.get('required_tags', []):
            if required_tag not in tags:
                violations.append({
                    'resource_type': 'EC2',
                    'resource_id': instance_id,
                    'resource_name': instance_name,
                    'violation': f'MISSING_TAG_{required_tag.upper()}',
                    'severity': 'medium',
                    'description': f'Instance missing required tag: {required_tag}',
                    'remediation': f'Add the {required_tag} tag to this instance',
                    'region': region
                })
        
        # Check EBS encryption
        for device in instance.get('BlockDeviceMappings', []):
            ebs = device.get('Ebs', {})
            if not ebs.get('Encrypted', False):
                violations.append({
                    'resource_type': 'EC2',
                    'resource_id': instance_id,
                    'resource_name': instance_name,
                    'violation': 'UNENCRYPTED_EBS',
                    'severity': 'high',
                    'description': 'EBS volume is not encrypted',
                    'remediation': 'Enable EBS encryption for all volumes',
                    'region': region
                })
                break  # Only report once per instance
        
        # Check for public IP with open security groups
        if instance.get('PublicIpAddress'):
            violations.append({
                'resource_type': 'EC2',
                'resource_id': instance_id,
                'resource_name': instance_name,
                'violation': 'PUBLIC_IP_ASSIGNED',
                'severity': 'low',
                'description': 'Instance has public IP assigned',
                'remediation': 'Review if public access is required. Consider using private subnets.',
                'region': region
            })
        
        return violations
    
    def _scan_traditional_compliance(self, regions):
        """Run traditional rule-based compliance checks"""
        all_violations = []
        
        for region in regions:
            try:
                ec2 = boto3.client('ec2', region_name=region)
                response = ec2.describe_instances()
                
                for reservation in response['Reservations']:
                    for instance in reservation['Instances']:
                        violations = self._check_ec2_compliance(instance, region)
                        all_violations.extend(violations)
            except Exception as e:
                print(f"Error scanning {region}: {e}")
        
        return all_violations
    
    def _save_to_database(self, scan_regions, violations_data, duration, user_id):
        """Save compliance scan results to database"""
        from models.database import SessionLocal
        db = SessionLocal()
        
        try:
            scan = Scan(
                user_id=user_id,
                scan_type='compliance',
                status='success',
                regions=scan_regions,
                total_resources=len(violations_data),
                total_cost=0,
                total_savings=0,
                duration_seconds=duration
            )
            db.add(scan)
            db.flush()
            
            # Create violation records
            for violation in violations_data:
                violation_record = ComplianceViolation(
                    scan_id=scan.id,
                    resource_type=violation.get('resource_type', 'unknown'),
                    resource_id=violation.get('resource_id', 'unknown'),
                    resource_name=violation.get('resource_name'),
                    violation=violation.get('violation'),
                    severity=violation.get('severity'),
                    description=violation.get('description'),
                    remediation=violation.get('remediation')
                )
                db.add(violation_record)
            
            db.commit()
            db.refresh(scan)
            
            print(f"✅ Saved compliance scan to database (Scan ID: {scan.id})")
            return scan.id
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error saving to database: {e}")
            return None
        finally:
            db.close()
    
    def _get_all_ec2_instances(self, regions):
        """Get all EC2 instances for baseline training"""
        all_instances = []
        
        for region in regions:
            try:
                ec2 = boto3.client('ec2', region_name=region)
                response = ec2.describe_instances()
                
                for reservation in response['Reservations']:
                    for instance in reservation['Instances']:
                        instance['_region'] = region
                        all_instances.append(instance)
            except Exception as e:
                print(f"Error fetching instances from {region}: {e}")
        
        return all_instances
    
    async def scan(self, regions: list = None, train_baseline: bool = False, user_id: int = None):
        """
        Run compliance scan with ML-powered anomaly detection
        """
        start_time = time.time()
        
        try:
            scan_regions = regions or self.config['aws']['regions']
            
            print(f"\n🔒 Starting Enhanced Compliance Scan with ML Anomaly Detection...")
            print(f"📍 Regions: {', '.join(scan_regions)}\n")
            
            # Step 1: Run traditional rule-based compliance scan
            print("📋 Running rule-based compliance checks...")
            rule_violations = self._scan_traditional_compliance(scan_regions)
            
            # Step 2: Get all instances for anomaly detection
            print("\n🤖 Running ML-powered anomaly detection...")
            all_instances = self._get_all_ec2_instances(scan_regions)
            
            # Step 3: Train baseline if requested or if no model exists
            if train_baseline or self.anomaly_detector.model is None:
                if len(all_instances) >= 2:
                    self.anomaly_detector.train_baseline(
                        all_instances,
                        contamination=0.1
                    )
                else:
                    print("⚠️ Not enough instances to train baseline (need at least 2)")
            
            # Step 4: Detect anomalies
            anomaly_violations = []
            anomaly_count = 0
            
            for instance in all_instances:
                region = instance.get('_region', 'us-east-1')
                prediction = self.anomaly_detector.predict_anomaly(instance, region)
                
                if prediction['is_anomaly'] and prediction['confidence'] >= 0.5:
                    anomaly_count += 1
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    
                    if prediction['confidence'] >= 0.8:
                        severity = 'critical'
                    elif prediction['confidence'] >= 0.6:
                        severity = 'high'
                    else:
                        severity = 'medium'
                    
                    anomaly_violations.append({
                        'resource_type': 'EC2',
                        'resource_id': instance['InstanceId'],
                        'resource_name': tags.get('Name', 'Unnamed'),
                        'violation': 'ML_ANOMALY_DETECTED',
                        'severity': severity,
                        'description': f"ML Anomaly Detection: {prediction['explanation']}",
                        'remediation': 'Review resource configuration and compare with baseline. Investigate unusual patterns.',
                        'region': region,
                        'ml_prediction': prediction
                    })
            
            # Step 5: Combine violations
            all_violations = rule_violations + anomaly_violations
            
            duration = time.time() - start_time
            
            by_severity = {
                'critical': len([v for v in all_violations if v.get('severity') == 'critical']),
                'high': len([v for v in all_violations if v.get('severity') == 'high']),
                'medium': len([v for v in all_violations if v.get('severity') == 'medium']),
                'low': len([v for v in all_violations if v.get('severity') == 'low'])
            }
            
            by_type = {}
            for violation in all_violations:
                vtype = violation.get('resource_type', 'unknown')
                by_type[vtype] = by_type.get(vtype, 0) + 1
            
            scan_id = self._save_to_database(scan_regions, all_violations, duration, user_id)
            
            print(f"\n✅ Compliance scan complete!")
            print(f"   Traditional violations: {len(rule_violations)}")
            print(f"   ML anomalies detected: {anomaly_count}")
            print(f"   Total violations: {len(all_violations)}")
            
            return {
                "status": "success",
                "scan_id": scan_id,
                "regions_scanned": scan_regions,
                "total_violations": len(all_violations),
                "rule_based_violations": len(rule_violations),
                "ml_anomalies": anomaly_count,
                "by_severity": by_severity,
                "by_type": by_type,
                "violations": all_violations,
                "scan_timestamp": datetime.utcnow().isoformat() + "Z",
                "duration_seconds": duration,
                "baseline_trained": train_baseline or (self.anomaly_detector.model is None)
            }
            
        except Exception as e:
            print(f"Enhanced compliance scan error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e)
            }


ComplianceService = EnhancedComplianceService
