"""
Tests for LLM Output Validator
"""
from llm_output_validator import LLMOutputValidator, validate_llm_output


def test_valid_recommendation():
    """Test a valid, safe recommendation"""
    validator = LLMOutputValidator()
    
    rec = {
        'priority': 'HIGH',
        'title': 'Enable Multi-AZ for RDS',
        'description': 'Enable Multi-AZ deployment using: aws rds modify-db-instance --db-instance-identifier mydb --multi-az --apply-immediately',
        'aws_service': 'Amazon RDS',
        'documentation_link': 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html'
    }
    
    result = validator.validate_recommendation(rec)
    
    print("✅ Valid Recommendation Test:")
    print(f"   Severity: {result['severity']}")
    print(f"   Warnings: {result['warnings']}")
    assert result['severity'] == 'SAFE'
    assert result['is_valid'] == True


def test_dangerous_recommendation():
    """Test recommendation with dangerous operations"""
    validator = LLMOutputValidator()
    
    rec = {
        'priority': 'CRITICAL',
        'title': 'Fix Database',
        'description': 'Drop database and recreate it. Run: DROP TABLE users; then restore from backup.',
        'aws_service': 'Amazon RDS'
    }
    
    result = validator.validate_recommendation(rec)
    
    print("\n⚠️ Dangerous Recommendation Test:")
    print(f"   Severity: {result['severity']}")
    print(f"   Warnings: {result['warnings']}")
    assert result['severity'] == 'DANGEROUS'
    assert 'drop' in ' '.join(result['warnings']).lower()


def test_vague_recommendation():
    """Test vague, unhelpful recommendation"""
    validator = LLMOutputValidator()
    
    rec = {
        'priority': 'MEDIUM',
        'title': 'Fix the issue',
        'description': 'Just restart the server and see if it helps.',
        'aws_service': 'EC2'
    }
    
    result = validator.validate_recommendation(rec)
    
    print("\n🤔 Vague Recommendation Test:")
    print(f"   Severity: {result['severity']}")
    print(f"   Warnings: {result['warnings']}")
    assert result['severity'] == 'REQUIRES_REVIEW'


def test_full_analysis_validation():
    """Test complete analysis with multiple recommendations"""
    
    analysis = {
        'executive_summary': 'Critical database issue',
        'root_causes': [
            {
                'title': 'Connection Pool Exhaustion',
                'description': 'Database ran out of connections',
                'evidence': '15 connection timeout errors in logs'
            }
        ],
        'recommendations': [
            {
                'priority': 'CRITICAL',
                'title': 'Increase RDS max_connections',
                'description': 'Modify RDS parameter: aws rds modify-db-parameter-group --parameter-name max_connections --parameter-value 200',
                'aws_service': 'Amazon RDS',
                'documentation_link': 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithParamGroups.html'
            },
            {
                'priority': 'HIGH',
                'title': 'Delete everything',  # Dangerous!
                'description': 'Run: rm -rf /var/lib/mysql to clean up',
                'aws_service': 'EC2'
            }
        ]
    }
    
    result = validate_llm_output(analysis)
    
    print("\n📊 Full Analysis Validation:")
    print(f"   Overall Valid: {result['overall_valid']}")
    print(f"   Total Recommendations: {result['validation_summary']['total_recommendations']}")
    print(f"   Dangerous Operations: {result['validation_summary']['dangerous_operations']}")
    print(f"   Requires Review: {result['validation_summary']['requires_review']}")
    
    assert result['overall_valid'] == False  # Should be invalid due to dangerous op
    assert result['validation_summary']['dangerous_operations'] >= 1


if __name__ == '__main__':
    print("="*80)
    print("LLM OUTPUT VALIDATION TESTS")
    print("="*80)
    
    test_valid_recommendation()
    test_dangerous_recommendation()
    test_vague_recommendation()
    test_full_analysis_validation()
    
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED!")
    print("="*80)
