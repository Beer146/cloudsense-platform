"""
Tests for Resource Protection Service
"""
from resource_protection_service import ResourceProtectionService


def test_tag_based_protection():
    """Test protection via tags"""
    service = ResourceProtectionService()
    
    # Production environment tag
    tags = [
        {'Key': 'Environment', 'Value': 'production'},
        {'Key': 'Name', 'Value': 'web-server'}
    ]
    
    is_protected, reason = service.is_protected(
        resource_id='i-1234567890',
        resource_name='web-server',
        tags=tags
    )
    
    assert is_protected == True
    assert 'Environment=production' in reason
    
    print("✅ Tag-based protection test passed")
    print(f"   Reason: {reason}")


def test_name_pattern_protection():
    """Test protection via name patterns"""
    service = ResourceProtectionService()
    
    test_cases = [
        ('prod-database', True),
        ('production-api', True),
        ('api-prod', True),
        ('redis-cache', True),
        ('monitoring-server', True),
        ('test-server', False),
        ('dev-instance', False)
    ]
    
    for name, should_protect in test_cases:
        is_protected, reason = service.is_protected(
            resource_id=f'i-{name}',
            resource_name=name
        )
        
        if should_protect:
            assert is_protected == True, f"{name} should be protected"
            print(f"✅ {name:20} → PROTECTED ({reason})")
        else:
            assert is_protected == False, f"{name} should NOT be protected"
            print(f"❌ {name:20} → Not protected (correct)")


def test_user_exclusions():
    """Test user-defined exclusions"""
    service = ResourceProtectionService()
    
    user_id = 1
    resource_id = 'i-test123'
    
    # Initially not protected
    is_protected, _ = service.is_protected(
        resource_id=resource_id,
        user_id=user_id
    )
    assert is_protected == False
    
    # Mark as false positive
    service.mark_as_false_positive(
        user_id=user_id,
        resource_id=resource_id,
        resource_name='test-instance',
        reason='This is my development server that runs 24/7'
    )
    
    # Now protected
    is_protected, reason = service.is_protected(
        resource_id=resource_id,
        user_id=user_id
    )
    assert is_protected == True
    assert 'User-marked' in reason
    
    print("✅ User exclusion test passed")
    print(f"   Reason: {reason}")


def test_critical_tag():
    """Test Critical=true tag"""
    service = ResourceProtectionService()
    
    tags = [{'Key': 'Critical', 'Value': 'true'}]
    
    is_protected, reason = service.is_protected(
        resource_id='i-critical',
        tags=tags
    )
    
    assert is_protected == True
    assert 'Critical=true' in reason
    
    print("✅ Critical tag test passed")


def test_stats():
    """Test protection statistics"""
    service = ResourceProtectionService()
    
    # Add some exclusions
    service.mark_as_false_positive(1, 'i-test1', 'test1')
    service.mark_as_false_positive(1, 'i-test2', 'test2')
    service.mark_as_false_positive(2, 'i-test3', 'test3')
    
    stats = service.get_protection_stats()
    
    assert stats['total_user_exclusions'] == 3
    assert stats['users_with_exclusions'] == 2
    
    print("✅ Stats test passed")
    print(f"   Stats: {stats}")


if __name__ == '__main__':
    print("="*80)
    print("RESOURCE PROTECTION TESTS")
    print("="*80)
    
    test_tag_based_protection()
    print()
    test_name_pattern_protection()
    print()
    test_user_exclusions()
    print()
    test_critical_tag()
    print()
    test_stats()
    
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED!")
    print("="*80)
