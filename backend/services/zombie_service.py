"""
Zombie Resource Hunter Service
Wrapper for the zombie hunter scanner
"""
import sys
from pathlib import Path
from datetime import datetime
import yaml
import time

# Add scripts to Python path
scripts_path = Path(__file__).parent.parent.parent / "scripts" / "zombie_hunter"
sys.path.insert(0, str(scripts_path))

# Import from zombie_hunter
from scanners import EC2Scanner, EBSScanner, RDSScanner, ELBScanner
from cost_calculator import CostCalculator

# Import database models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Scan, ZombieResource, get_db


class ZombieHunterService:
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
                'thresholds': {
                    'ec2': {'stopped_days': 7, 'cpu_threshold': 5},
                    'ebs': {'unattached_days': 7},
                    'rds': {'idle_days': 7, 'connection_threshold': 1},
                    'elb': {'no_traffic_days': 7, 'request_threshold': 10}
                }
            }
    
    def _scan_resources(self, regions, resource_types=None):
        """Scan for zombie resources"""
        all_zombies = []
        
        for region in regions:
            print(f"Scanning {region}...")
            
            scanners_to_run = []
            
            if resource_types is None or 'ec2' in resource_types:
                scanners_to_run.append(('EC2', EC2Scanner(region, self.config)))
            
            if resource_types is None or 'ebs' in resource_types:
                scanners_to_run.append(('EBS', EBSScanner(region, self.config)))
            
            if resource_types is None or 'rds' in resource_types:
                scanners_to_run.append(('RDS', RDSScanner(region, self.config)))
            
            if resource_types is None or 'elb' in resource_types:
                scanners_to_run.append(('ELB', ELBScanner(region, self.config)))
            
            for scanner_name, scanner in scanners_to_run:
                try:
                    zombies = scanner.scan()
                    all_zombies.extend(zombies)
                    print(f"Found {len(zombies)} {scanner_name} zombies in {region}")
                except Exception as e:
                    print(f"Error scanning {scanner_name} in {region}: {str(e)}")
        
        return all_zombies
    
    def _save_to_database(self, scan_regions, zombies, cost_summary, duration):
        """Save scan results to database"""
        from models.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Create scan record
            scan = Scan(
                scan_type='zombie',
                status='success',
                regions=scan_regions,
                total_resources=len(zombies),
                total_cost=cost_summary.get('total_monthly_savings', 0),
                total_savings=cost_summary.get('total_annual_savings', 0),
                duration_seconds=duration
            )
            db.add(scan)
            db.flush()  # Get scan ID
            
            # Create zombie resource records
            for zombie in zombies:
                zombie_record = ZombieResource(
                    scan_id=scan.id,
                    resource_type=zombie.get('resource_type', 'unknown'),
                    resource_id=zombie.get('resource_id', 'unknown'),
                    name=zombie.get('name', 'N/A'),
                    region=zombie.get('region', 'unknown'),
                    status=zombie.get('status', 'unknown'),
                    reason=zombie.get('reason', ''),
                    instance_type=zombie.get('instance_type'),
                    monthly_cost=zombie.get('estimated_monthly_cost', zombie.get('monthly_cost', 0)),
                    details=zombie  # Store full zombie data as JSON
                )
                db.add(zombie_record)
            
            db.commit()
            print(f"✅ Saved scan results to database (Scan ID: {scan.id})")
            return scan.id
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error saving to database: {e}")
            return None
        finally:
            db.close()
    
    async def run_scan(self, regions: list = None):
        """Run zombie resource scan"""
        start_time = time.time()
        
        try:
            scan_regions = regions or self.config['aws']['regions']
            
            # Scan for zombies
            zombies = self._scan_resources(scan_regions)
            
            print(f"\nTotal zombies found: {len(zombies)}")
            for zombie in zombies:
                cost = zombie.get('estimated_monthly_cost', zombie.get('monthly_cost', 0))
                print(f"  - {zombie.get('resource_type', 'unknown')}: {zombie.get('resource_id', 'unknown')} - ${cost:.2f}/mo")
            
            # Calculate costs
            calculator = CostCalculator()
            cost_summary = calculator.calculate_total_savings(zombies)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Save to database
            scan_id = self._save_to_database(scan_regions, zombies, cost_summary, duration)
            
            # Count by type and calculate costs
            ec2_zombies = [z for z in zombies if z.get('resource_type') == 'EC2']
            ebs_zombies = [z for z in zombies if z.get('resource_type') == 'EBS']
            rds_zombies = [z for z in zombies if z.get('resource_type') == 'RDS']
            elb_zombies = [z for z in zombies if z.get('resource_type') == 'ELB']
            
            def get_cost(zombie):
                return zombie.get('estimated_monthly_cost', zombie.get('monthly_cost', 0))
            
            # Format response
            results = {
                "status": "success",
                "scan_id": scan_id,
                "regions_scanned": scan_regions,
                "zombies_found": {
                    "ec2": {
                        "count": len(ec2_zombies),
                        "stopped_instances": len(ec2_zombies),
                        "monthly_cost": sum([get_cost(z) for z in ec2_zombies]),
                        "details": ec2_zombies
                    },
                    "ebs": {
                        "count": len(ebs_zombies),
                        "unattached_volumes": len(ebs_zombies),
                        "monthly_cost": sum([get_cost(z) for z in ebs_zombies]),
                        "details": ebs_zombies
                    },
                    "rds": {
                        "count": len(rds_zombies),
                        "idle_databases": len(rds_zombies),
                        "monthly_cost": sum([get_cost(z) for z in rds_zombies]),
                        "details": rds_zombies
                    },
                    "elb": {
                        "count": len(elb_zombies),
                        "unused_load_balancers": len(elb_zombies),
                        "monthly_cost": sum([get_cost(z) for z in elb_zombies]),
                        "details": elb_zombies
                    }
                },
                "total_zombies": len(zombies),
                "total_monthly_cost": cost_summary.get('total_monthly_savings', 0),
                "total_annual_cost": cost_summary.get('total_annual_savings', 0),
                "scan_timestamp": datetime.utcnow().isoformat() + "Z",
                "duration_seconds": duration
            }
            
            return results
            
        except Exception as e:
            print(f"Scan error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e)
            }
