"""
LLM-Powered Post-Mortem Analysis using Claude API
Intelligent log analysis, root cause detection, and actionable recommendations
"""
import os
from anthropic import Anthropic
from datetime import datetime
from typing import List, Dict, Any
import json
import re
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class LLMPostMortemAnalyzer:
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables. Please add it to backend/.env")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def analyze_logs(self, error_patterns: List[Dict], log_summary: Dict) -> Dict[str, Any]:
        """
        Use Claude to analyze logs and provide intelligent insights
        
        Args:
            error_patterns: List of grouped error patterns from traditional analysis
            log_summary: Summary statistics (total errors, warnings, etc.)
        
        Returns:
            {
                'executive_summary': str,
                'root_causes': List[Dict],
                'recommendations': List[Dict],
                'severity_assessment': str,
                'affected_services': List[str]
            }
        """
        print("\n🤖 Sending logs to Claude API for intelligent analysis...")
        
        # Prepare context for Claude
        context = self._prepare_context(error_patterns, log_summary)
        
        # Build prompt
        prompt = self._build_analysis_prompt(context)
        
        try:
            # Call Claude API
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
                'affected_services': []
            }
        except Exception as e:
            print(f"❌ Claude API error: {e}")
            return {
                'executive_summary': f'Error during LLM analysis: {str(e)}',
                'root_causes': [],
                'recommendations': [],
                'severity_assessment': 'ERROR',
                'affected_services': []
            }
    
    def _clean_json_response(self, text: str) -> str:
        """Remove markdown code blocks and clean JSON response"""
        # Remove ```json and ``` markers
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        text = text.strip()
        return text
    
    def _prepare_context(self, error_patterns: List[Dict], log_summary: Dict) -> Dict:
        """Prepare log data for Claude"""
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
      "description": "Detailed explanation",
      "evidence": "What in the logs supports this",
      "impact": "HIGH/MEDIUM/LOW",
      "affected_services": ["service1", "service2"]
    }}
  ],
  "recommendations": [
    {{
      "priority": "CRITICAL/HIGH/MEDIUM/LOW",
      "title": "Actionable recommendation title",
      "description": "Detailed steps to fix",
      "aws_service": "Relevant AWS service",
      "documentation_link": "Link to AWS docs if applicable"
    }}
  ],
  "severity_assessment": "CRITICAL/HIGH/MEDIUM/LOW",
  "affected_services": ["list", "of", "services"],
  "preventive_measures": [
    "Future prevention step 1",
    "Future prevention step 2"
  ]
}}

**Important:**
- Focus on AWS-specific insights (Lambda, EC2, RDS, etc.)
- Provide actionable recommendations with specific AWS service references
- Include AWS documentation links where relevant
- Identify patterns that might indicate larger systemic issues
- Consider cost implications if relevant

Return ONLY the JSON object, no markdown code blocks, no additional text."""

        return prompt
    
    def generate_executive_summary(self, analysis: Dict) -> str:
        """Generate a concise executive summary from analysis"""
        if 'executive_summary' in analysis:
            return analysis['executive_summary']
        
        # Fallback if no summary provided
        severity = analysis.get('severity_assessment', 'UNKNOWN')
        root_causes = len(analysis.get('root_causes', []))
        
        return f"{severity} severity incident detected. {root_causes} root causes identified. Immediate action recommended."


if __name__ == "__main__":
    # Test the analyzer
    print("🧪 Testing Claude API connection...")
    
    analyzer = LLMPostMortemAnalyzer()
    print("✅ API key loaded successfully!")
    
    test_patterns = [
        {
            'pattern': 'Lambda timeout exceeded',
            'count': 15,
            'example': '2024-12-20 10:30:15 ERROR Task timed out after 30.00 seconds'
        },
        {
            'pattern': 'DynamoDB ProvisionedThroughputExceededException',
            'count': 8,
            'example': '2024-12-20 10:31:22 ERROR Rate exceeded for table users'
        }
    ]
    
    test_summary = {
        'total_errors': 23,
        'total_warnings': 5,
        'lookback_hours': 24
    }
    
    result = analyzer.analyze_logs(test_patterns, test_summary)
    print("\n📋 Analysis Result:")
    print(json.dumps(result, indent=2))
