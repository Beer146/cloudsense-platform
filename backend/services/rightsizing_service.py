"""
Right-Sizing Recommendation Service
Wrapper for the rightsizing engine
"""
import sys
from pathlib import Path
from datetime import datetime
import yaml
import time

# Add scripts to Python path
scripts_path = Path(__file__).parent.parent.parent / "scripts" / "rightsizing"
sys.path.insert(0, str(scripts_path))

# Import from rightsizing
from analyzers import EC2Analyzer, RDSAnalyzer
from recommenders import EC2Recommender, ReservedInstanceRecommender
from cost_optimizer import CostOptimizer

# Import database models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Scan, RightSizingRecommendation


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
        
        original_days = self.config['analysis']['lookback_days']
        self.config['analysis']['lookback_days'] = days
        
        for region in regions:
            print(f"Analyzing {region}...")
            
            try:
                ec2_analyzer = EC2Analyzer(region, self.config)
                ec2_results = ec2_analyzer.analyze_all_instances()
                all_ec2_analysis.extend(ec2_results)
                print(f"  Found {len(ec2_results)} EC2 instances to analyze")
            except Exception as e:
                print(f"EC2 analysis error in {region}: {e}")
            
            try:
                rds_analyzer = RDSAnalyzer(region, self.config)
                rds_results = rds_analyzer.analyze_all_instances()
                all_rds_analysis.extend(rds_results)
                print(f"  Found {len(rds_results)} RDS instances to analyze")
            except Exception as e:
                print(f"RDS analysis error in {region}: {e}")
        
        self.config['analysis']['lookback_days'] = original_days
        
        return all_ec2_analysis, all_rds_analysis
    
    def _save_to_database(self, analyze_regions, ec2_recommendations, savings_summary, duration, days):
        """Save analysis results to database"""
        from models.database import SessionLocal
        db = SessionLocal()
        
        try:
            scan = Scan(
                scan_type='rightsizing',
                status='success',
                regions=analyze_regions,
                total_resources=len(ec2_recommendations),
                total_cost=0,  # Not applicable for rightsizing
                total_savings=savings_summary.get('total', {}).get('annual_savings', 0),
                duration_seconds=duration
            )
            db.add(scan)
            db.flush()
            
            for rec in ec2_recommendations:
                rec_record = RightSizingRecommendation(
                    scan_id=scan.id,
                    instance_id=rec.get('instance_id', 'unknown'),
                    name=rec.get('name', 'N/A'),
                    region=rec.get('region', 'unknown'),
                    current_type=rec.get('current_type', 'unknown'),
                    recommended_type=rec.get('recommended_type', 'unknown'),
                    strategy=rec.get('strategy', 'unknown'),
                    reason=rec.get('reason', ''),
                    current_monthly_cost=rec.get('current_monthly_cost', 0),
                    recommended_monthly_cost=rec.get('recommended_monthly_cost', 0),
                    monthly_savings=rec.get('monthly_savings', 0),
                    annual_savings=rec.get('annual_savings', 0),
                    cpu_metrics=rec.get('cpu_utilization', {})
                )
                db.add(rec_record)
            
            db.commit()
            print(f"✅ Saved analysis results to database (Scan ID: {scan.id})")
            return scan.id
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error saving to database: {e}")
            return None
        finally:
            db.close()
    
    async def analyze_resources(self, regions: list = None, days: int = 30):
        """Analyze resources and generate right-sizing recommendations"""
        start_time = time.time()
        
        try:
            analyze_regions = regions or self.config['aws']['regions']
            
            ec2_analysis, rds_analysis = self._analyze_resources(analyze_regions, days)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # ALWAYS generate recommendations (even if empty)
            ec2_recommender = EC2Recommender(self.config)
            ec2_recommendations = ec2_recommender.generate_recommendations(ec2_analysis)
            
            try:
                ri_recommender = ReservedInstanceRecommender(self.config)
                ri_recommendations = ri_recommender.generate_recommendations(ec2_analysis)
            except:
                ri_recommendations = []
            
            optimizer = CostOptimizer(self.config)
            savings_summary = optimizer.calculate_total_savings(ec2_recommendations, ri_recommendations)
            
            # ALWAYS save to database (even if no resources/recommendations)
            scan_id = self._save_to_database(analyze_regions, ec2_recommendations, savings_summary, duration, days)
            
            # Determine message
            message = None
            if not ec2_analysis and not rds_analysis:
                message = "No resources found or insufficient data"
            elif len(ec2_recommendations) == 0 and len(ec2_analysis) > 0:
                message = "All resources are already well-optimized!"
            
            results = {
                "status": "success",
                "scan_id": scan_id,
                "message": message,
                "regions_analyzed": analyze_regions,
                "recommendations": {
                    "ec2": {
                        "total_analyzed": len(ec2_analysis),
                        "total_recommendations": len(ec2_recommendations),
                        "downsize_opportunities": len([r for r in ec2_recommendations if r.get('strategy') == 'downsize']),
                        "family_switches": len([r for r in ec2_recommendations if r.get('strategy') == 'family_switch']),
                        "monthly_savings": savings_summary.get('ec2', {}).get('monthly_savings', 0),
                        "annual_savings": savings_summary.get('ec2', {}).get('annual_savings', 0),
                        "examples": ec2_recommendations[:5]
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
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "duration_seconds": duration
            }
            
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
