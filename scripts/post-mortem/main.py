"""
Post-Mortem Generator
Analyzes CloudWatch Logs to generate incident reports
"""
import boto3
import yaml
from datetime import datetime, timedelta
from collections import defaultdict
import re
from typing import List, Dict, Any


class PostMortemGenerator:
    def __init__(self, config_path='config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.error_keywords = self.config['analysis']['error_keywords']
        self.warning_keywords = self.config['analysis']['warning_keywords']
        self.lookback_hours = self.config['analysis']['lookback_hours']
    
    def get_log_groups(self, region: str) -> List[str]:
        """Get all CloudWatch log groups in a region"""
        try:
            client = boto3.client('logs', region_name=region)
            paginator = client.get_paginator('describe_log_groups')
            
            log_groups = []
            for page in paginator.paginate():
                for group in page['logGroups']:
                    log_groups.append(group['logGroupName'])
            
            return log_groups
        except Exception as e:
            print(f"Error getting log groups in {region}: {e}")
            return []
    
    def search_logs(self, region: str, log_group: str) -> List[Dict[str, Any]]:
        """Search for errors and warnings in a log group"""
        try:
            client = boto3.client('logs', region_name=region)
            
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=self.lookback_hours)
            
            start_ms = int(start_time.timestamp() * 1000)
            end_ms = int(end_time.timestamp() * 1000)
            
            # Build filter pattern for errors and warnings
            keywords = self.error_keywords + self.warning_keywords
            filter_pattern = ' OR '.join([f'"{kw}"' for kw in keywords])
            
            events = []
            
            try:
                paginator = client.get_paginator('filter_log_events')
                for page in paginator.paginate(
                    logGroupName=log_group,
                    startTime=start_ms,
                    endTime=end_ms,
                    filterPattern=filter_pattern,
                    PaginationConfig={'MaxItems': self.config['analysis']['max_log_events']}
                ):
                    for event in page.get('events', []):
                        events.append({
                            'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000),
                            'message': event['message'],
                            'log_group': log_group,
                            'region': region,
                            'severity': self._classify_severity(event['message'])
                        })
            except client.exceptions.ResourceNotFoundException:
                print(f"Log group {log_group} not found")
                return []
            
            return events
            
        except Exception as e:
            print(f"Error searching logs in {log_group}: {e}")
            return []
    
    def _classify_severity(self, message: str) -> str:
        """Classify log message severity"""
        message_upper = message.upper()
        
        for keyword in self.error_keywords:
            if keyword.upper() in message_upper:
                return 'ERROR'
        
        for keyword in self.warning_keywords:
            if keyword.upper() in message_upper:
                return 'WARNING'
        
        return 'INFO'
    
    def group_similar_errors(self, events: List[Dict]) -> Dict[str, List[Dict]]:
        """Group similar error messages together"""
        grouped = defaultdict(list)
        
        for event in events:
            # Extract error pattern (remove timestamps, IDs, etc.)
            pattern = self._extract_error_pattern(event['message'])
            grouped[pattern].append(event)
        
        return dict(grouped)
    
    def _extract_error_pattern(self, message: str) -> str:
        """Extract error pattern by removing variable parts"""
        # Remove timestamps
        pattern = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', '[TIMESTAMP]', message)
        
        # Remove UUIDs
        pattern = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '[UUID]', pattern, flags=re.IGNORECASE)
        
        # Remove IP addresses
        pattern = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '[IP]', pattern)
        
        # Remove numeric IDs
        pattern = re.sub(r'\b\d{5,}\b', '[ID]', pattern)
        
        # Take first 100 chars as pattern
        return pattern[:100]
    
    def generate_recommendations(self, grouped_errors: Dict) -> List[str]:
        """Generate recommendations based on error patterns"""
        recommendations = []
        
        for pattern, events in grouped_errors.items():
            if len(events) > 10:
                recommendations.append(
                    f"🔴 HIGH FREQUENCY: Error pattern occurred {len(events)} times - "
                    f"investigate root cause: '{pattern[:80]}...'"
                )
        
        # Check for common issues
        all_messages = ' '.join([e['message'] for events in grouped_errors.values() for e in events])
        
        if 'timeout' in all_messages.lower():
            recommendations.append("⚠️ TIMEOUT DETECTED: Consider increasing timeout values or optimizing slow operations")
        
        if 'connection refused' in all_messages.lower() or 'connection reset' in all_messages.lower():
            recommendations.append("⚠️ CONNECTION ISSUES: Check network connectivity, security groups, and service availability")
        
        if 'out of memory' in all_messages.lower() or 'memory' in all_messages.lower():
            recommendations.append("⚠️ MEMORY ISSUES: Review memory allocation and check for memory leaks")
        
        if 'permission denied' in all_messages.lower() or 'unauthorized' in all_messages.lower():
            recommendations.append("⚠️ PERMISSION ISSUES: Review IAM roles and resource policies")
        
        return recommendations
    
    def generate_report(self, all_events: List[Dict]) -> Dict[str, Any]:
        """Generate structured post-mortem report"""
        if not all_events:
            return {
                'status': 'no_incidents',
                'message': 'No errors or warnings found in the specified time period'
            }
        
        # Sort by timestamp
        all_events.sort(key=lambda x: x['timestamp'])
        
        # Separate by severity
        errors = [e for e in all_events if e['severity'] == 'ERROR']
        warnings = [e for e in all_events if e['severity'] == 'WARNING']
        
        # Group similar errors
        grouped_errors = self.group_similar_errors(errors) if errors else {}
        
        # Generate recommendations
        recommendations = self.generate_recommendations(grouped_errors)
        
        # Build timeline
        timeline = []
        for event in all_events[:50]:  # Top 50 events
            timeline.append({
                'timestamp': event['timestamp'].isoformat(),
                'severity': event['severity'],
                'log_group': event['log_group'],
                'region': event['region'],
                'message': event['message'][:200]  # Truncate long messages
            })
        
        return {
            'status': 'success',
            'summary': {
                'total_errors': len(errors),
                'total_warnings': len(warnings),
                'unique_error_patterns': len(grouped_errors),
                'time_range': {
                    'start': all_events[0]['timestamp'].isoformat(),
                    'end': all_events[-1]['timestamp'].isoformat()
                },
                'affected_log_groups': list(set([e['log_group'] for e in all_events]))
            },
            'timeline': timeline,
            'error_patterns': [
                {
                    'pattern': pattern[:100],
                    'count': len(events),
                    'first_occurrence': events[0]['timestamp'].isoformat(),
                    'last_occurrence': events[-1]['timestamp'].isoformat(),
                    'example': events[0]['message'][:300]
                }
                for pattern, events in sorted(grouped_errors.items(), key=lambda x: len(x[1]), reverse=True)[:10]
            ],
            'recommendations': recommendations
        }
    
    def analyze(self, regions: List[str] = None) -> Dict[str, Any]:
        """Run full post-mortem analysis"""
        analyze_regions = regions or self.config['aws']['regions']
        
        print(f"\n🔍 Starting Post-Mortem Analysis...")
        print(f"📅 Analyzing last {self.lookback_hours} hours")
        print(f"📍 Regions: {', '.join(analyze_regions)}\n")
        
        all_events = []
        
        for region in analyze_regions:
            print(f"\n{'='*80}")
            print(f"Region: {region}")
            print(f"{'='*80}\n")
            
            # Get log groups
            log_groups = self.get_log_groups(region)
            print(f"Found {len(log_groups)} log groups")
            
            # Search each log group
            for log_group in log_groups:
                print(f"Scanning {log_group}...", end=' ')
                events = self.search_logs(region, log_group)
                
                if events:
                    print(f"✅ Found {len(events)} events")
                    all_events.extend(events)
                else:
                    print("✓ Clean")
        
        print(f"\n{'='*80}")
        print(f"ANALYSIS COMPLETE")
        print(f"{'='*80}\n")
        
        print(f"📊 Total Events Found: {len(all_events)}")
        print(f"🔴 Errors: {len([e for e in all_events if e['severity'] == 'ERROR'])}")
        print(f"⚠️  Warnings: {len([e for e in all_events if e['severity'] == 'WARNING'])}")
        
        return self.generate_report(all_events)


def main():
    generator = PostMortemGenerator()
    report = generator.analyze()
    
    if report['status'] == 'success':
        print(f"\n{'='*80}")
        print("POST-MORTEM REPORT")
        print(f"{'='*80}\n")
        
        print("📊 SUMMARY:")
        print(f"  Total Errors: {report['summary']['total_errors']}")
        print(f"  Total Warnings: {report['summary']['total_warnings']}")
        print(f"  Unique Error Patterns: {report['summary']['unique_error_patterns']}")
        print(f"  Time Range: {report['summary']['time_range']['start']} to {report['summary']['time_range']['end']}")
        
        if report['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"  {rec}")
        
        if report['error_patterns']:
            print(f"\n🔴 TOP ERROR PATTERNS:")
            for i, pattern in enumerate(report['error_patterns'][:5], 1):
                print(f"\n  {i}. Pattern: {pattern['pattern']}")
                print(f"     Occurrences: {pattern['count']}")
                print(f"     First: {pattern['first_occurrence']}")
                print(f"     Last: {pattern['last_occurrence']}")
    else:
        print(f"\n✅ {report['message']}")


if __name__ == '__main__':
    main()
