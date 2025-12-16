"""
Post-Mortem Generator Service
Wrapper for the post-mortem analyzer
"""
import sys
from pathlib import Path
from datetime import datetime
import yaml
import time

# Add scripts to Python path
scripts_path = Path(__file__).parent.parent.parent / "scripts" / "post-mortem"
sys.path.insert(0, str(scripts_path))

# Import from post-mortem
from main import PostMortemGenerator

# Import database models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Scan


class PostMortemService:
    def __init__(self):
        # Pass the full path to the config file
        config_path = Path(__file__).parent.parent.parent / "scripts" / "post-mortem" / "config.yaml"
        self.generator = PostMortemGenerator(config_path=str(config_path))
    
    def _save_to_database(self, regions, report_data, duration):
        """Save post-mortem analysis to database"""
        from models.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Calculate total events
            total_events = 0
            if report_data.get('status') == 'success':
                summary = report_data.get('summary', {})
                total_events = summary.get('total_errors', 0) + summary.get('total_warnings', 0)
            
            scan = Scan(
                scan_type='postmortem',
                status='success',
                regions=regions,
                total_resources=total_events,
                total_cost=0,  # Not applicable
                total_savings=0,  # Not applicable
                duration_seconds=duration
            )
            db.add(scan)
            db.commit()
            db.refresh(scan)
            
            print(f"✅ Saved post-mortem analysis to database (Scan ID: {scan.id})")
            return scan.id
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error saving to database: {e}")
            return None
        finally:
            db.close()
    
    async def analyze(self, regions: list = None, lookback_hours: int = 24):
        """Run post-mortem analysis"""
        start_time = time.time()
        
        try:
            # Update lookback hours if specified
            if lookback_hours:
                self.generator.lookback_hours = lookback_hours
            
            analyze_regions = regions or self.generator.config['aws']['regions']
            
            # Run analysis
            print(f"\n🔍 Running post-mortem analysis for {lookback_hours} hours...")
            report = self.generator.analyze(regions=analyze_regions)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Save to database
            scan_id = self._save_to_database(analyze_regions, report, duration)
            
            # Format response
            if report['status'] == 'no_incidents':
                results = {
                    "status": "success",
                    "scan_id": scan_id,
                    "message": report['message'],
                    "regions_analyzed": analyze_regions,
                    "lookback_hours": lookback_hours,
                    "summary": {
                        "total_errors": 0,
                        "total_warnings": 0,
                        "unique_patterns": 0
                    },
                    "timeline": [],
                    "recommendations": [],
                    "duration_seconds": duration
                }
            else:
                results = {
                    "status": "success",
                    "scan_id": scan_id,
                    "regions_analyzed": analyze_regions,
                    "lookback_hours": lookback_hours,
                    "summary": report['summary'],
                    "timeline": report['timeline'][:20],  # Top 20 events
                    "error_patterns": report['error_patterns'][:10],  # Top 10 patterns
                    "recommendations": report['recommendations'],
                    "duration_seconds": duration
                }
            
            return results
            
        except Exception as e:
            print(f"Post-mortem analysis error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e)
            }
