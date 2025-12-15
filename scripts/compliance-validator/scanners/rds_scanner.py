"""
RDS Compliance Scanner
"""
import boto3


class RDSComplianceScanner:
    def __init__(self, region, config):
        self.region = region
        self.config = config
        self.rds_client = boto3.client('rds', region_name=region)
        self.rules = config['rules']['rds']
    
    def scan(self):
        """Scan RDS instances for compliance violations"""
        print(f"🔍 Scanning RDS instances in {self.region}...")
        
        violations = []
        
        try:
            response = self.rds_client.describe_db_instances()
            instances = response.get('DBInstances', [])
            
            for instance in instances:
                instance_violations = self._check_instance(instance)
                violations.extend(instance_violations)
            
            print(f"✅ Found {len(violations)} RDS compliance violations")
            return violations
            
        except Exception as e:
            print(f"❌ Error scanning RDS: {str(e)}")
            return []
    
    def _check_instance(self, instance):
        """Check a single RDS instance for compliance"""
        violations = []
        instance_id = instance['DBInstanceIdentifier']
        
        # Check if publicly accessible
        if self.rules.get('block_public_access'):
            if instance.get('PubliclyAccessible', False):
                violations.append({
                    'resource_type': 'RDS',
                    'resource_id': instance_id,
                    'violation': 'publicly_accessible',
                    'severity': 'critical',
                    'description': f'RDS instance "{instance_id}" is publicly accessible',
                    'remediation': 'Disable public accessibility in instance settings'
                })
        
        # Check encryption
        if self.rules.get('require_encryption'):
            if not instance.get('StorageEncrypted', False):
                violations.append({
                    'resource_type': 'RDS',
                    'resource_id': instance_id,
                    'violation': 'unencrypted',
                    'severity': 'high',
                    'description': f'RDS instance "{instance_id}" is not encrypted',
                    'remediation': 'Enable encryption (requires recreating instance)'
                })
        
        # Check backup retention
        if self.rules.get('require_backup'):
            retention = instance.get('BackupRetentionPeriod', 0)
            min_retention = self.rules.get('backup_retention_days', 7)
            
            if retention < min_retention:
                violations.append({
                    'resource_type': 'RDS',
                    'resource_id': instance_id,
                    'violation': 'insufficient_backup',
                    'severity': 'medium',
                    'description': f'RDS instance "{instance_id}" backup retention is {retention} days (minimum: {min_retention})',
                    'remediation': f'Set backup retention period to at least {min_retention} days'
                })
        
        return violations
