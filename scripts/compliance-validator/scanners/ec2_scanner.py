"""
EC2 Compliance Scanner
"""
import boto3


class EC2ComplianceScanner:
    def __init__(self, region, config):
        self.region = region
        self.config = config
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.rules = config['rules']['ec2']
    
    def scan(self):
        """Scan EC2 instances for compliance violations"""
        print(f"🔍 Scanning EC2 instances in {self.region}...")
        
        violations = []
        
        try:
            response = self.ec2_client.describe_instances()
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_violations = self._check_instance(instance)
                    violations.extend(instance_violations)
            
            print(f"✅ Found {len(violations)} EC2 compliance violations")
            return violations
            
        except Exception as e:
            print(f"❌ Error scanning EC2: {str(e)}")
            return []
    
    def _check_instance(self, instance):
        """Check a single EC2 instance for compliance"""
        violations = []
        instance_id = instance['InstanceId']
        
        # Check required tags
        required_tags = self.rules.get('required_tags', [])
        instance_tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
        
        missing_tags = [tag for tag in required_tags if tag not in instance_tags]
        
        if missing_tags:
            violations.append({
                'resource_type': 'EC2',
                'resource_id': instance_id,
                'violation': 'missing_tags',
                'severity': 'medium',
                'description': f'EC2 instance "{instance_id}" missing required tags: {", ".join(missing_tags)}',
                'remediation': f'Add tags: {", ".join(missing_tags)}'
            })
        
        # Check EBS encryption
        if self.rules.get('require_encryption'):
            for bdm in instance.get('BlockDeviceMappings', []):
                ebs = bdm.get('Ebs', {})
                if not ebs.get('Encrypted', False):
                    violations.append({
                        'resource_type': 'EC2',
                        'resource_id': instance_id,
                        'violation': 'unencrypted_volume',
                        'severity': 'high',
                        'description': f'EC2 instance "{instance_id}" has unencrypted EBS volume',
                        'remediation': 'Enable EBS encryption for volumes'
                    })
                    break  # Only report once per instance
        
        return violations
