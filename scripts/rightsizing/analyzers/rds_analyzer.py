"""
RDS Analyzer - Collects and analyzes RDS instance utilization metrics
"""

import boto3
from datetime import datetime, timedelta
import statistics


class RDSAnalyzer:
    def __init__(self, region, config):
        self.region = region
        self.config = config
        self.rds_client = boto3.client('rds', region_name=region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        
        self.lookback_days = config['analysis']['lookback_days']
        self.cpu_percentile = config['analysis']['cpu_percentile']
        self.min_datapoints = config['analysis']['min_datapoints']
    
    def analyze_all_instances(self):
        """Analyze all RDS instances in the region"""
        print(f"🔍 Analyzing RDS instances in {self.region}...")
        
        instances = self._get_rds_instances()
        analysis_results = []
        
        for instance in instances:
            db_identifier = instance['DBInstanceIdentifier']
            db_instance_class = instance['DBInstanceClass']
            engine = instance['Engine']
            
            print(f"   Analyzing {db_identifier}...")
            
            # Collect metrics
            metrics = self._collect_metrics(db_identifier)
            
            if metrics and self._has_sufficient_data(metrics):
                analysis = {
                    'db_identifier': db_identifier,
                    'region': self.region,
                    'instance_class': db_instance_class,
                    'engine': engine,
                    'multi_az': instance.get('MultiAZ', False),
                    'storage_type': instance.get('StorageType', 'gp2'),
                    'allocated_storage': instance.get('AllocatedStorage', 0),
                    'metrics': metrics,
                    'current_cost': self._estimate_monthly_cost(db_instance_class, engine)
                }
                analysis_results.append(analysis)
            else:
                print(f"      ⚠️  Insufficient data for {db_identifier}")
        
        print(f"✅ Analyzed {len(analysis_results)} RDS instances in {self.region}\n")
        return analysis_results
    
    def _get_rds_instances(self):
        """Get all RDS instances"""
        response = self.rds_client.describe_db_instances()
        return [db for db in response['DBInstances'] if db['DBInstanceStatus'] == 'available']
    
    def _collect_metrics(self, db_identifier):
        """Collect CloudWatch metrics for an RDS instance"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=self.lookback_days)
        
        metrics = {
            'cpu_utilization': self._get_metric_stats(
                db_identifier, 'CPUUtilization', start_time, end_time
            ),
            'database_connections': self._get_metric_stats(
                db_identifier, 'DatabaseConnections', start_time, end_time
            ),
            'read_iops': self._get_metric_stats(
                db_identifier, 'ReadIOPS', start_time, end_time
            ),
            'write_iops': self._get_metric_stats(
                db_identifier, 'WriteIOPS', start_time, end_time
            ),
            'freeable_memory': self._get_metric_stats(
                db_identifier, 'FreeableMemory', start_time, end_time
            )
        }
        
        return metrics
    
    def _get_metric_stats(self, db_identifier, metric_name, start_time, end_time):
        """Get statistics for a specific CloudWatch metric"""
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'DBInstanceIdentifier', 'Value': db_identifier}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=['Average', 'Maximum', 'Minimum']
            )
            
            if not response['Datapoints']:
                return None
            
            datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
            
            averages = [dp['Average'] for dp in datapoints]
            maximums = [dp['Maximum'] for dp in datapoints]
            
            return {
                'datapoints': len(datapoints),
                'average': statistics.mean(averages),
                'max': max(maximums),
                'min': min([dp['Minimum'] for dp in datapoints]),
                'p95': self._percentile(averages, self.cpu_percentile),
                'values': averages
            }
            
        except Exception as e:
            print(f"      ⚠️  Error getting {metric_name}: {str(e)}")
            return None
    
    def _percentile(self, data, percentile):
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (len(sorted_data) - 1) * percentile / 100
        floor_index = int(index)
        ceil_index = floor_index + 1
        
        if ceil_index >= len(sorted_data):
            return sorted_data[floor_index]
        
        return sorted_data[floor_index] + (index - floor_index) * (
            sorted_data[ceil_index] - sorted_data[floor_index]
        )
    
    def _has_sufficient_data(self, metrics):
        """Check if we have enough data points for analysis"""
        if not metrics.get('cpu_utilization'):
            return False
        
        cpu_datapoints = metrics['cpu_utilization']['datapoints']
        return cpu_datapoints >= self.min_datapoints
    
    def _estimate_monthly_cost(self, instance_class, engine):
        """Estimate monthly cost for RDS instance"""
        base_pricing = {
            'db.t3.micro': 0.017,
            'db.t3.small': 0.034,
            'db.t3.medium': 0.068,
            'db.t3.large': 0.136,
            'db.t2.micro': 0.017,
            'db.t2.small': 0.034,
            'db.m5.large': 0.174,
            'db.m5.xlarge': 0.348,
            'db.r5.large': 0.24,
            'db.r5.xlarge': 0.48,
        }
        
        hourly_rate = base_pricing.get(instance_class, 0.10)
        
        # Oracle/SQL Server cost more
        if 'oracle' in engine.lower() or 'sqlserver' in engine.lower():
            hourly_rate *= 2
        
        hours_per_month = 730
        return hourly_rate * hours_per_month