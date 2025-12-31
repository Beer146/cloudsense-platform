"""
LLM-powered Post-Mortem Analysis using Claude API
WITH PII/SECRETS REDACTION AND OUTPUT VALIDATION
"""
import os
import json
import re
from typing import List, Dict, Any
from anthropic import Anthropic
from dotenv import load_dotenv
from services.security.redaction_service import RedactionService
from services.security.llm_output_validator import LLMOutputValidator

load_dotenv()


class LLMPostMortemAnalyzer:
    """Uses Claude to analyze CloudWatch logs with security and validation"""
    
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        
        # Initialize redaction service
        self.redactor = RedactionService(redact_ips=False)
        
        # Initialize validation service
        self.validator = LLMOutputValidator()
        
        print("✅ LLM Post-Mortem Analyzer enabled")
        print(f"   Model: {self.model}")
        print(f"   🔒 PII/Secrets redaction: ENABLED")
        print(f"   ✅ Output validation: ENABLED")
    
    def analyze_logs(self, error_patterns: List[Dict], log_summary: Dict) -> Dict[str, Any]:
        """
        Use Claude to analyze logs with automatic validation
        
        Returns analysis with validation annotations
        """
        print("\n🤖 Preparing logs for Claude API analysis...")
        
        # STEP 1: Redact sensitive data
        redacted_patterns, redaction_stats = self._redact_error_patterns(error_patterns)
        
        if redaction_stats:
            print(f"   🔒 Redacted {sum(redaction_stats.values())} sensitive items:")
            for redaction_type, count in redaction_stats.items():
                print(f"      - {redaction_type}: {count}")
        else:
            print(f"   ✅ No sensitive data detected in logs")
        
        # STEP 2: Get analysis from Claude
        context = self._prepare_context(redacted_patterns, log_summary)
        prompt = self._build_analysis_prompt(context)
        
        try:
            print("   📤 Sending to Claude API...")
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            response_text = self._clean_json_response(response_text)
            
            # Parse Claude's response
            analysis = json.loads(response_text)
            
            print(f"   ✅ Claude analysis received")
            
            # STEP 3: Validate LLM output
            print(f"   🔍 Validating LLM output...")
            
            validation_result = self.validator.validate_full_analysis(analysis)
            
            # Log validation results
            summary = validation_result['validation_summary']
            print(f"      Total recommendations: {summary['total_recommendations']}")
            print(f"      Dangerous operations flagged: {summary['dangerous_operations']}")
            print(f"      Requires review: {summary['requires_review']}")
            
            if summary['dangerous_operations'] > 0:
                print(f"      ⚠️ DANGEROUS OPERATIONS DETECTED - Human approval required!")
            
            # Combine original analysis with validation
            validated_analysis = {
                'executive_summary': analysis.get('executive_summary'),
                'root_causes': validation_result['root_causes'],
                'recommendations': validation_result['recommendations'],
                'severity_assessment': analysis.get('severity_assessment'),
                'affected_services': analysis.get('affected_services'),
                'preventive_measures': analysis.get('preventive_measures'),
                'redaction_stats': redaction_stats,
                'validation_summary': validation_result['validation_summary']
            }
            
            return validated_analysis
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse Claude response as JSON: {e}")
            return {
                'executive_summary': response_text,
                'root_causes': [],
                'recommendations': [],
                'severity_assessment': 'UNKNOWN',
                'affected_services': [],
                'redaction_stats': redaction_stats,
                'validation_summary': {'error': 'Failed to parse JSON'}
            }
        except Exception as e:
            print(f"❌ Claude API error: {e}")
            return {
                'executive_summary': f'Error during LLM analysis: {str(e)}',
                'root_causes': [],
                'recommendations': [],
                'severity_assessment': 'ERROR',
                'affected_services': [],
                'redaction_stats': redaction_stats,
                'validation_summary': {'error': str(e)}
            }
    
    def _redact_error_patterns(self, error_patterns: List[Dict]) -> tuple[List[Dict], Dict[str, int]]:
        """Redact sensitive information from error patterns"""
        redacted_patterns = []
        total_stats = {}
        
        for pattern in error_patterns:
            redacted_pattern = pattern.copy()
            
            if 'pattern' in pattern:
                redacted_text, stats = self.redactor.redact(pattern['pattern'])
                redacted_pattern['pattern'] = redacted_text
                for key, count in stats.items():
                    total_stats[key] = total_stats.get(key, 0) + count
            
            if 'example' in pattern:
                redacted_example, stats = self.redactor.redact(pattern['example'])
                redacted_pattern['example'] = redacted_example
                for key, count in stats.items():
                    total_stats[key] = total_stats.get(key, 0) + count
            
            if 'logs' in pattern and isinstance(pattern['logs'], list):
                redacted_logs = []
                for log in pattern['logs']:
                    redacted_log, stats = self.redactor.redact(log)
                    redacted_logs.append(redacted_log)
                    for key, count in stats.items():
                        total_stats[key] = total_stats.get(key, 0) + count
                redacted_pattern['logs'] = redacted_logs
            
            redacted_patterns.append(redacted_pattern)
        
        return redacted_patterns, total_stats
    
    def _clean_json_response(self, text: str) -> str:
        """Remove markdown code blocks"""
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        return text.strip()
    
    def _prepare_context(self, error_patterns: List[Dict], log_summary: Dict) -> Dict:
        """Prepare log data for Claude"""
        return {
            'total_errors': log_summary.get('total_errors', 0),
            'total_warnings': log_summary.get('total_warnings', 0),
            'unique_patterns': len(error_patterns),
            'error_patterns': error_patterns[:20],
            'timeframe': f"{log_summary.get('lookback_hours', 24)} hours"
        }
    
    def _build_analysis_prompt(self, context: Dict) -> str:
        """Build prompt for Claude with validation requirements"""
        
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
Analyze these logs and provide a comprehensive post-mortem report in **valid JSON format**.

