"""
EC2 Analyzer - Collects and analyzes EC2 instance utilization metrics
"""

import boto3
from datetime import datetime, timedelta
import statistics
import pandas as pd


class EC2Analyzer:
    def __init__(self, region, config):
        self.region = region
        self.config = config
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        
        self.lookback_days = config['analysis']['lookback_days']
        self.cpu_percentile = config['analysis']['cpu_percentile']
        self.min_datapoints = config['analysis']['min_datapoints']
    
    def analyze_all_instances(self):
        """Analyze all running EC2 instances in the region"""
        print(f"🔍 Analyzing EC2 instances in {self.region}...")
        
        instances = self._get_running_instances()
        analysis_results = []
        
        for instance in instances:
            instance_id = instance['InstanceId']
            instance_type = instance['InstanceType']
            launch_time = instance['LaunchTime']
            
            # Get instance name
            name = self._get_instance_name(instance)
            
            print(f"   Analyzing {instance_id} ({name})...")
            
            # Collect metrics
            metrics = self._collect_metrics(instance_id)
            
            if metrics and self._has_sufficient_data(metrics):
                analysis = {
                    'instance_id': instance_id,
                    'name': name,
                    'region': self.region,
                    'instance_type': instance_type,
                    'launch_time': launch_time,
                    'metrics': metrics,
                    'current_cost': self._estimate_monthly_cost(instance_type)
                }
                analysis_results.append(analysis)
            else:
                print(f"      ⚠️  Insufficient data for {instance_id}")
        
        print(f"✅ Analyzed {len(analysis_results)} instances in {self.region}\n")
        return analysis_results
    
    def _get_running_instances(self):
        """Get all running EC2 instances"""
        response = self.ec2_client.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )
        
        instances = []
        for reservation in response['Reservations']:
            instances.extend(reservation['Instances'])
        
        return instances
    
    def _get_instance_name(self, instance):
        """Extract instance name from tags"""
        tags = instance.get('Tags', [])
        for tag in tags:
            if tag['Key'] == 'Name':
                return tag['Value']
        return 'N/A'
    
    def _collect_metrics(self, instance_id):
        """Collect CloudWatch metrics for an instance"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=self.lookback_days)
        
        metrics = {
            'cpu_utilization': self._get_metric_stats(
                instance_id, 'CPUUtilization', start_time, end_time
            ),
            'network_in': self._get_metric_stats(
                instance_id, 'NetworkIn', start_time, end_time
            ),
            'network_out': self._get_metric_stats(
                instance_id, 'NetworkOut', start_time, end_time
            ),
            'disk_read_bytes': self._get_metric_stats(
                instance_id, 'DiskReadBytes', start_time, end_time
            ),
            'disk_write_bytes': self._get_metric_stats(
                instance_id, 'DiskWriteBytes', start_time, end_time
            )
        }
        
        return metrics
    
    def _get_metric_stats(self, instance_id, metric_name, start_time, end_time):
        """Get statistics for a specific CloudWatch metric"""
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'InstanceId', 'Value': instance_id}
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
                'values': averages  # For detailed analysis
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
        
        # Linear interpolation
        return sorted_data[floor_index] + (index - floor_index) * (
            sorted_data[ceil_index] - sorted_data[floor_index]
        )
    
    def _has_sufficient_data(self, metrics):
        """Check if we have enough data points for analysis"""
        if not metrics.get('cpu_utilization'):
            return False
        
        cpu_datapoints = metrics['cpu_utilization']['datapoints']
        return cpu_datapoints >= self.min_datapoints
    
    def _estimate_monthly_cost(self, instance_type):
        """Estimate monthly cost (simplified pricing)"""
        pricing = {
            't3.micro': 0.0104,
            't3.small': 0.0208,
            't3.medium': 0.0416,
            't3.large': 0.0832,
            't3.xlarge': 0.1664,
            't3.2xlarge': 0.3328,
            't3a.micro': 0.0094,
            't3a.small': 0.0188,
            't3a.medium': 0.0376,
            't3a.large': 0.0752,
            'm5.large': 0.096,
            'm5.xlarge': 0.192,
            'm5.2xlarge': 0.384,
            'm5a.large': 0.086,
            'm5a.xlarge': 0.172,
            'c5.large': 0.085,
            'c5.xlarge': 0.17,
            'c5.2xlarge': 0.34,
            'r5.large': 0.126,
            'r5.xlarge': 0.252,
        }
        
        hourly_rate = pricing.get(instance_type, 0.10)
        hours_per_month = 730
        return hourly_rate * hours_per_month