"""
Main entry point for Right-Sizing Recommendation Engine
"""

import argparse
import yaml
import sys
from analyzers import EC2Analyzer, RDSAnalyzer
from recommenders import EC2Recommender, ReservedInstanceRecommender
from cost_optimizer import CostOptimizer
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


def analyze_resources(config, resource_types=None):
    """Analyze resource utilization across regions"""
    regions = config['aws']['regions']
    
    all_ec2_analysis = []
    all_rds_analysis = []
    
    print("\n🚀 Starting Right-Sizing Analysis...")
    print(f"📍 Analyzing regions: {', '.join(regions)}")
    print(f"📅 Lookback period: {config['analysis']['lookback_days']} days\n")
    
    for region in regions:
        print(f"\n{'='*100}")
        print(f"Region: {region}")
        print(f"{'='*100}\n")
        
        # Analyze EC2
        if resource_types is None or 'ec2' in resource_types:
            try:
                ec2_analyzer = EC2Analyzer(region, config)
                ec2_results = ec2_analyzer.analyze_all_instances()
                all_ec2_analysis.extend(ec2_results)
            except Exception as e:
                print(f"❌ Error analyzing EC2 in {region}: {str(e)}\n")
        
        # Analyze RDS
        if resource_types is None or 'rds' in resource_types:
            try:
                rds_analyzer = RDSAnalyzer(region, config)
                rds_results = rds_analyzer.analyze_all_instances()
                all_rds_analysis.extend(rds_results)
            except Exception as e:
                print(f"❌ Error analyzing RDS in {region}: {str(e)}\n")
    
    return all_ec2_analysis, all_rds_analysis


def generate_recommendations(config, ec2_analysis, rds_analysis):
    """Generate optimization recommendations"""
    
    # EC2 Right-Sizing Recommendations
    ec2_recommender = EC2Recommender(config)
    ec2_recommendations = ec2_recommender.generate_recommendations(ec2_analysis)
    
    # Reserved Instance Recommendations
    ri_recommender = ReservedInstanceRecommender(config)
    ri_recommendations = ri_recommender.generate_recommendations(ec2_analysis)
    
    return ec2_recommendations, ri_recommendations


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Right-Sizing Recommendation Engine - Optimize AWS costs through intelligent resource analysis'
    )
    
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--resources',
        help='Comma-separated list of resource types to analyze (ec2,rds). Default: all'
    )
    
    parser.add_argument(
        '--format',
        choices=['console', 'json', 'csv', 'html'],
        help='Output format (overrides config.yaml)'
    )
    
    parser.add_argument(
        '--lookback-days',
        type=int,
        help='Number of days to analyze (overrides config.yaml)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with CLI arguments
    if args.format:
        config['reporting']['format'] = args.format
    
    if args.lookback_days:
        config['analysis']['lookback_days'] = args.lookback_days
    
    # Parse resource types
    resource_types = None
    if args.resources:
        resource_types = [r.strip().lower() for r in args.resources.split(',')]
        print(f"🎯 Analyzing only: {', '.join(resource_types)}")
    
    # Step 1: Analyze resources
    ec2_analysis, rds_analysis = analyze_resources(config, resource_types)
    
    if not ec2_analysis and not rds_analysis:
        print("\n⚠️  No resources found to analyze.")
        print("Either no resources exist, or insufficient CloudWatch data is available.")
        return 0
    
    # Step 2: Generate recommendations
    print("\n" + "="*100)
    print("GENERATING RECOMMENDATIONS")
    print("="*100 + "\n")
    
    ec2_recommendations, ri_recommendations = generate_recommendations(
        config, ec2_analysis, rds_analysis
    )
    
    # Step 3: Calculate savings
    optimizer = CostOptimizer(config)
    savings_summary = optimizer.calculate_total_savings(
        ec2_recommendations, ri_recommendations
    )
    stats = optimizer.get_summary_stats(ec2_recommendations, ri_recommendations)
    
    # Step 4: Generate report
    reporter = Reporter(config)
    reporter.generate_report(
        ec2_recommendations, ri_recommendations, savings_summary, stats
    )
    
    # Summary
    total_savings = savings_summary['total']['annual_savings']
    
    if total_savings > 0:
        print(f"\n✨ Analysis complete!")
        print(f"💰 Total potential annual savings: ${total_savings:.2f}")
        print(f"📊 Total recommendations: {stats['total_recommendations']}")
    else:
        print("\n✨ Analysis complete!")
        print("🎉 Your resources are already well-optimized!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())