**CRITICAL REQUIREMENTS FOR RECOMMENDATIONS:**
1. EVERY recommendation MUST include a valid AWS documentation link
2. Be SPECIFIC with exact AWS CLI commands or console steps
3. NO vague suggestions like "just restart" or "try increasing resources"
4. NO dangerous operations without explicit warnings (delete, drop, rm -rf, etc.)
5. Include concrete, actionable steps that can be verified

**JSON Structure:**
{{
  "executive_summary": "2-3 sentence high-level summary for executives",
  "root_causes": [
    {{
      "title": "Brief title of root cause",
      "description": "Detailed explanation of what went wrong",
      "evidence": "Specific log entries or metrics that support this conclusion",
      "impact": "Business impact of this issue",
      "affected_services": ["service1", "service2"]
    }}
  ],
  "recommendations": [
    {{
      "priority": "CRITICAL|HIGH|MEDIUM|LOW",
      "title": "Specific, actionable recommendation title",
      "description": "Detailed remediation steps with exact AWS CLI commands or console navigation. Be SPECIFIC - include resource names, parameter values, and step-by-step instructions.",
      "aws_service": "Exact AWS service name (e.g., Amazon RDS, Amazon EC2)",
      "documentation_link": "https://docs.aws.amazon.com/... (REQUIRED - must be a real AWS doc link)"
    }}
  ],
  "severity_assessment": "CRITICAL|HIGH|MEDIUM|LOW",
  "affected_services": ["list", "of", "services"],
  "preventive_measures": ["Future prevention step 1", "Step 2"]
}}

**Examples of GOOD recommendations:**
✅ "Enable Multi-AZ: aws rds modify-db-instance --db-instance-identifier prod-db --multi-az --apply-immediately. Doc: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html"

✅ "Configure CloudWatch alarm: aws cloudwatch put-metric-alarm --alarm-name high-cpu --metric-name CPUUtilization --threshold 80. Doc: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html"

**Examples of BAD recommendations (DO NOT DO THIS):**
❌ "Just restart the server"
❌ "Increase resources and monitor"  
❌ "Delete the database and recreate it"
❌ "Try increasing memory" (no specifics)

Return ONLY the JSON, no additional text."""
        
        return prompt

    def analyze_logs_with_rate_limiting(
        self, 
        error_patterns: List[Dict], 
        log_summary: Dict,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Analyze logs with rate limiting and cost controls
        
        Args:
            error_patterns: Error patterns from logs
            log_summary: Summary statistics
            user_id: User ID for rate limiting
            
        Returns:
            Analysis with rate limit info or fallback to rule-based
        """
        from services.security.rate_limiter import get_rate_limiter
        
        limiter = get_rate_limiter()
        
        # Check rate limits
        rate_allowed, rate_reason = limiter.check_rate_limit(user_id)
        if not rate_allowed:
            print(f"   ⚠️ Rate limit exceeded: {rate_reason}")
            return {
                'executive_summary': 'Rate limit exceeded. Using rule-based analysis only.',
                'root_causes': [],
                'recommendations': [],
                'severity_assessment': 'UNKNOWN',
                'affected_services': [],
                'rate_limit_exceeded': True,
                'rate_limit_reason': rate_reason,
                'fallback_mode': 'RULE_BASED'
            }
        
        # Check cost limits
        cost_allowed, cost_reason = limiter.check_cost_limit(user_id)
        if not cost_allowed:
            print(f"   ⚠️ Cost limit exceeded: {cost_reason}")
            return {
                'executive_summary': 'Daily cost limit exceeded. Using rule-based analysis only.',
                'root_causes': [],
                'recommendations': [],
                'severity_assessment': 'UNKNOWN',
                'affected_services': [],
                'cost_limit_exceeded': True,
                'cost_limit_reason': cost_reason,
                'fallback_mode': 'RULE_BASED'
            }
        
        # Proceed with LLM analysis
        print(f"   ✅ Rate limits OK - proceeding with LLM analysis")
        
        result = self.analyze_logs(error_patterns, log_summary)
        
        # Estimate token usage (rough approximation)
        # In production, get actual usage from Anthropic API response
        estimated_input_tokens = len(str(error_patterns)) * 0.25  # ~4 chars per token
        estimated_output_tokens = len(str(result)) * 0.25
        
        # Record usage
        limiter.record_request(
            user_id,
            input_tokens=int(estimated_input_tokens),
            output_tokens=int(estimated_output_tokens)
        )
        
        # Add usage stats to response
        stats = limiter.get_user_stats(user_id)
        result['usage_stats'] = stats
        
        return result
