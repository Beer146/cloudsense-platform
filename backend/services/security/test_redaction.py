"""
Tests for RedactionService
Run with: python -m pytest services/security/test_redaction.py -v
"""
import pytest
from redaction_service import RedactionService, redact_text


def test_aws_credentials():
    """Test AWS credential redaction"""
    service = RedactionService()
    
    text = "AWS Key: AKIAIOSFODNN7EXAMPLE and secret: aws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    redacted, stats = service.redact(text)
    
    assert 'AKIAIOSFODNN7EXAMPLE' not in redacted
    assert 'REDACTED_AWS_KEY' in redacted
    assert 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY' not in redacted
    assert 'REDACTED_AWS_SECRET' in redacted
    assert stats['aws_access_key'] == 1


def test_api_keys():
    """Test API key redaction"""
    service = RedactionService()
    
    text = 'api_key=sk_live_51H7xK2L3M4N5O6P7Q8R9S and apikey: "test_key_12345abcdef"'
    redacted, stats = service.redact(text)
    
    assert 'sk_live_51H7xK2L3M4N5O6P7Q8R9S' not in redacted
    assert 'test_key_12345abcdef' not in redacted
    assert 'REDACTED_API_KEY' in redacted
    assert stats['api_key_pattern'] >= 1


def test_passwords():
    """Test password redaction"""
    service = RedactionService()
    
    text = 'password=SuperSecret123! and pwd: "admin@2024"'
    redacted, stats = service.redact(text)
    
    assert 'SuperSecret123!' not in redacted
    assert 'admin@2024' not in redacted
    assert 'REDACTED_PASSWORD' in redacted
    assert stats['password_pattern'] >= 1


def test_connection_strings():
    """Test database connection string redaction"""
    service = RedactionService()
    
    text = 'DB: postgresql://user:pass@localhost:5432/mydb and mongodb://admin:secret@cluster.mongodb.net/db'
    redacted, stats = service.redact(text)
    
    assert 'user:pass@localhost' not in redacted
    assert 'admin:secret@cluster' not in redacted
    assert 'REDACTED_CONNECTION_STRING' in redacted
    assert stats['connection_string'] >= 1


def test_jwt_tokens():
    """Test JWT redaction"""
    service = RedactionService()
    
    text = 'Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
    redacted, stats = service.redact(text)
    
    assert 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9' not in redacted
    assert 'REDACTED_JWT' in redacted
    assert stats['jwt_token'] == 1


def test_pii_email():
    """Test email address redaction"""
    service = RedactionService()
    
    text = 'Contact: john.doe@example.com or support@company.io'
    redacted, stats = service.redact(text)
    
    assert 'john.doe@example.com' not in redacted
    assert 'support@company.io' not in redacted
    assert 'REDACTED_EMAIL' in redacted
    assert stats['email'] == 2


def test_pii_ssn():
    """Test SSN redaction"""
    service = RedactionService()
    
    text = 'SSN: 123-45-6789'
    redacted, stats = service.redact(text)
    
    assert '123-45-6789' not in redacted
    assert 'REDACTED_SSN' in redacted
    assert stats['ssn'] == 1


def test_pii_credit_card():
    """Test credit card redaction"""
    service = RedactionService()
    
    text = 'Card: 4532-1234-5678-9010 and 5425233430109903'
    redacted, stats = service.redact(text)
    
    assert '4532-1234-5678-9010' not in redacted
    assert '5425233430109903' not in redacted
    assert 'REDACTED_CC' in redacted
    assert stats['credit_card'] == 2


def test_pii_phone():
    """Test phone number redaction"""
    service = RedactionService()
    
    text = 'Call: (555) 123-4567 or +1-555-987-6543'
    redacted, stats = service.redact(text)
    
    assert '555-123-4567' not in redacted or 'REDACTED_PHONE' in redacted
    assert stats.get('phone_number', 0) >= 1


