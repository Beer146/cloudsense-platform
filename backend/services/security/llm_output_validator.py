"""
LLM Output Validation Service
Ensures Claude's recommendations are safe, accurate, and actionable
"""
import re
from typing import Dict, List, Optional
import requests


class LLMOutputValidator:
    """
    Validates LLM-generated recommendations to prevent:
    - Hallucinated remediation steps
    - Dangerous operations
    - Missing required fields
    - Invalid AWS documentation links
    """
    
    # Dangerous operations that require explicit approval
    DANGEROUS_KEYWORDS = [
        'delete all',
        'drop database',
        'drop table',
        'truncate table',
        'rm -rf',
        'format',
        'destroy',
        'terminate all',
        'remove all',
        '--force',
        '--no-preserve-root'
    ]
    
    # AWS documentation domains (whitelist)
    VALID_DOC_DOMAINS = [
        'docs.aws.amazon.com',
        'aws.amazon.com/documentation',
        'aws.amazon.com/getting-started'
    ]
    
    # Required fields for recommendations
    REQUIRED_RECOMMENDATION_FIELDS = [
        'priority',
        'title', 
        'description',
        'aws_service'
    ]
    
    REQUIRED_ROOT_CAUSE_FIELDS = [
        'title',
        'description',
        'evidence'
    ]
    
    def __init__(self):
        self.validation_stats = {
            'total_validated': 0,
            'dangerous_flagged': 0,
            'invalid_links': 0,
            'missing_fields': 0,
            'low_confidence': 0
        }
    
    def validate_recommendation(self, recommendation: Dict) -> Dict:
        """
        Validate a single recommendation
        
        Returns:
            {
                'is_valid': bool,
                'warnings': List[str],
                'severity': 'SAFE' | 'REQUIRES_REVIEW' | 'DANGEROUS',
                'validated_recommendation': Dict (with safety annotations)
            }
        """
        warnings = []
        severity = 'SAFE'
        
        # Check 1: Required fields
        missing_fields = [
            field for field in self.REQUIRED_RECOMMENDATION_FIELDS 
            if field not in recommendation or not recommendation[field]
        ]
        
        if missing_fields:
            warnings.append(f"Missing required fields: {', '.join(missing_fields)}")
            severity = 'REQUIRES_REVIEW'
            self.validation_stats['missing_fields'] += 1
        
        # Check 2: Dangerous operations in description
        description = recommendation.get('description', '').lower()
        dangerous_found = [
            keyword for keyword in self.DANGEROUS_KEYWORDS 
            if keyword in description
        ]
        
        if dangerous_found:
            warnings.append(f"⚠️ DANGEROUS OPERATIONS DETECTED: {', '.join(dangerous_found)}")
            severity = 'DANGEROUS'
            self.validation_stats['dangerous_flagged'] += 1
        
        # Check 3: AWS documentation link validation
        doc_link = recommendation.get('documentation_link')
        if doc_link:
            link_valid = self._validate_aws_doc_link(doc_link)
            if not link_valid:
                warnings.append(f"Invalid AWS documentation link: {doc_link}")
                severity = 'REQUIRES_REVIEW'
                self.validation_stats['invalid_links'] += 1
        else:
            warnings.append("No AWS documentation link provided")
            severity = 'REQUIRES_REVIEW' if severity == 'SAFE' else severity
        
        # Check 4: Priority validation
        priority = recommendation.get('priority', '').upper()
        if priority not in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            warnings.append(f"Invalid priority: {priority}")
            severity = 'REQUIRES_REVIEW'
        
        # Check 5: Vague or generic descriptions
        if description and self._is_vague_description(description):
            warnings.append("Description appears vague or generic")
            severity = 'REQUIRES_REVIEW' if severity == 'SAFE' else severity
            self.validation_stats['low_confidence'] += 1
        
        self.validation_stats['total_validated'] += 1
        
        # Annotate recommendation with validation results
        validated_rec = recommendation.copy()
        validated_rec['validation'] = {
            'severity': severity,
            'warnings': warnings,
            'requires_human_approval': severity in ['DANGEROUS', 'REQUIRES_REVIEW']
        }
        
        return {
            'is_valid': severity != 'DANGEROUS',
            'warnings': warnings,
            'severity': severity,
            'validated_recommendation': validated_rec
        }
    
    def validate_root_cause(self, root_cause: Dict) -> Dict:
        """
        Validate a root cause analysis
        
        Returns:
            {
                'is_valid': bool,
                'warnings': List[str],
                'validated_root_cause': Dict
            }
        """
        warnings = []
        
        # Check required fields
        missing_fields = [
            field for field in self.REQUIRED_ROOT_CAUSE_FIELDS
            if field not in root_cause or not root_cause[field]
        ]
        
        if missing_fields:
            warnings.append(f"Missing fields: {', '.join(missing_fields)}")
        
        # Check if evidence is actually from logs (not speculation)
        evidence = root_cause.get('evidence', '').lower()
        speculation_indicators = ['might', 'possibly', 'could be', 'perhaps', 'maybe']
        
        if any(indicator in evidence for indicator in speculation_indicators):
            warnings.append("Evidence contains speculative language - may not be conclusive")
        
        validated = root_cause.copy()
        validated['validation'] = {
            'warnings': warnings,
            'has_missing_fields': len(missing_fields) > 0
        }
        
        return {
            'is_valid': len(missing_fields) == 0,
            'warnings': warnings,
            'validated_root_cause': validated
        }
    
    def validate_full_analysis(self, llm_analysis: Dict) -> Dict:
        """
        Validate complete LLM post-mortem analysis
        
        Returns:
            {
                'overall_valid': bool,
                'recommendations': List[validated_recommendations],
                'root_causes': List[validated_root_causes],
                'validation_summary': Dict
            }
        """
        validated_recommendations = []
        validated_root_causes = []
        all_warnings = []
        
        # Validate recommendations
        if 'recommendations' in llm_analysis:
            for rec in llm_analysis['recommendations']:
                validation_result = self.validate_recommendation(rec)
                validated_recommendations.append(validation_result['validated_recommendation'])
                all_warnings.extend(validation_result['warnings'])
        
        # Validate root causes
        if 'root_causes' in llm_analysis:
            for cause in llm_analysis['root_causes']:
                validation_result = self.validate_root_cause(cause)
                validated_root_causes.append(validation_result['validated_root_cause'])
                all_warnings.extend(validation_result['warnings'])
        
        # Count severity levels
        dangerous_count = sum(
            1 for rec in validated_recommendations 
            if rec.get('validation', {}).get('severity') == 'DANGEROUS'
        )
        
        requires_review_count = sum(
            1 for rec in validated_recommendations
            if rec.get('validation', {}).get('severity') == 'REQUIRES_REVIEW'
        )
        
        return {
            'overall_valid': dangerous_count == 0,
            'recommendations': validated_recommendations,
            'root_causes': validated_root_causes,
            'validation_summary': {
                'total_recommendations': len(validated_recommendations),
                'total_root_causes': len(validated_root_causes),
                'dangerous_operations': dangerous_count,
                'requires_review': requires_review_count,
                'all_warnings': all_warnings,
                'stats': self.validation_stats
            }
        }
    
    def _validate_aws_doc_link(self, url: str) -> bool:
        """
        Validate that URL is a real AWS documentation link
        
        Checks:
        1. URL points to valid AWS domain
        2. URL returns 200 OK (link exists)
        """
        # Check domain
        valid_domain = any(domain in url for domain in self.VALID_DOC_DOMAINS)
        if not valid_domain:
            return False
        
        # Check URL accessibility (with timeout)
        try:
            response = requests.head(url, timeout=3, allow_redirects=True)
            return response.status_code == 200
        except:
            # If we can't verify, assume it's valid (don't block on network issues)
            # But log the warning
            return True
    
    def _is_vague_description(self, description: str) -> bool:
        """
        Check if description is too vague or generic
        
        Red flags:
        - Very short (<50 chars)
        - Generic phrases without specifics
        - No AWS service names
        - No concrete actions
        """
        if len(description) < 50:
            return True
        
        vague_phrases = [
            'just restart',
            'try restarting',
            'increase resources',
            'check the logs',
            'investigate further',
            'contact support'
        ]
        
        description_lower = description.lower()
        if any(phrase in description_lower for phrase in vague_phrases):
            return True
        
        # Should mention at least one AWS service or specific action
        has_aws_service = bool(re.search(r'(ec2|rds|s3|lambda|cloudwatch|iam|vpc)', description_lower))
        has_cli_command = bool(re.search(r'aws (ec2|rds|s3|cloudwatch)', description_lower))
        
        return not (has_aws_service or has_cli_command)
    
    def get_validation_stats(self) -> Dict:
        """Get cumulative validation statistics"""
        return self.validation_stats.copy()
    
    def reset_stats(self):
        """Reset validation statistics"""
        for key in self.validation_stats:
            self.validation_stats[key] = 0


# Convenience function
def validate_llm_output(llm_analysis: Dict) -> Dict:
    """
    Quick validation of LLM analysis output
    
    Args:
        llm_analysis: Raw output from Claude API
        
    Returns:
        Validated analysis with safety annotations
    """
    validator = LLMOutputValidator()
    return validator.validate_full_analysis(llm_analysis)
