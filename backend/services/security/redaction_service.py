"""
PII and Secrets Redaction Service
Sanitizes logs before sending to external APIs (Claude, etc.)
"""
import re
from typing import Dict, List, Tuple


class RedactionService:
    """
    Redacts sensitive information from logs and text data
    
    Protects against:
    - API keys and tokens
    - Passwords and credentials
    - PII (emails, SSNs, credit cards, phone numbers)
    - AWS credentials
    - Database connection strings
    - IP addresses (optional - can be useful for debugging)
    - JWTs and session tokens
    """
    
    # Redaction patterns with explanations
    PATTERNS = {
        # AWS Credentials
        'aws_access_key': (
            r'AKIA[0-9A-Z]{16}',
            '[REDACTED_AWS_KEY]',
            'AWS Access Key ID'
        ),
        'aws_secret_key': (
            r'aws_secret_access_key["\']?\s*[:=]\s*["\']?([A-Za-z0-9/+=]{40})',
            '[REDACTED_AWS_SECRET]',
            'AWS Secret Access Key'
        ),
        
        # Generic API Keys and Tokens (improved pattern)
        'bearer_token': (
            r'Bearer\s+[A-Za-z0-9\-._~+/]+=*',
            'Bearer [REDACTED_TOKEN]',
            'Bearer Token'
        ),
        'api_key_pattern': (
            r'(api[_-]?key|apikey|api[_-]?token|token|key)[\s"\']*([:=]|:)[\s"\']*(sk_[a-z]+_[A-Za-z0-9]{20,}|[A-Za-z0-9\-._~+/]{20,})',
            r'\1=[REDACTED_API_KEY]',
            'API Key/Token'
        ),
        
        # Passwords
        'password_pattern': (
            r'(password|passwd|pwd|pass)[\s"\']*([:=]|:)[\s"\']?([^\s,;"\']{3,})',
            r'\1=[REDACTED_PASSWORD]',
            'Password'
        ),
        
        # Database Connection Strings
        'connection_string': (
            r'(mysql|postgresql|postgres|mongodb|redis):\/\/[^\s]+',
            r'\1://[REDACTED_CONNECTION_STRING]',
            'Database Connection String'
        ),
        
        # JWTs
        'jwt_token': (
            r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',
            '[REDACTED_JWT]',
            'JWT Token'
        ),
        
        # PII - Email Addresses
        'email': (
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[REDACTED_EMAIL]',
            'Email Address'
        ),
        
        # PII - Social Security Numbers
        'ssn': (
            r'\b\d{3}-\d{2}-\d{4}\b',
            '[REDACTED_SSN]',
            'Social Security Number'
        ),
        
        # PII - Credit Card Numbers
        'credit_card': (
            r'\b(?:\d{4}[\s\-]?){3}\d{4}\b',
            '[REDACTED_CC]',
            'Credit Card Number'
        ),
        
        # PII - Phone Numbers (US format)
        'phone_number': (
            r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
            '[REDACTED_PHONE]',
            'Phone Number'
        ),
        
        # Private Keys
        'private_key': (
            r'-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----[^-]+-----END (?:RSA |EC |DSA )?PRIVATE KEY-----',
            '[REDACTED_PRIVATE_KEY]',
            'Private Key'
        ),
    }
    
    # Optional: IP addresses - useful for debugging, but can be PII
    IP_PATTERN = (
        r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        '[REDACTED_IP]',
        'IP Address'
    )
    
    def __init__(self, redact_ips: bool = False):
        """
        Initialize redaction service
        
        Args:
            redact_ips: Whether to redact IP addresses (default: False for debugging)
        """
        self.redact_ips = redact_ips
        self.redaction_stats = {pattern_name: 0 for pattern_name in self.PATTERNS.keys()}
        if redact_ips:
            self.redaction_stats['ip_address'] = 0
    
    def redact(self, text: str) -> Tuple[str, Dict[str, int]]:
        """
        Redact sensitive information from text
        
        Args:
            text: Raw text that may contain sensitive data
            
        Returns:
            Tuple of (redacted_text, stats_dict)
            stats_dict shows how many of each pattern type were redacted
        """
        if not text:
            return text, {}
        
        redacted = text
        stats = {}
        
        # Apply each redaction pattern
        for pattern_name, (pattern, replacement, description) in self.PATTERNS.items():
            matches = re.findall(pattern, redacted, flags=re.IGNORECASE)
            count = len(matches)
            
            if count > 0:
                redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
                stats[pattern_name] = count
                self.redaction_stats[pattern_name] += count
        
        # Optionally redact IP addresses
        if self.redact_ips:
            ip_matches = re.findall(self.IP_PATTERN[0], redacted)
            ip_count = len(ip_matches)
            if ip_count > 0:
                redacted = re.sub(self.IP_PATTERN[0], self.IP_PATTERN[1], redacted)
                stats['ip_address'] = ip_count
                self.redaction_stats['ip_address'] += ip_count
        
        return redacted, stats
    
    def redact_log_events(self, log_events: List[Dict]) -> Tuple[List[Dict], Dict[str, int]]:
        """
        Redact sensitive information from CloudWatch log events
        
        Args:
            log_events: List of log event dicts with 'message' field
            
        Returns:
            Tuple of (redacted_events, total_stats)
        """
        redacted_events = []
        total_stats = {}
        
        for event in log_events:
            if 'message' in event:
                redacted_message, stats = self.redact(event['message'])
                
                # Merge stats
                for key, count in stats.items():
                    total_stats[key] = total_stats.get(key, 0) + count
                
                redacted_event = event.copy()
                redacted_event['message'] = redacted_message
                redacted_event['redacted'] = len(stats) > 0
                redacted_events.append(redacted_event)
            else:
                redacted_events.append(event)
        
        return redacted_events, total_stats
    
    def get_redaction_summary(self) -> Dict[str, int]:
        """Get cumulative redaction statistics"""
        return self.redaction_stats.copy()
    
    def reset_stats(self):
        """Reset redaction statistics"""
        self.redaction_stats = {pattern_name: 0 for pattern_name in self.PATTERNS.keys()}
        if self.redact_ips:
            self.redaction_stats['ip_address'] = 0


# Convenience function for one-off redactions
def redact_text(text: str, redact_ips: bool = False) -> str:
    """
    Quick redaction of text without stats tracking
    
    Args:
        text: Text to redact
        redact_ips: Whether to redact IP addresses
        
    Returns:
        Redacted text
    """
    service = RedactionService(redact_ips=redact_ips)
    redacted, _ = service.redact(text)
    return redacted
