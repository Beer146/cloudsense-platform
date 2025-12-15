"""
Main entry point for Zombie Resource Hunter
"""

import argparse
import yaml
import sys
from scanners import EC2Scanner, EBSScanner, RDSScanner, ELBScanner
from cost_calculator import CostCalculator
from reporter import Reporter


def load_config(config_file='config.yaml'):
    """Load configuration from YAML file"""
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"❌ Error: Configuration file '{config_file}' not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error: Invalid YAML in configuration file: {e}")
        sys.exit(1)


def scan_resources(config, resource_types=None):
    """Scan for zombie resources across all regions"""
    regions = config['aws']['regions']
    all_zombies = []
    
    print("\n🚀 Starting Zombie Resource Hunter...")
    print(f"📍 Scanning regions: {', '.join(regions)}\n")
    
    for region in regions:
        print(f"\n{'='*80}")
        print(f"Region: {region}")
        print(f"{'='*80}")
        
        # Determine which scanners to run
        scanners_to_run = []
        
        if resource_types is None or 'ec2' in resource_types:
            scanners_to_run.append(('EC2', EC2Scanner(region, config)))
        
        if resource_types is None or 'ebs' in resource_types:
            scanners_to_run.append(('EBS', EBSScanner(region, config)))
        
        if resource_types is None or 'rds' in resource_types:
            scanners_to_run.append(('RDS', RDSScanner(region, config)))
        
        if resource_types is None or 'elb' in resource_types:
            scanners_to_run.append(('ELB', ELBScanner(region, config)))
        
        # Run scanners
        for scanner_name, scanner in scanners_to_run:
            try:
                zombies = scanner.scan()
                all_zombies.extend(zombies)
            except Exception as e:
                print(f"❌ Error scanning {scanner_name} in {region}: {str(e)}")
    
    return all_zombies


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Zombie Resource Hunter - Find and eliminate unused AWS resources'
    )
    
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--resources',
        help='Comma-separated list of resource types to scan (ec2,ebs,rds,elb). Default: all'
    )
    
    parser.add_argument(
        '--format',
        choices=['console', 'json', 'csv', 'html'],
        help='Output format (overrides config.yaml)'
    )
    
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Enable cleanup mode (DANGEROUS - will delete resources if configured)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Dry run mode - only report, do not delete (default: true)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override format if specified
    if args.format:
        config['reporting']['format'] = args.format
    
    # Parse resource types
    resource_types = None
    if args.resources:
        resource_types = [r.strip().lower() for r in args.resources.split(',')]
        print(f"🎯 Scanning only: {', '.join(resource_types)}")
    
    # Scan for zombies
    zombies = scan_resources(config, resource_types)
    
    # Calculate costs
    calculator = CostCalculator()
    cost_summary = calculator.calculate_total_savings(zombies)
    stats = calculator.get_summary_stats(zombies)
    
    # Generate report
    reporter = Reporter(config)
    reporter.generate_report(zombies, cost_summary, stats)
    
    # Cleanup warning
    if args.cleanup and not args.dry_run:
        if config['cleanup']['enabled']:
            print("\n⚠️  WARNING: Cleanup mode is ENABLED but not implemented yet!")
            print("⚠️  This feature will be added in a future version.")
            print("⚠️  For now, please manually delete resources based on the report.")
        else:
            print("\n⚠️  Cleanup is disabled in config.yaml")
            print("⚠️  Set cleanup.enabled = true to enable (use with caution!)")
    
    print(f"\n✨ Scan complete! Found {len(zombies)} zombie resources.")
    
    if len(zombies) > 0:
        print(f"💰 Potential monthly savings: ${cost_summary['total_monthly_savings']:.2f}")
        print(f"💰 Potential annual savings: ${cost_summary['total_annual_savings']:.2f}")
    else:
        print("🎉 No zombie resources found - your AWS account is clean!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())