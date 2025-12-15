"""
Right-Sizing Recommendation Service
Wrapper for the rightsizing engine
"""
import sys
from pathlib import Path
from datetime import datetime
import yaml

# Add scripts to Python path
scripts_path = Path(__file__).parent.parent.parent / "scripts" / "rightsizing"
sys.path.insert(0, str(scripts_path))

# Import from rightsizing
from analyzers import EC2Analyzer, RDSAnalyzer
from recommenders import EC2Recommender, ReservedInstanceRecommender
from cost_optimizer import CostOptimizer


class RightSizingService:
    def __init__(self):
        self.config_path = scripts_path / "config.yaml"
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return {
                'aws': {'regions': ['us-east-1', 'us-west-2']},
                'analysis': {'lookback_days': 30, 'min_datapoints': 20, 'cpu_percentile': 95},
                'ec2': {
                    'cpu_underutilized_threshold': 20,
                    'min_savings_threshold': 10,
                    'allowed_families': ['t3', 't3a', 'm5', 'm5a', 'c5', 'c5a', 'r5', 'r5a']
                }
            }
    
    def _analyze_resources(self, regions, days):
        """Analyze resource utilization"""
        all_ec2_analysis = []
        all_rds_analysis = []
        
        # Temporarily override lookback days
        original_days = self.config['analysis']['lookback_days']
        self.config['analysis']['lookback_days'] = days
        
        for region in regions:
            print(f"Analyzing {region}...")
            
            # Analyze EC2
            try:
                ec2_analyzer = EC2Analyzer(region, self.config)
                ec2_results = ec2_analyzer.analyze_all_instances()
                all_ec2_analysis.extend(ec2_results)
                print(f"  Found {len(ec2_results)} EC2 instances to analyze")
            except Exception as e:
                print(f"EC2 analysis error in {region}: {e}")
            
            # Analyze RDS
            try:
                rds_analyzer = RDSAnalyzer(region, self.config)
                rds_results = rds_analyzer.analyze_all_instances()
                all_rds_analysis.extend(rds_results)
                print(f"  Found {len(rds_results)} RDS instances to analyze")
            except Exception as e:
                print(f"RDS analysis error in {region}: {e}")
        
        # Restore original config
        self.config['analysis']['lookback_days'] = original_days
        
        return all_ec2_analysis, all_rds_analysis
    
    async def analyze_resources(self, regions: list = None, days: int = 30):
        """
        Analyze resources and generate right-sizing recommendations
        
        Args:
            regions: List of AWS regions to analyze
            days: Number of days of metrics to analyze
            
        Returns:
            dict: Analysis results with recommendations
        """
        try:
            # Use regions from config if not provided
            analyze_regions = regions or self.config['aws']['regions']
            
            # Step 1: Analyze resources
            ec2_analysis, rds_analysis = self._analyze_resources(analyze_regions, days)
            
            if not ec2_analysis and not rds_analysis:
                return {
                    "status": "success",
                    "message": "No resources found or insufficient data",
                    "regions_analyzed": analyze_regions,
                    "recommendations": {
                        "ec2": {"total_analyzed": 0, "downsize_opportunities": 0, "monthly_savings": 0, "examples": []},
                        "rds": {"total_analyzed": 0, "downsize_opportunities": 0, "monthly_savings": 0}
                    },
                    "total_monthly_savings": 0,
                    "analysis_period_days": days,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            
            # Step 2: Generate recommendations
            ec2_recommender = EC2Recommender(self.config)
            ec2_recommendations = ec2_recommender.generate_recommendations(ec2_analysis)
            
            # Try RI recommendations
            try:
                ri_recommender = ReservedInstanceRecommender(self.config)
                ri_recommendations = ri_recommender.generate_recommendations(ec2_analysis)
            except Exception as e:
                print(f"RI recommendation error: {e}")
                ri_recommendations = []
            
            # Step 3: Calculate savings
            optimizer = CostOptimizer(self.config)
            savings_summary = optimizer.calculate_total_savings(ec2_recommendations, ri_recommendations)
            
            # Format response
            results = {
                "status": "success",
                "regions_analyzed": analyze_regions,
                "recommendations": {
                    "ec2": {
                        "total_analyzed": len(ec2_analysis),
                        "total_recommendations": len(ec2_recommendations),
                        "downsize_opportunities": len([r for r in ec2_recommendations if r.get('strategy') == 'downsize']),
                        "family_switches": len([r for r in ec2_recommendations if r.get('strategy') == 'family_switch']),
                        "monthly_savings": savings_summary.get('ec2', {}).get('monthly_savings', 0),
                        "annual_savings": savings_summary.get('ec2', {}).get('annual_savings', 0),
                        "examples": ec2_recommendations[:5]  # Top 5 recommendations
                    },
                    "rds": {
                        "total_analyzed": len(rds_analysis),
                        "downsize_opportunities": 0,
                        "monthly_savings": 0
                    },
                    "reserved_instances": {
                        "recommendations": len(ri_recommendations),
                        "annual_savings": savings_summary.get('ri', {}).get('annual_savings', 0)
                    }
                },
                "total_monthly_savings": savings_summary.get('total', {}).get('monthly_savings', 0),
                "total_annual_savings": savings_summary.get('total', {}).get('annual_savings', 0),
                "analysis_period_days": days,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            # Print summary
            print(f"\nAnalysis complete:")
            print(f"  EC2 instances analyzed: {len(ec2_analysis)}")
            print(f"  Recommendations: {len(ec2_recommendations)}")
            print(f"  Potential monthly savings: ${results['total_monthly_savings']:.2f}")
            
            return results
            
        except Exception as e:
            print(f"Analysis error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e)
            }
