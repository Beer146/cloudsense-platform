"""
Main entry point for Compliance-as-Code Validator
"""
import yaml
import sys
from scanners import S3ComplianceScanner, RDSComplianceScanner, SecurityGroupScanner, EC2ComplianceScanner


def load_config(config_file='config.yaml'):
    """Load configuration from YAML file"""
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"❌ Error: Configuration file '{config_file}' not found")
        sys.exit(1)


def scan_compliance(config):
    """Run compliance scans across all regions"""
    regions = config['aws']['regions']
    all_violations = []
    
    print("\n🚀 Starting Compliance Scan...")
    print(f"📍 Scanning regions: {', '.join(regions)}\n")
    
    for region in regions:
        print(f"\n{'='*100}")
        print(f"Region: {region}")
        print(f"{'='*100}\n")
        
        # S3 Scanner (only from us-east-1)
        if region == 'us-east-1':
            try:
                s3_scanner = S3ComplianceScanner(region, config)
                s3_violations = s3_scanner.scan()
                all_violations.extend(s3_violations)
            except Exception as e:
                print(f"❌ Error scanning S3: {str(e)}\n")
        
        # RDS Scanner
        try:
            rds_scanner = RDSComplianceScanner(region, config)
            rds_violations = rds_scanner.scan()
            all_violations.extend(rds_violations)
        except Exception as e:
            print(f"❌ Error scanning RDS: {str(e)}\n")
        
        # Security Group Scanner
        try:
            sg_scanner = SecurityGroupScanner(region, config)
            sg_violations = sg_scanner.scan()
            all_violations.extend(sg_violations)
        except Exception as e:
            print(f"❌ Error scanning security groups: {str(e)}\n")
        
        # EC2 Scanner
        try:
            ec2_scanner = EC2ComplianceScanner(region, config)
            ec2_violations = ec2_scanner.scan()
            all_violations.extend(ec2_violations)
        except Exception as e:
            print(f"❌ Error scanning EC2: {str(e)}\n")
    
    return all_violations


def main():
    config = load_config()
    violations = scan_compliance(config)
    
    # Summary
    print(f"\n{'='*100}")
    print("COMPLIANCE SCAN SUMMARY")
    print(f"{'='*100}\n")
    
    if len(violations) == 0:
        print("✅ No compliance violations found - all resources are compliant!")
        return 0
    
    # Group by severity
    critical = [v for v in violations if v.get('severity') == 'critical']
    high = [v for v in violations if v.get('severity') == 'high']
    medium = [v for v in violations if v.get('severity') == 'medium']
    low = [v for v in violations if v.get('severity') == 'low']
    
    print(f"🚨 Critical: {len(critical)}")
    print(f"⚠️  High: {len(high)}")
    print(f"⚡ Medium: {len(medium)}")
    print(f"ℹ️  Low: {len(low)}")
    print(f"\n📊 Total Violations: {len(violations)}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
