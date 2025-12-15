"""
EBS Volume Scanner - Finds unattached and unused volumes
"""

import boto3
from datetime import datetime, timedelta


class EBSScanner:
    def __init__(self, region, config):
        self.region = region
        self.config = config
        self.ec2_client = boto3.client('ec2', region_name=region)
        
    def scan(self):
        """Scan for zombie EBS volumes"""
        print(f"🔍 Scanning EBS volumes in {self.region}...")
        
        zombies = []
        
        # Get all volumes
        response = self.ec2_client.describe_volumes()
        
        for volume in response['Volumes']:
            volume_id = volume['VolumeId']
            state = volume['State']
            size = volume['Size']
            volume_type = volume['VolumeType']
            create_time = volume['CreateTime']
            
            # Get volume name from tags
            name = self._get_volume_name(volume)
            
            # Check if volume is unattached
            if state == 'available':
                zombie_info = self._check_unattached_volume(
                    volume_id, name, size, volume_type, create_time
                )
                
                if zombie_info:
                    zombies.append(zombie_info)
        
        print(f"✅ Found {len(zombies)} zombie EBS volumes in {self.region}")
        return zombies
    
    def _get_volume_name(self, volume):
        """Extract volume name from tags"""
        tags = volume.get('Tags', [])
        for tag in tags:
            if tag['Key'] == 'Name':
                return tag['Value']
        return 'N/A'
    
    def _check_unattached_volume(self, volume_id, name, size, volume_type, create_time):
        """Check if unattached volume is a zombie"""
        unattached_days_threshold = self.config['thresholds']['ebs']['unattached_days']
        
        # Calculate how long it's been unattached
        days_unattached = (datetime.now(create_time.tzinfo) - create_time).days
        
        if days_unattached >= unattached_days_threshold:
            return {
                'resource_type': 'EBS',
                'resource_id': volume_id,
                'name': name,
                'region': self.region,
                'status': 'unattached',
                'reason': f'Volume unattached for {days_unattached} days (threshold: {unattached_days_threshold})',
                'size_gb': size,
                'volume_type': volume_type,
                'days_unattached': days_unattached,
                'estimated_monthly_cost': self._estimate_cost(size, volume_type)
            }
        
        return None
    
    def _estimate_cost(self, size_gb, volume_type):
        """Estimate monthly cost for EBS volume"""
        # Simplified pricing per GB/month
        pricing = {
            'gp2': 0.10,
            'gp3': 0.08,
            'io1': 0.125,
            'io2': 0.125,
            'st1': 0.045,
            'sc1': 0.015,
            'standard': 0.05
        }
        
        price_per_gb = pricing.get(volume_type, 0.10)
        return size_gb * price_per_gb