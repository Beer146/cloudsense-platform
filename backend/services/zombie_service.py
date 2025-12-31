"""
Zombie Resource Detection Service with ML Predictions
"""
import boto3
from typing import List, Dict, Tuple
from datetime import datetime
import time
import sys
from pathlib import Path

# Import ML predictor
from services.ml_zombie_predictor import ZombiePredictor

# Import database models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Scan, ZombieResource


class ZombieService:
    def __init__(self):
        self.predictor = ZombiePredictor()
        self.pricing = {
            't2.micro': 0.0116,
            't2.small': 0.023,
            't2.medium': 0.0464,
            't3.micro': 0.0104,
            't3.small': 0.0208,
            't3.medium': 0.0416,
        }
    
    def _calculate_monthly_cost(self, instance_type):
        """Calculate monthly cost for an instance"""
        hourly_cost = self.pricing.get(instance_type, 0.05)  # Default $0.05/hr
        return hourly_cost * 730  # Hours per month
    
    def _scan_ec2_zombies(self, region):
        """Scan for zombie EC2 instances"""
        zombies = []
        ec2 = boto3.client('ec2', region_name=region)
        
        try:
            response = ec2.describe_instances()
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    state = instance['State']['Name']
                    
                    # Stopped instances are zombies
                    if state == 'stopped':
                        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                        instance_type = instance.get('InstanceType', 't2.micro')
                        monthly_cost = self._calculate_monthly_cost(instance_type)
                        
                        zombies.append({
                            'type': 'EC2',
                            'id': instance['InstanceId'],
                            'name': tags.get('Name', 'Unnamed'),
                            'region': region,
                            'status': state,
                            'reason': 'Instance is stopped',
                            'instance_type': instance_type,
                            'monthly_cost': monthly_cost,
                            'launch_time': instance.get('LaunchTime'),
                            'tags': tags,
                            'details': {}
                        })
        except Exception as e:
            print(f"Error scanning EC2 in {region}: {e}")
        
        return zombies
    
    def _get_active_resources(self, regions):
        """Get list of active (running) EC2 instances for risk prediction"""
        active_resources = []
        
        for region in regions:
            try:
                ec2 = boto3.client('ec2', region_name=region)
                response = ec2.describe_instances(
                    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
                )
                
                for reservation in response['Reservations']:
                    for instance in reservation['Instances']:
                        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                        
                        active_resources.append({
                            'id': instance['InstanceId'],
                            'type': 'EC2',
                            'instance_type': instance['InstanceType'],
                            'state': instance['State'],
                            'launch_time': instance.get('LaunchTime'),
                            'region': region,
                            'tags': tags,
                            'name': tags.get('Name', 'Unnamed')
                        })
            except Exception as e:
                print(f"Error getting active resources in {region}: {e}")
        
        return active_resources
    
    def _save_to_database(self, scan_regions, zombies_data, duration, user_id):
        """Save zombie scan results to database"""
        from models.database import SessionLocal
        db = SessionLocal()
        
        try:
            total_cost = sum(z.get('monthly_cost', 0) for z in zombies_data)
            
            scan = Scan(
                user_id=user_id,
                scan_type='zombie',
                status='success',
                regions=scan_regions,
                total_resources=len(zombies_data),
                total_cost=total_cost,
                total_savings=0,
                duration_seconds=duration
            )
            db.add(scan)
            db.flush()
            
            for zombie in zombies_data:
                zombie_record = ZombieResource(
                    scan_id=scan.id,
                    resource_type=zombie.get('type', 'unknown'),
                    resource_id=zombie.get('id', 'unknown'),
                    name=zombie.get('name'),
                    region=zombie.get('region'),
                    status=zombie.get('status'),
                    reason=zombie.get('reason'),
                    instance_type=zombie.get('instance_type'),
                    monthly_cost=zombie.get('monthly_cost', 0),
                    details=zombie.get('details', {})
                )
                db.add(zombie_record)
            
            db.commit()
            db.refresh(scan)
            
            print(f"✅ Saved zombie scan to database (Scan ID: {scan.id})")
            return scan.id
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error saving to database: {e}")
            return None
        finally:
            db.close()
    
    async def scan(self, regions: list = None, user_id: int = None):
        """Run zombie resource scan with ML predictions"""
        start_time = time.time()
        
        try:
            scan_regions = regions or ['us-east-1', 'us-west-2']
            
            print(f"\n🔍 Starting Zombie Scan with ML Predictions...")
            print(f"📍 Regions: {', '.join(scan_regions)}\n")
            
            # Scan for zombies
            all_zombies = []
            for region in scan_regions:
                zombies = self._scan_ec2_zombies(region)
                all_zombies.extend(zombies)
            
            # Add ML predictions to each zombie
            for zombie in all_zombies:
                prediction = self.predictor.predict_zombie_probability(
                    resource=zombie,
                    region=zombie.get('region', 'us-east-1')
                )
                zombie['ml_prediction'] = prediction
            
            # Scan ACTIVE resources for risk prediction
            active_resources = self._get_active_resources(scan_regions)
            at_risk_resources = []
            
            for resource in active_resources:
                prediction = self.predictor.predict_zombie_probability(
                    resource=resource,
                    region=resource.get('region', 'us-east-1')
                )
                
                # Flag high-risk resources (>= 50% chance of becoming zombie)
                if prediction['zombie_probability'] >= 0.5:
                    resource['ml_prediction'] = prediction
                    at_risk_resources.append(resource)
            
            duration = time.time() - start_time
            
            # Save to database
            # Apply resource protection
            actual_zombies, protected_resources = self._apply_resource_protection(all_zombies, user_id)
            
            if protected_resources:
                print(f"   🛡️ Protected {len(protected_resources)} resources from being flagged as zombies")
            
            scan_id = self._save_to_database(scan_regions, actual_zombies, duration, user_id)
            
            # Calculate totals
            total_cost = sum(z.get('monthly_cost', 0) for z in actual_zombies)
            
            # Format response
            return {
                "status": "success",
                "scan_id": scan_id,
                "regions_scanned": scan_regions,
                "total_zombies": len(actual_zombies),
                "total_monthly_cost": total_cost,
                "zombies_found": {
                    "ec2": {
                        "count": len([z for z in actual_zombies if z['type'] == 'EC2']),
                        "zombies": [z for z in actual_zombies if z['type'] == 'EC2']
                    }
                },
                "zombies": actual_zombies,
                "protected_resources": protected_resources,
                "at_risk_resources": at_risk_resources,
                "at_risk_count": len(at_risk_resources),
                "scan_timestamp": datetime.utcnow().isoformat() + "Z",
                "duration_seconds": duration
            }
            
        except Exception as e:
            print(f"Zombie scan error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e)
            }

    def _apply_resource_protection(self, zombies: List[Dict], user_id: int) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter out protected resources from zombie list
        
        Args:
            zombies: List of detected zombies
            user_id: User ID for user-specific exclusions
            
        Returns:
            (actual_zombies, protected_resources)
        """
        from services.resource_protection_service import get_protection_service
        
        protection = get_protection_service()
        
        actual_zombies = []
        protected_resources = []
        
        for zombie in zombies:
            resource_id = zombie.get('resource_id')
            resource_name = zombie.get('resource_name')
            tags = zombie.get('tags', [])
            
            is_protected, reason = protection.is_protected(
                resource_id=resource_id,
                resource_name=resource_name,
                tags=tags,
                user_id=user_id
            )
            
            if is_protected:
                zombie['protection_reason'] = reason
                protected_resources.append(zombie)
                print(f"   🛡️ Protected: {resource_name or resource_id} - {reason}")
            else:
                actual_zombies.append(zombie)
        
        return actual_zombies, protected_resources