def test_ip_address_optional():
    """Test that IP addresses are NOT redacted by default"""
    service = RedactionService(redact_ips=False)
    
    text = 'Server IP: 192.168.1.100'
    redacted, stats = service.redact(text)
    
    assert '192.168.1.100' in redacted  # Should NOT be redacted
    assert 'ip_address' not in stats


def test_ip_address_when_enabled():
    """Test IP address redaction when enabled"""
    service = RedactionService(redact_ips=True)
    
    text = 'Server IP: 192.168.1.100 and 10.0.0.1'
    redacted, stats = service.redact(text)
    
    assert '192.168.1.100' not in redacted
    assert '10.0.0.1' not in redacted
    assert 'REDACTED_IP' in redacted
    assert stats['ip_address'] == 2


def test_cloudwatch_log_events():
    """Test redaction of CloudWatch log format"""
    service = RedactionService()
    
    log_events = [
        {'timestamp': 1234567890, 'message': 'Login attempt for user@example.com with password=secret123'},
        {'timestamp': 1234567891, 'message': 'API call with token: Bearer abc123xyz'},
        {'timestamp': 1234567892, 'message': 'Normal log message without secrets'}
    ]
    
    redacted_events, stats = service.redact_log_events(log_events)
    
    assert len(redacted_events) == 3
    assert 'user@example.com' not in redacted_events[0]['message']
    assert 'secret123' not in redacted_events[0]['message']
    assert 'abc123xyz' not in redacted_events[1]['message']
    assert redacted_events[0]['redacted'] == True
    assert redacted_events[1]['redacted'] == True
    assert redacted_events[2]['redacted'] == False


def test_real_world_log_example():
    """Test with realistic CloudWatch error log"""
    service = RedactionService()
    
    log = """
    2025-12-28 10:30:45 ERROR: Database connection failed
    Connection string: postgresql://admin:P@ssw0rd123@db.example.com:5432/production
    API Key: sk_live_51HxK2L3M4N5O6P7Q8R9S
    User email: john.doe@company.com
    IP: 192.168.1.50
    JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature
    """
    
    redacted, stats = service.redact(log)
    
    # Verify all sensitive data is gone
    assert 'P@ssw0rd123' not in redacted
    assert 'admin' in redacted  # Username is OK, password is not
    assert 'sk_live_51HxK2L3M4N5O6P7Q8R9S' not in redacted
    assert 'john.doe@company.com' not in redacted
    assert '192.168.1.50' in redacted  # IPs not redacted by default
    assert 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9' not in redacted
    
    # Verify redaction placeholders exist
    assert 'REDACTED_CONNECTION_STRING' in redacted or 'REDACTED_PASSWORD' in redacted
    assert 'REDACTED_API_KEY' in redacted
    assert 'REDACTED_EMAIL' in redacted
    assert 'REDACTED_JWT' in redacted
    
    # Stats should show what was redacted
    assert stats['connection_string'] >= 1 or stats['password_pattern'] >= 1
    assert stats['api_key_pattern'] >= 1
    assert stats['email'] >= 1
    assert stats['jwt_token'] >= 1


def test_convenience_function():
    """Test the quick redact_text function"""
    text = "Password: secret123 and email: user@example.com"
    redacted = redact_text(text)
    
    assert 'secret123' not in redacted
    assert 'user@example.com' not in redacted
    assert 'REDACTED' in redacted


if __name__ == '__main__':
    # Run a quick manual test
    service = RedactionService()
    
    test_log = """
    ERROR: Authentication failed
    Username: admin
    Password: MySecretPass123!
    API Key: sk_test_FAKEKEYFORTEST123456789ABC
    Email: support@company.com
    """
    
    print("Original log:")
    print(test_log)
    print("\nRedacted log:")
    redacted, stats = service.redact(test_log)
    print(redacted)
    print("\nRedaction stats:")
    print(stats)
