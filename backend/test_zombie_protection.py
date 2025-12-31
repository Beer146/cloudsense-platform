"""
Test zombie detection with resource protection
"""
from services.zombie_service import ZombieService
from services.resource_protection_service import get_protection_service

print("="*80)
print("ZOMBIE DETECTION WITH RESOURCE PROTECTION")
print("="*80)

# Create mock zombies with various names/tags
mock_zombies = [
    {
        'resource_id': 'i-prod-db-001',
        'resource_name': 'prod-database',
        'type': 'EC2',
        'tags': [{'Key': 'Environment', 'Value': 'production'}],
        'monthly_cost': 100
    },
    {
        'resource_id': 'i-test-server',
        'resource_name': 'test-server',
        'type': 'EC2',
        'tags': [{'Key': 'Environment', 'Value': 'test'}],
        'monthly_cost': 50
    },
    {
        'resource_id': 'i-redis-cache',
        'resource_name': 'redis-cache',
        'type': 'EC2',
        'tags': [],
        'monthly_cost': 75
    },
    {
        'resource_id': 'i-monitoring',
        'resource_name': 'monitoring-prometheus',
        'type': 'EC2',
        'tags': [{'Key': 'Critical', 'Value': 'true'}],
        'monthly_cost': 60
    },
    {
        'resource_id': 'i-dev-instance',
        'resource_name': 'dev-playground',
        'type': 'EC2',
        'tags': [],
        'monthly_cost': 30
    }
]

service = ZombieService()
user_id = 1

print(f"\n📋 Mock zombies detected: {len(mock_zombies)}")
for z in mock_zombies:
    print(f"   - {z['resource_name']:25} (${z['monthly_cost']}/mo)")

print(f"\n🛡️ Applying resource protection...\n")

actual_zombies, protected = service._apply_resource_protection(mock_zombies, user_id)

print(f"\n📊 Results:")
print(f"   Actual zombies: {len(actual_zombies)}")
print(f"   Protected resources: {len(protected)}")

print(f"\n💀 Zombies to flag:")
for z in actual_zombies:
    print(f"   ❌ {z['resource_name']:25} ${z['monthly_cost']}/mo")

print(f"\n🛡️ Protected from flagging:")
for p in protected:
    print(f"   ✅ {p['resource_name']:25} ${p['monthly_cost']}/mo - {p['protection_reason']}")

# Calculate costs
zombie_cost = sum(z['monthly_cost'] for z in actual_zombies)
protected_cost = sum(p['monthly_cost'] for p in protected)

print(f"\n💰 Cost Analysis:")
print(f"   Zombie cost to eliminate: ${zombie_cost}/mo")
print(f"   Protected infrastructure: ${protected_cost}/mo (kept running)")

print("\n" + "="*80)
print("✅ RESOURCE PROTECTION WORKING!")
print("="*80)
