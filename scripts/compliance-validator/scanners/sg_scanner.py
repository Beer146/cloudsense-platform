"""
Security Group Compliance Scanner
"""
import boto3


class SecurityGroupScanner:
    def __init__(self, region, config):
        self.region = region
        self.config = config
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.rules = config['rules']['security_groups']
    
    def scan(self):
        """Scan security groups for compliance violations"""
        print(f"🔍 Scanning security groups in {self.region}...")
        
        violations = []
        
        try:
            response = self.ec2_client.describe_security_groups()
            security_groups = response.get('SecurityGroups', [])
            
            for sg in security_groups:
                sg_violations = self._check_security_group(sg)
                violations.extend(sg_violations)
            
            print(f"✅ Found {len(violations)} security group violations")
            return violations
            
        except Exception as e:
            print(f"❌ Error scanning security groups: {str(e)}")
            return []
    
    def _check_security_group(self, sg):
        """Check a single security group for compliance"""
        violations = []
        sg_id = sg['GroupId']
        sg_name = sg['GroupName']
        
        # Check ingress rules
        for rule in sg.get('IpPermissions', []):
            # Check for 0.0.0.0/0 (open to internet)
            for ip_range in rule.get('IpRanges', []):
                if ip_range.get('CidrIp') == '0.0.0.0/0':
                    from_port = rule.get('FromPort', 0)
                    to_port = rule.get('ToPort', 65535)
                    
                    # Check if it's a sensitive port
                    sensitive_ports = self.rules.get('sensitive_ports', [])
                    
                    for port in sensitive_ports:
                        if from_port <= port <= to_port:
                            violations.append({
                                'resource_type': 'SecurityGroup',
                                'resource_id': sg_id,
                                'resource_name': sg_name,
                                'violation': 'sensitive_port_open',
                                'severity': 'critical',
                                'description': f'Security group "{sg_name}" ({sg_id}) allows internet access on port {port}',
                                'remediation': f'Restrict access on port {port} to specific IP ranges'
                            })
                            break  # Don't report multiple times for same SG
        
        return violations
