"""
RDS Instance Scanner - Finds idle database instances
"""

import boto3
from datetime import datetime, timedelta


class RDSScanner:
    def __init__(self, region, config):
        self.region = region
        self.config = config
        self.rds_client = boto3.client('rds', region_name=region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        
    def scan(self):
        """Scan for zombie RDS instances"""
        print(f"🔍 Scanning RDS instances in {self.region}...")
        
        zombies = []
        
        # Get all RDS instances
        response = self.rds_client.describe_db_instances()
        
        for db_instance in response['DBInstances']:
            db_identifier = db_instance['DBInstanceIdentifier']
            db_instance_class = db_instance['DBInstanceClass']
            engine = db_instance['Engine']
            status = db_instance['DBInstanceStatus']
            create_time = db_instance['InstanceCreateTime']
            
            # Only check available instances
            if status == 'available':
                zombie_info = self._check_idle_database(
                    db_identifier, db_instance_class, engine, create_time
                )
                
                if zombie_info:
                    zombies.append(zombie_info)
        
        print(f"✅ Found {len(zombies)} zombie RDS instances in {self.region}")
        return zombies
    
    def _check_idle_database(self, db_identifier, db_instance_class, engine, create_time):
        """Check if database is idle based on connections"""
        connection_threshold = self.config['thresholds']['rds']['connection_threshold']
        
        # Get average database connections for the past 7 days
        avg_connections = self._get_average_connections(db_identifier)
        
        if avg_connections is not None and avg_connections < connection_threshold:
            return {
                'resource_type': 'RDS',
                'resource_id': db_identifier,
                'name': db_identifier,
                'region': self.region,
                'status': 'idle',
                'reason': f'Average connections: {avg_connections:.2f} (threshold: {connection_threshold})',
                'instance_class': db_instance_class,
                'engine': engine,
                'avg_connections': avg_connections,
                'estimated_monthly_cost': self._estimate_cost(db_instance_class, engine)
            }
        
        return None
    
    def _get_average_connections(self, db_identifier):
        """Get average database connections from CloudWatch"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='DatabaseConnections',
                Dimensions=[
                    {'Name': 'DBInstanceIdentifier', 'Value': db_identifier}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                datapoints = response['Datapoints']
                avg_connections = sum(dp['Average'] for dp in datapoints) / len(datapoints)
                return avg_connections
            
            return None
            
        except Exception as e:
            print(f"⚠️  Warning: Could not get connection metrics for {db_identifier}: {str(e)}")
            return None
    
    def _estimate_cost(self, instance_class, engine):
        """Estimate monthly cost for RDS instance"""
        # Simplified pricing - varies by engine and instance class
        # These are approximate on-demand prices per hour
        base_pricing = {
            'db.t3.micro': 0.017,
            'db.t3.small': 0.034,
            'db.t3.medium': 0.068,
            'db.t2.micro': 0.017,
            'db.t2.small': 0.034,
            'db.t2.medium': 0.068,
            'db.m5.large': 0.174,
            'db.m5.xlarge': 0.348,
            'db.r5.large': 0.24,
            'db.r5.xlarge': 0.48,
        }
        
        hourly_rate = base_pricing.get(instance_class, 0.10)
        
        # MySQL/PostgreSQL are cheaper than Oracle/SQL Server
        if 'oracle' in engine.lower() or 'sqlserver' in engine.lower():
            hourly_rate *= 2
        
        hours_per_month = 730
        return hourly_rate * hours_per_month