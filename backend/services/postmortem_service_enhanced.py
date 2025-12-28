"""
Enhanced Post-Mortem Service with LLM-Powered Analysis
Combines traditional log analysis with Claude API for intelligent insights
"""
import boto3
from datetime import datetime, timedelta
import re
import sys
from pathlib import Path
from typing import List, Dict, Any

# Import LLM analyzer
from services.llm_postmortem_analyzer import LLMPostMortemAnalyzer

# Import database models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Scan
from models.database import SessionLocal


class EnhancedPostMortemService:
    def __init__(self):
        self.regions = ['us-east-1', 'us-west-2']
        try:
            self.llm_analyzer = LLMPostMortemAnalyzer()
            self.llm_enabled = True
            print("✅ LLM Post-Mortem Analyzer enabled")
        except Exception as e:
            print(f"⚠️ LLM analyzer disabled: {e}")
            self.llm_enabled = False
    
    def _get_log_groups(self, region: str) -> List[str]:
        """Get CloudWatch log groups"""
        try:
            logs = boto3.client('logs', region_name=region)
            response = logs.describe_log_groups(limit=10)
            return [lg['logGroupName'] for lg in response.get('logGroups', [])]
        except Exception as e:
            print(f"Error getting log groups in {region}: {e}")
            return []
    
    def _search_logs(self, log_group: str, region: str, lookback_hours: int = 24) -> List[Dict]:
        """Search CloudWatch Logs for errors and warnings"""
        try:
            logs = boto3.client('logs', region_name=region)
            
            start_time = int((datetime.now() - timedelta(hours=lookback_hours)).timestamp() * 1000)
            end_time = int(datetime.now().timestamp() * 1000)
            
            # Search for ERROR and WARN patterns
            query = """
            fields @timestamp, @message
            | filter @message like /ERROR|CRITICAL|FATAL|Exception|exception/
            | sort @timestamp desc
            | limit 100
            """
            
            query_id = logs.start_query(
                logGroupName=log_group,
                startTime=start_time,
                endTime=end_time,
                queryString=query
            )
            
            # Wait for query to complete
            import time
            for _ in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                result = logs.get_query_results(queryId=query_id['queryId'])
                
                if result['status'] == 'Complete':
                    return self._parse_log_results(result.get('results', []))
                elif result['status'] == 'Failed':
                    print(f"Query failed for {log_group}")
                    return []
            
            return []
            
        except Exception as e:
            print(f"Error searching logs in {log_group}: {e}")
            return []
    
    def _parse_log_results(self, results: List) -> List[Dict]:
        """Parse CloudWatch Insights query results"""
        logs = []
        for result in results:
            log_entry = {}
            for field in result:
                log_entry[field['field']] = field['value']
            logs.append(log_entry)
        return logs
    
    def _group_errors(self, logs: List[Dict]) -> List[Dict]:
        """Group similar error messages"""
        error_patterns = {}
        
        for log in logs:
            message = log.get('@message', '')
            
            # Extract error pattern (remove timestamps, IDs, etc.)
            pattern = self._extract_pattern(message)
            
            if pattern not in error_patterns:
                error_patterns[pattern] = {
                    'pattern': pattern,
                    'count': 0,
                    'example': message,
                    'first_seen': log.get('@timestamp'),
                    'last_seen': log.get('@timestamp')
                }
            
            error_patterns[pattern]['count'] += 1
            error_patterns[pattern]['last_seen'] = log.get('@timestamp')
        
        # Sort by count
        return sorted(error_patterns.values(), key=lambda x: x['count'], reverse=True)
    
    def _extract_pattern(self, message: str) -> str:
        """Extract error pattern by removing variable parts"""
        # Remove timestamps
        pattern = re.sub(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}', '[TIMESTAMP]', message)
        # Remove IDs (UUIDs, instance IDs, etc.)
        pattern = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '[ID]', pattern)
        pattern = re.sub(r'i-[a-f0-9]+', '[INSTANCE-ID]', pattern)
        # Remove numbers
        pattern = re.sub(r'\d+', '[NUM]', pattern)
        # Remove excess whitespace
        pattern = ' '.join(pattern.split())
        
        return pattern[:200]  # Limit length
    
    def _save_to_database(self, regions: List[str], summary: Dict, duration: float, user_id: int) -> int:
        """Save post-mortem scan to database"""
        db = SessionLocal()
        try:
            scan = Scan(
                user_id=user_id,
                scan_type='postmortem',
                status='success',
                regions=regions,
                total_resources=summary.get('total_errors', 0) + summary.get('total_warnings', 0),
                total_cost=0,
                total_savings=0,
                duration_seconds=duration
            )
            db.add(scan)
            db.commit()
            db.refresh(scan)
            
            print(f"✅ Saved post-mortem scan to database (Scan ID: {scan.id})")
            return scan.id
        except Exception as e:
            db.rollback()
            print(f"❌ Error saving to database: {e}")
            return None
        finally:
            db.close()
    
    async def analyze(self, lookback_hours: int = 24, use_llm: bool = True, user_id: int = None):
        """
        Analyze CloudWatch Logs for incidents with optional LLM enhancement
        
        Args:
            lookback_hours: How many hours back to search
            use_llm: Whether to use Claude API for analysis
        """
        import time
        start_time = time.time()
        
        print(f"\n📋 Starting Post-Mortem Analysis...")
        print(f"   Lookback: {lookback_hours} hours")
        print(f"   LLM Analysis: {'Enabled' if (use_llm and self.llm_enabled) else 'Disabled'}")
        
        all_logs = []
        
        # Scan all regions
        for region in self.regions:
            print(f"\n📍 Scanning {region}...")
            log_groups = self._get_log_groups(region)
            
            if not log_groups:
                print(f"   No log groups found in {region}")
                continue
            
            print(f"   Found {len(log_groups)} log groups")
            
            for log_group in log_groups[:5]:  # Limit to 5 log groups
                print(f"   Searching {log_group}...")
                logs = self._search_logs(log_group, region, lookback_hours)
                all_logs.extend(logs)
        
        # Group errors
        error_patterns = self._group_errors(all_logs)
        
        # Build summary
        summary = {
            'total_errors': len(all_logs),
            'total_warnings': 0,  # Could enhance to count warnings separately
            'unique_patterns': len(error_patterns),
            'lookback_hours': lookback_hours
        }
        
        # LLM Analysis
        llm_analysis = None
        if use_llm and self.llm_enabled and error_patterns:
            try:
                llm_analysis = self.llm_analyzer.analyze_logs(error_patterns, summary)
            except Exception as e:
                print(f"⚠️ LLM analysis failed: {e}")
        
        # Generate recommendations
        if llm_analysis:
            recommendations = [
                f"[{rec['priority']}] {rec['title']}: {rec['description']}"
                for rec in llm_analysis.get('recommendations', [])[:5]
            ]
            executive_summary = llm_analysis.get('executive_summary', '')
        else:
            # Fallback to traditional recommendations
            recommendations = self._generate_traditional_recommendations(error_patterns)
            executive_summary = None
        
        # Save to database
        duration = time.time() - start_time
        scan_id = self._save_to_database(self.regions, summary, duration, user_id)
        
        print(f"\n✅ Post-Mortem Analysis Complete!")
        print(f"   Total errors found: {summary['total_errors']}")
        print(f"   Unique patterns: {summary['unique_patterns']}")
        if llm_analysis:
            print(f"   LLM root causes: {len(llm_analysis.get('root_causes', []))}")
            print(f"   LLM recommendations: {len(llm_analysis.get('recommendations', []))}")
        
        return {
            'status': 'success',
            'scan_id': scan_id,
            'regions_analyzed': self.regions,
            'lookback_hours': lookback_hours,
            'summary': summary,
            'error_patterns': error_patterns[:10],  # Top 10
            'recommendations': recommendations,
            'llm_analysis': llm_analysis,  # Include full LLM analysis
            'duration_seconds': duration
        }
    
    def _generate_traditional_recommendations(self, error_patterns: List[Dict]) -> List[str]:
        """Fallback recommendations if LLM is not available"""
        recommendations = []
        
        if not error_patterns:
            return ["No errors found - system appears healthy"]
        
        # Generic recommendations based on patterns
        top_pattern = error_patterns[0]
        recommendations.append(f"Investigate most frequent error: {top_pattern['pattern']} ({top_pattern['count']} occurrences)")
        
        if len(error_patterns) > 5:
            recommendations.append(f"Multiple error types detected ({len(error_patterns)} unique patterns) - consider systematic review")
        
        recommendations.append("Review CloudWatch Logs for detailed stack traces and context")
        recommendations.append("Set up CloudWatch Alarms for critical error patterns")
        
        return recommendations


# Maintain backward compatibility
PostMortemService = EnhancedPostMortemService
