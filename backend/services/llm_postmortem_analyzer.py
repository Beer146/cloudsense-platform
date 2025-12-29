"""
LLM-powered Post-Mortem Analysis using Claude API
WITH PII/SECRETS REDACTION
"""
import os
import json
import re
from typing import List, Dict, Any
from anthropic import Anthropic
from dotenv import load_dotenv
from services.security.redaction_service import RedactionService

load_dotenv()


class LLMPostMortemAnalyzer:
    """Uses Claude to analyze CloudWatch logs and provide intelligent post-mortem insights"""
    
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        
        # Initialize redaction service
        # redact_ips=False keeps IPs for debugging (they're useful for infrastructure logs)
        self.redactor = RedactionService(redact_ips=False)
        
        print("✅ LLM Post-Mortem Analyzer enabled")
        print(f"   Model: {self.model}")
        print(f"   🔒 PII/Secrets redaction: ENABLED")
    
    def analyze_logs(self, error_patterns: List[Dict], log_summary: Dict) -> Dict[str, Any]:
        """
        Use Claude to analyze logs and provide intelligent insights
        WITH AUTOMATIC PII/SECRETS REDACTION
        
        Args:
            error_patterns: List of grouped error patterns from traditional analysis
            log_summary: Summary statistics (total errors, warnings, etc.)
        
        Returns:
            {
                'executive_summary': str,
                'root_causes': List[Dict],
                'recommendations': List[Dict],
                'severity_assessment': str,
                'affected_services': List[str],
                'redaction_stats': Dict[str, int]  # NEW: Shows what was redacted
            }
        """
        print("\n🤖 Preparing logs for Claude API analysis...")
        
        # SECURITY: Redact sensitive data from error patterns BEFORE sending to Claude
        redacted_patterns, redaction_stats = self._redact_error_patterns(error_patterns)
        
        if redaction_stats:
            print(f"   🔒 Redacted {sum(redaction_stats.values())} sensitive items:")
            for redaction_type, count in redaction_stats.items():
                print(f"      - {redaction_type}: {count}")
        else:
            print(f"   ✅ No sensitive data detected in logs")
        
        # Prepare context for Claude (now with redacted data)
        context = self._prepare_context(redacted_patterns, log_summary)
        
        # Build prompt
        prompt = self._build_analysis_prompt(context)
        
        try:
            print("   📤 Sending to Claude API...")
            
            # Call Claude API (data is already redacted)
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for more consistent analysis
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse response
            response_text = message.content[0].text
            
            # Remove markdown code blocks if present
            response_text = self._clean_json_response(response_text)
            
            # Claude will return structured JSON
            analysis = json.loads(response_text)
            
            # Add redaction stats to response for transparency
            analysis['redaction_stats'] = redaction_stats
            
            print(f"✅ Claude analysis complete!")
            print(f"   Root causes identified: {len(analysis.get('root_causes', []))}")
            print(f"   Recommendations: {len(analysis.get('recommendations', []))}")
            
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse Claude response as JSON: {e}")
            print(f"   Response text: {response_text[:200]}...")
            # Fallback: return text-based response
            return {
                'executive_summary': response_text,
                'root_causes': [],
                'recommendations': [],
                'severity_assessment': 'UNKNOWN',
                'affected_services': [],
                'redaction_stats': redaction_stats
            }
        except Exception as e:
            print(f"❌ Claude API error: {e}")
            return {
                'executive_summary': f'Error during LLM analysis: {str(e)}',
                'root_causes': [],
                'recommendations': [],
                'severity_assessment': 'ERROR',
                'affected_services': [],
                'redaction_stats': redaction_stats
            }
    
    def _redact_error_patterns(self, error_patterns: List[Dict]) -> tuple[List[Dict], Dict[str, int]]:
        """
        Redact sensitive information from error patterns
        
        Args:
            error_patterns: Raw error patterns that may contain PII/secrets
            
        Returns:
            Tuple of (redacted_patterns, redaction_stats)
        """
        redacted_patterns = []
        total_stats = {}
        
        for pattern in error_patterns:
            redacted_pattern = pattern.copy()
            
            # Redact the error pattern text
            if 'pattern' in pattern:
                redacted_text, stats = self.redactor.redact(pattern['pattern'])
                redacted_pattern['pattern'] = redacted_text
                
                # Merge stats
                for key, count in stats.items():
                    total_stats[key] = total_stats.get(key, 0) + count
            
            # Redact example log messages
            if 'example' in pattern:
                redacted_example, stats = self.redactor.redact(pattern['example'])
                redacted_pattern['example'] = redacted_example
                
                # Merge stats
                for key, count in stats.items():
                    total_stats[key] = total_stats.get(key, 0) + count
            
            # Redact any log samples
            if 'logs' in pattern and isinstance(pattern['logs'], list):
                redacted_logs = []
                for log in pattern['logs']:
                    redacted_log, stats = self.redactor.redact(log)
                    redacted_logs.append(redacted_log)
                    
                    # Merge stats
                    for key, count in stats.items():
                        total_stats[key] = total_stats.get(key, 0) + count
                
                redacted_pattern['logs'] = redacted_logs
            
            redacted_patterns.append(redacted_pattern)
        
        return redacted_patterns, total_stats
    
    def _clean_json_response(self, text: str) -> str:
        """Remove markdown code blocks and clean JSON response"""
        # Remove ```json and ``` markers
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        text = text.strip()
        return text
    
    def _prepare_context(self, error_patterns: List[Dict], log_summary: Dict) -> Dict:
        """
        Prepare log data for Claude
        Note: error_patterns should already be redacted at this point
        """
        return {
            'total_errors': log_summary.get('total_errors', 0),
            'total_warnings': log_summary.get('total_warnings', 0),
            'unique_patterns': len(error_patterns),
            'error_patterns': error_patterns[:20],  # Limit to top 20 patterns
            'timeframe': f"{log_summary.get('lookback_hours', 24)} hours"
        }
    
    def _build_analysis_prompt(self, context: Dict) -> str:
        """Build prompt for Claude"""
        
        patterns_text = ""
        for i, pattern in enumerate(context['error_patterns'][:10], 1):
            patterns_text += f"\n{i}. Pattern: {pattern.get('pattern', 'Unknown')}\n"
            patterns_text += f"   Occurrences: {pattern.get('count', 0)}\n"
            patterns_text += f"   Example: {pattern.get('example', '')[:200]}...\n"
        
        prompt = f"""You are an AWS infrastructure expert analyzing CloudWatch logs for a post-mortem incident report.

**IMPORTANT:** Some sensitive data has been redacted (e.g., [REDACTED_PASSWORD], [REDACTED_API_KEY]). Focus your analysis on the error patterns and infrastructure issues, not the redacted values.

**Log Summary:**
- Timeframe: Last {context['timeframe']}
- Total Errors: {context['total_errors']}
- Total Warnings: {context['total_warnings']}
- Unique Error Patterns: {context['unique_patterns']}

**Top Error Patterns:**
{patterns_text}

**Your Task:**
Analyze these logs and provide a comprehensive post-mortem report in **valid JSON format** with the following structure:

{{
  "executive_summary": "2-3 sentence high-level summary for executives",
  "root_causes": [
    {{
      "title": "Brief title of root cause",
      "description": "Detailed explanation of what went wrong",
      "evidence": "What in the logs supports this conclusion",
      "impact": "Business impact of this issue",
      "affected_services": ["service1", "service2"]
    }}
  ],
  "recommendations": [
    {{
      "priority": "CRITICAL|HIGH|MEDIUM|LOW",
      "title": "Recommendation title",
      "description": "Detailed remediation steps",
      "aws_service": "AWS service name",
      "documentation_link": "https://docs.aws.amazon.com/..."
    }}
  ],
  "severity_assessment": "CRITICAL|HIGH|MEDIUM|LOW",
  "affected_services": ["list", "of", "services"],
  "preventive_measures": ["Future prevention step 1", "Step 2"]
}}

**Requirements:**
1. Be specific with AWS service names and exact error types
2. Provide actionable recommendations with AWS CLI commands or console steps
3. Include valid AWS documentation links
4. Prioritize recommendations by severity
5. Do NOT speculate about redacted values - work with what's visible
6. Focus on infrastructure root causes, not just symptoms

Return ONLY the JSON, no additional text."""
        
        return prompt
