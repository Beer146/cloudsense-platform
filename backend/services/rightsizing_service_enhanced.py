"""
Enhanced Right-Sizing Service with LSTM Workload Forecasting
Combines historical analysis with ML-powered future predictions
"""
import boto3
from datetime import datetime, timedelta
import time
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Import LSTM forecaster
from services.lstm_workload_forecaster import LSTMWorkloadForecaster

# Import database models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Scan
from models.database import SessionLocal


class EnhancedRightSizingService:
    def __init__(self):
        self.regions = ['us-east-1', 'us-west-2']
        try:
            self.lstm_forecaster = LSTMWorkloadForecaster()
            self.lstm_enabled = True
            print("✅ LSTM Workload Forecaster enabled")
        except Exception as e:
            print(f"⚠️ LSTM forecaster disabled: {e}")
            self.lstm_enabled = False
    
    def _get_cloudwatch_metrics(self, instance_id: str, region: str, metric_name: str, days: int = 30) -> pd.DataFrame:
        """Fetch CloudWatch metrics for an instance"""
        try:
            cloudwatch = boto3.client('cloudwatch', region_name=region)
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName=metric_name,
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Average']
            )
            
            if not response['Datapoints']:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(response['Datapoints'])
            df = df.sort_values('Timestamp')
            df = df.rename(columns={'Average': metric_name.lower(), 'Timestamp': 'timestamp'})
            
            return df[['timestamp', metric_name.lower()]]
            
        except Exception as e:
            print(f"Error fetching metrics for {instance_id}: {e}")
            return pd.DataFrame()
    
    def _analyze_instance_with_lstm(self, instance_id: str, region: str) -> dict:
        """Analyze instance with LSTM forecasting"""
        print(f"\n🔍 Analyzing {instance_id} with LSTM forecasting...")
        
        # Fetch 30 days of CPU metrics
        cpu_df = self._get_cloudwatch_metrics(instance_id, region, 'CPUUtilization', days=30)
        
        if cpu_df.empty or len(cpu_df) < 168:  # Need at least 7 days
            return {
                'has_forecast': False,
                'reason': 'Insufficient historical data (need 7+ days)',
                'traditional_avg': None
            }
        
        # Traditional analysis (14-day average)
        recent_14d = cpu_df.tail(14 * 24)
        traditional_avg = recent_14d['cpuutilization'].mean()
        
        # LSTM forecast
        if self.lstm_enabled and len(cpu_df) >= 168:
            try:
                # Train/use LSTM
                cpu_values = cpu_df['cpuutilization'].values
                
                # Train if model doesn't exist
                if self.lstm_forecaster.model is None:
                    self.lstm_forecaster.train(cpu_df, 'cpuutilization')
                
                # Forecast next 7 days
                recent_data = cpu_values[-168:]  # Last 7 days
                forecast = self.lstm_forecaster.forecast(recent_data, hours_ahead=168)
                
                # Analyze workload pattern
                pattern = self.lstm_forecaster.analyze_workload_pattern(recent_data)
                
                return {
                    'has_forecast': True,
                    'traditional_avg': float(traditional_avg),
                    'forecast_avg': forecast.get('avg_predicted', traditional_avg),
                    'forecast_max': forecast.get('max_predicted', traditional_avg),
                    'forecast_min': forecast.get('min_predicted', traditional_avg),
                    'trend': forecast.get('trend', 'UNKNOWN'),
                    'seasonality': forecast.get('seasonality_detected', False),
                    'workload_pattern': pattern.get('pattern', 'UNKNOWN'),
                    'pattern_recommendation': pattern.get('recommendation', ''),
                    'coefficient_of_variation': pattern.get('coefficient_of_variation', 0)
                }
            except Exception as e:
                print(f"⚠️ LSTM forecast failed: {e}")
                return {
                    'has_forecast': False,
                    'reason': f'LSTM error: {str(e)}',
                    'traditional_avg': float(traditional_avg)
                }
        else:
            return {
                'has_forecast': False,
                'reason': 'LSTM disabled or insufficient data',
                'traditional_avg': float(traditional_avg)
            }
    
    def _generate_lstm_recommendation(self, instance, analysis: dict) -> dict:
        """Generate enhanced recommendation using LSTM insights"""
        instance_type = instance.get('InstanceType', 'unknown')
        
        if not analysis.get('has_forecast'):
            # Fallback to traditional
            avg_cpu = analysis.get('traditional_avg', 0)
            if avg_cpu < 20:
                return {
                    'action': 'DOWNSIZE',
                    'reason': f'Average CPU {avg_cpu:.1f}% (traditional analysis)',
                    'confidence': 'MEDIUM'
                }
            return {
                'action': 'KEEP',
                'reason': f'Average CPU {avg_cpu:.1f}% (traditional analysis)',
                'confidence': 'MEDIUM'
            }
        
        # LSTM-enhanced recommendation
        forecast_avg = analysis['forecast_avg']
        forecast_max = analysis['forecast_max']
        trend = analysis['trend']
        pattern = analysis['workload_pattern']
        
        # Decision logic
        if trend == 'GROWING' and forecast_max > 80:
            return {
                'action': 'UPSIZE',
                'reason': f'Workload growing, forecast shows {forecast_max:.1f}% peak usage',
                'confidence': 'HIGH',
                'ml_enhanced': True,
                'details': f'Trend: {trend}, Pattern: {pattern}'
            }
        elif trend == 'SHRINKING' and forecast_avg < 20:
            return {
                'action': 'DOWNSIZE',
                'reason': f'Workload shrinking, forecast shows {forecast_avg:.1f}% average usage',
                'confidence': 'HIGH',
                'ml_enhanced': True,
                'details': f'Trend: {trend}, Pattern: {pattern}'
            }
        elif pattern == 'BURSTY':
            return {
                'action': 'CONSIDER_AUTOSCALING',
                'reason': f'Bursty workload detected (CV: {analysis["coefficient_of_variation"]:.2f})',
                'confidence': 'HIGH',
                'ml_enhanced': True,
                'details': analysis['pattern_recommendation']
            }
        elif forecast_avg < 20:
            return {
                'action': 'DOWNSIZE',
                'reason': f'Forecast shows {forecast_avg:.1f}% average usage, trend: {trend}',
                'confidence': 'HIGH',
                'ml_enhanced': True,
                'details': f'Pattern: {pattern}'
            }
        else:
            return {
                'action': 'KEEP',
                'reason': f'Forecast shows {forecast_avg:.1f}% average usage, {pattern} pattern',
                'confidence': 'HIGH',
                'ml_enhanced': True,
                'details': f'Trend: {trend}, Seasonality: {analysis["seasonality"]}'
            }
    
    def _save_to_database(self, regions: list, results: dict, duration: float) -> int:
        """Save analysis to database"""
        db = SessionLocal()
        try:
            scan = Scan(
                scan_type='rightsizing',
                status='success',
                regions=regions,
                total_resources=results.get('total_analyzed', 0),
                total_cost=0,
                total_savings=results.get('total_monthly_savings', 0),
                duration_seconds=duration
            )
            db.add(scan)
            db.commit()
            db.refresh(scan)
            
            print(f"✅ Saved right-sizing analysis to database (Scan ID: {scan.id})")
            return scan.id
        except Exception as e:
            db.rollback()
            print(f"❌ Error saving to database: {e}")
            return None
        finally:
            db.close()
    
    async def analyze(self, regions: list = None, use_lstm: bool = True):
        """
        Analyze EC2 instances with optional LSTM forecasting
        
        Args:
            regions: AWS regions to analyze
            use_lstm: Whether to use LSTM for predictions
        """
        start_time = time.time()
        
        scan_regions = regions or self.regions
        
        print(f"\n📏 Starting Enhanced Right-Sizing Analysis...")
        print(f"   LSTM Forecasting: {'Enabled' if (use_lstm and self.lstm_enabled) else 'Disabled'}")
        print(f"   Regions: {', '.join(scan_regions)}")
        
        all_instances = []
        lstm_analyses = []
        
        # Scan instances
        for region in scan_regions:
            print(f"\n📍 Scanning {region}...")
            try:
                ec2 = boto3.client('ec2', region_name=region)
                response = ec2.describe_instances(
                    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
                )
                
                for reservation in response['Reservations']:
                    for instance in reservation['Instances']:
                        all_instances.append({
                            'instance': instance,
                            'region': region
                        })
            except Exception as e:
                print(f"Error scanning {region}: {e}")
        
        duration = time.time() - start_time
        
        # ALWAYS save to database, even with no instances
        results = {
            'total_analyzed': len(all_instances),
            'lstm_enhanced_count': 0,
            'total_monthly_savings': 0
        }
        scan_id = self._save_to_database(scan_regions, results, duration)
        
        if not all_instances:
            print("ℹ️ No running instances found")
            
            return {
                'status': 'success',
                'scan_id': scan_id,  # FIXED: Now includes scan_id
                'message': 'No running instances to analyze',
                'total_analyzed': 0,
                'lstm_enhanced_count': 0,
                'recommendations': [],
                'total_monthly_savings': 0,
                'regions_analyzed': scan_regions,
                'duration_seconds': duration
            }
        
        print(f"\n🔍 Found {len(all_instances)} running instances")
        
        # Analyze each instance
        recommendations = []
        for item in all_instances[:5]:  # Limit to 5 for demo
            instance = item['instance']
            region = item['region']
            instance_id = instance['InstanceId']
            
            if use_lstm and self.lstm_enabled:
                analysis = self._analyze_instance_with_lstm(instance_id, region)
                recommendation = self._generate_lstm_recommendation(instance, analysis)
                
                if analysis.get('has_forecast'):
                    lstm_analyses.append(analysis)
                    recommendation['lstm_analysis'] = analysis
            else:
                # Traditional analysis only
                recommendation = {
                    'action': 'ANALYZE_MANUALLY',
                    'reason': 'LSTM disabled',
                    'confidence': 'LOW'
                }
            
            recommendations.append({
                'instance_id': instance_id,
                'instance_type': instance.get('InstanceType'),
                'region': region,
                'recommendation': recommendation
            })
        
        duration = time.time() - start_time
        
        # Update results and save again
        results = {
            'total_analyzed': len(all_instances),
            'lstm_enhanced_count': len(lstm_analyses),
            'total_monthly_savings': 0
        }
        scan_id = self._save_to_database(scan_regions, results, duration)
        
        print(f"\n✅ Right-Sizing Analysis Complete!")
        print(f"   Instances analyzed: {len(all_instances)}")
        print(f"   LSTM-enhanced: {len(lstm_analyses)}")
        
        return {
            'status': 'success',
            'scan_id': scan_id,
            'total_analyzed': len(all_instances),
            'lstm_enhanced_count': len(lstm_analyses),
            'recommendations': recommendations,
            'total_monthly_savings': 0,
            'regions_analyzed': scan_regions,
            'duration_seconds': duration
        }


# Maintain backward compatibility
RightSizingService = EnhancedRightSizingService
