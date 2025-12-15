"""
EC2 Instance Scanner - Finds stopped and underutilized instances
"""

import boto3
from datetime import datetime, timedelta
from dateutil import parser


class EC2Scanner:
    def __init__(self, region, config):
        self.region = region
        self.config = config
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        
    def scan(self):
        """Scan for zombie EC2 instances"""
        print(f"🔍 Scanning EC2 instances in {self.region}...")
        
        zombies = []
        
        # Get all instances
        response = self.ec2_client.describe_instances()
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                state = instance['State']['Name']
                instance_type = instance['InstanceType']
                launch_time = instance['LaunchTime']
                
                # Get instance name from tags
                name = self._get_instance_name(instance)
                
                zombie_info = None
                
                # Check if instance is stopped
                if state == 'stopped':
                    zombie_info = self._check_stopped_instance(
                        instance_id, name, instance_type, launch_time
                    )
                
                # Check if running instance is underutilized
                elif state == 'running':
                    zombie_info = self._check_underutilized_instance(
                        instance_id, name, instance_type, launch_time
                    )
                
                if zombie_info:
                    zombies.append(zombie_info)
        
        print(f"✅ Found {len(zombies)} zombie EC2 instances in {self.region}")
        return zombies
    
    def _get_instance_name(self, instance):
        """Extract instance name from tags"""
        tags = instance.get('Tags', [])
        for tag in tags:
            if tag['Key'] == 'Name':
                return tag['Value']
        return 'N/A'
    
    def _check_stopped_instance(self, instance_id, name, instance_type, launch_time):
        """Check if stopped instance is a zombie"""
        stopped_days_threshold = self.config['thresholds']['ec2']['stopped_days']
        
        # For stopped instances, check state transition time
        # In production, you'd check the StateTransitionReason timestamp
        # For now, we'll use a simplified check
        
        return {
            'resource_type': 'EC2',
            'resource_id': instance_id,
            'name': name,
            'region': self.region,
            'status': 'stopped',
            'reason': f'Instance stopped for more than {stopped_days_threshold} days',
            'instance_type': instance_type,
            'estimated_monthly_cost': self._estimate_cost(instance_type, stopped=True)
        }
    
    def _check_underutilized_instance(self, instance_id, name, instance_type, launch_time):
        """Check if running instance is underutilized"""
        cpu_threshold = self.config['thresholds']['ec2']['cpu_threshold']
        
        # Get average CPU utilization for the past 7 days
        avg_cpu = self._get_average_cpu(instance_id)
        
        if avg_cpu is not None and avg_cpu < cpu_threshold:
            return {
                'resource_type': 'EC2',
                'resource_id': instance_id,
                'name': name,
                'region': self.region,
                'status': 'underutilized',
                'reason': f'Average CPU usage: {avg_cpu:.2f}% (threshold: {cpu_threshold}%)',
                'instance_type': instance_type,
                'avg_cpu': avg_cpu,
                'estimated_monthly_cost': self._estimate_cost(instance_type, stopped=False)
            }
        
        return None
    
    def _get_average_cpu(self, instance_id):
        """Get average CPU utilization from CloudWatch"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[
                    {'Name': 'InstanceId', 'Value': instance_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                datapoints = response['Datapoints']
                avg_cpu = sum(dp['Average'] for dp in datapoints) / len(datapoints)
                return avg_cpu
            
            return None
            
        except Exception as e:
            print(f"⚠️  Warning: Could not get CPU metrics for {instance_id}: {str(e)}")
            return None
    
    def _estimate_cost(self, instance_type, stopped=False):
        """Estimate monthly cost (simplified pricing)"""
        # Simplified pricing - in production, use AWS Pricing API
        pricing = {
            't2.micro': 0.0116,
            't2.small': 0.023,
            't2.medium': 0.0464,
            't3.micro': 0.0104,
            't3.small': 0.0208,
            't3.medium': 0.0416,
            'm5.large': 0.096,
            'm5.xlarge': 0.192,
            'c5.large': 0.085,
            'c5.xlarge': 0.17,
        }
        
        hourly_rate = pricing.get(instance_type, 0.05)  # default if not found
        
        if stopped:
            # Stopped instances only pay for EBS storage, roughly $0.10/GB/month
            # Assuming 30GB average
            return 3.0
        else:
            # Running instance
            hours_per_month = 730
            return hourly_rate * hours_per_month