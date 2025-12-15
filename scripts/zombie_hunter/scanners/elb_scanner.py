"""
ELB Scanner - Finds unused load balancers
"""

import boto3
from datetime import datetime, timedelta


class ELBScanner:
    def __init__(self, region, config):
        self.region = region
        self.config = config
        # ELBv2 for Application and Network Load Balancers
        self.elbv2_client = boto3.client('elbv2', region_name=region)
        # Classic Load Balancers
        self.elb_client = boto3.client('elb', region_name=region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        
    def scan(self):
        """Scan for zombie load balancers"""
        print(f"🔍 Scanning load balancers in {self.region}...")
        
        zombies = []
        
        # Scan Application/Network Load Balancers (ELBv2)
        zombies.extend(self._scan_elbv2())
        
        # Scan Classic Load Balancers
        zombies.extend(self._scan_classic_elb())
        
        print(f"✅ Found {len(zombies)} zombie load balancers in {self.region}")
        return zombies
    
    def _scan_elbv2(self):
        """Scan Application and Network Load Balancers"""
        zombies = []
        
        try:
            response = self.elbv2_client.describe_load_balancers()
            
            for lb in response['LoadBalancers']:
                lb_arn = lb['LoadBalancerArn']
                lb_name = lb['LoadBalancerName']
                lb_type = lb['Type']
                created_time = lb['CreatedTime']
                
                zombie_info = self._check_unused_elbv2(
                    lb_arn, lb_name, lb_type, created_time
                )
                
                if zombie_info:
                    zombies.append(zombie_info)
                    
        except Exception as e:
            print(f"⚠️  Warning: Could not scan ELBv2 in {self.region}: {str(e)}")
        
        return zombies
    
    def _scan_classic_elb(self):
        """Scan Classic Load Balancers"""
        zombies = []
        
        try:
            response = self.elb_client.describe_load_balancers()
            
            for lb in response['LoadBalancerDescriptions']:
                lb_name = lb['LoadBalancerName']
                created_time = lb['CreatedTime']
                
                zombie_info = self._check_unused_classic_elb(
                    lb_name, created_time
                )
                
                if zombie_info:
                    zombies.append(zombie_info)
                    
        except Exception as e:
            print(f"⚠️  Warning: Could not scan Classic ELB in {self.region}: {str(e)}")
        
        return zombies
    
    def _check_unused_elbv2(self, lb_arn, lb_name, lb_type, created_time):
        """Check if ELBv2 is unused based on request count"""
        request_threshold = self.config['thresholds']['elb']['request_threshold']
        
        # Get average request count
        avg_requests = self._get_elbv2_request_count(lb_arn, lb_type)
        
        if avg_requests is not None and avg_requests < request_threshold:
            return {
                'resource_type': 'ELB',
                'resource_id': lb_name,
                'name': lb_name,
                'region': self.region,
                'status': 'unused',
                'reason': f'Average requests: {avg_requests:.2f} (threshold: {request_threshold})',
                'lb_type': lb_type,
                'avg_requests': avg_requests,
                'estimated_monthly_cost': self._estimate_cost(lb_type)
            }
        
        return None
    
    def _check_unused_classic_elb(self, lb_name, created_time):
        """Check if Classic ELB is unused"""
        request_threshold = self.config['thresholds']['elb']['request_threshold']
        
        avg_requests = self._get_classic_elb_request_count(lb_name)
        
        if avg_requests is not None and avg_requests < request_threshold:
            return {
                'resource_type': 'ELB',
                'resource_id': lb_name,
                'name': lb_name,
                'region': self.region,
                'status': 'unused',
                'reason': f'Average requests: {avg_requests:.2f} (threshold: {request_threshold})',
                'lb_type': 'classic',
                'avg_requests': avg_requests,
                'estimated_monthly_cost': self._estimate_cost('classic')
            }
        
        return None
    
    def _get_elbv2_request_count(self, lb_arn, lb_type):
        """Get request count for ALB/NLB from CloudWatch"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            # Metric name differs by type
            metric_name = 'RequestCount' if lb_type == 'application' else 'ProcessedBytes'
            
            # Extract load balancer name from ARN for dimensions
            lb_name = lb_arn.split(':loadbalancer/')[-1]
            
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ApplicationELB' if lb_type == 'application' else 'AWS/NetworkELB',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'LoadBalancer', 'Value': lb_name}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Sum']
            )
            
            if response['Datapoints']:
                datapoints = response['Datapoints']
                total = sum(dp['Sum'] for dp in datapoints)
                avg_per_day = total / len(datapoints) if datapoints else 0
                return avg_per_day
            
            return 0
            
        except Exception as e:
            print(f"⚠️  Warning: Could not get metrics for {lb_arn}: {str(e)}")
            return None
    
    def _get_classic_elb_request_count(self, lb_name):
        """Get request count for Classic ELB"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ELB',
                MetricName='RequestCount',
                Dimensions=[
                    {'Name': 'LoadBalancerName', 'Value': lb_name}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Sum']
            )
            
            if response['Datapoints']:
                datapoints = response['Datapoints']
                total = sum(dp['Sum'] for dp in datapoints)
                avg_per_day = total / len(datapoints) if datapoints else 0
                return avg_per_day
            
            return 0
            
        except Exception as e:
            print(f"⚠️  Warning: Could not get metrics for {lb_name}: {str(e)}")
            return None
    
    def _estimate_cost(self, lb_type):
        """Estimate monthly cost for load balancer"""
        # Simplified pricing per hour
        pricing = {
            'application': 0.0225,  # ALB
            'network': 0.0225,      # NLB
            'classic': 0.025,       # Classic ELB
        }
        
        hourly_rate = pricing.get(lb_type, 0.025)
        hours_per_month = 730
        
        # Base cost + LCU costs (simplified)
        return (hourly_rate * hours_per_month) + 5  # +$5 for minimal LCU usage