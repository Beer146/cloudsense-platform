"""
S3 Bucket Compliance Scanner
"""
import boto3


class S3ComplianceScanner:
    def __init__(self, region, config):
        self.region = region
        self.config = config
        self.s3_client = boto3.client('s3', region_name=region)
        self.rules = config['rules']['s3']
    
    def scan(self):
        """Scan S3 buckets for compliance violations"""
        print(f"🔍 Scanning S3 buckets in {self.region}...")
        
        violations = []
        
        try:
            # Get all buckets (S3 is global, but we'll check from this region)
            if self.region != 'us-east-1':
                # Only scan from one region to avoid duplicates
                return violations
            
            response = self.s3_client.list_buckets()
            buckets = response.get('Buckets', [])
            
            for bucket in buckets:
                bucket_name = bucket['Name']
                bucket_violations = self._check_bucket(bucket_name)
                violations.extend(bucket_violations)
            
            print(f"✅ Found {len(violations)} S3 compliance violations")
            return violations
            
        except Exception as e:
            print(f"❌ Error scanning S3: {str(e)}")
            return []
    
    def _check_bucket(self, bucket_name):
        """Check a single bucket for compliance"""
        violations = []
        
        try:
            # Check encryption
            if self.rules.get('require_encryption'):
                if not self._has_encryption(bucket_name):
                    violations.append({
                        'resource_type': 'S3',
                        'resource_id': bucket_name,
                        'violation': 'unencrypted',
                        'severity': 'high',
                        'description': f'S3 bucket "{bucket_name}" is not encrypted',
                        'remediation': 'Enable default encryption on the bucket'
                    })
            
            # Check public access
            if self.rules.get('block_public_access'):
                if self._is_public(bucket_name):
                    violations.append({
                        'resource_type': 'S3',
                        'resource_id': bucket_name,
                        'violation': 'public_access',
                        'severity': 'critical',
                        'description': f'S3 bucket "{bucket_name}" allows public access',
                        'remediation': 'Enable "Block all public access" on the bucket'
                    })
            
            # Check versioning
            if self.rules.get('require_versioning'):
                if not self._has_versioning(bucket_name):
                    violations.append({
                        'resource_type': 'S3',
                        'resource_id': bucket_name,
                        'violation': 'no_versioning',
                        'severity': 'low',
                        'description': f'S3 bucket "{bucket_name}" does not have versioning enabled',
                        'remediation': 'Enable versioning on the bucket'
                    })
        
        except Exception as e:
            print(f"   ⚠️  Error checking bucket {bucket_name}: {str(e)}")
        
        return violations
    
    def _has_encryption(self, bucket_name):
        """Check if bucket has encryption enabled"""
        try:
            self.s3_client.get_bucket_encryption(Bucket=bucket_name)
            return True
        except self.s3_client.exceptions.ServerSideEncryptionConfigurationNotFoundError:
            return False
        except Exception:
            return False
    
    def _is_public(self, bucket_name):
        """Check if bucket allows public access"""
        try:
            # Check public access block
            response = self.s3_client.get_public_access_block(Bucket=bucket_name)
            config = response['PublicAccessBlockConfiguration']
            
            # If all are True, bucket is private
            if all([
                config.get('BlockPublicAcls', False),
                config.get('IgnorePublicAcls', False),
                config.get('BlockPublicPolicy', False),
                config.get('RestrictPublicBuckets', False)
            ]):
                return False
            
            return True
            
        except self.s3_client.exceptions.NoSuchPublicAccessBlockConfiguration:
            # No block = potentially public
            return True
        except Exception:
            return False
    
    def _has_versioning(self, bucket_name):
        """Check if bucket has versioning enabled"""
        try:
            response = self.s3_client.get_bucket_versioning(Bucket=bucket_name)
            return response.get('Status') == 'Enabled'
        except Exception:
            return False
