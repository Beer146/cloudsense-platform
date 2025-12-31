"""
Resource Protection Service
Prevents false positives by protecting always-on and critical resources
"""
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class ResourceProtectionService:
    """
    Protects critical resources from being flagged as zombies
    
    Protection criteria:
    1. Tag-based (Environment=production, Critical=true, etc.)
    2. Name pattern matching (prod-*, *-cache, etc.)
    3. User-defined exclusions (false positive feedback)
    """
    
    # Protected tag patterns
    PROTECTED_TAGS = {
        'Environment': ['production', 'prod', 'live'],
        'Critical': ['true', 'yes', '1'],
        'AlwaysOn': ['true', 'yes', '1'],
        'Protected': ['true', 'yes', '1'],
        'Tier': ['production', 'critical']
    }
    
    # Protected name patterns (regex)
    PROTECTED_NAME_PATTERNS = [
        r'prod[-_]',           # prod-database, prod_api
        r'production[-_]',     # production-db
        r'[-_]prod$',          # api-prod, service_prod
        r'[-_]production$',    # db-production
        r'cache',              # Any cache (redis, memcached)
        r'database',           # Database servers
        r'db[-_]',            # db-master, db_replica
        r'master',             # Master nodes
        r'primary',            # Primary instances
        r'monitoring',         # Monitoring infrastructure
        r'prometheus',         # Prometheus
        r'grafana',            # Grafana
        r'elasticsearch',      # Elasticsearch
        r'kibana',             # Kibana
        r'backup',             # Backup systems
    ]
    
    def __init__(self):
        # User-defined exclusions (in production, store in database)
        self.user_exclusions = {}  # {user_id: [resource_ids]}
        
        print("✅ Resource Protection Service initialized")
        print(f"   Protected tag keys: {list(self.PROTECTED_TAGS.keys())}")
        print(f"   Protected name patterns: {len(self.PROTECTED_NAME_PATTERNS)}")
    
    def is_protected(
        self,
        resource_id: str,
        resource_name: Optional[str] = None,
        tags: Optional[List[Dict[str, str]]] = None,
        user_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a resource is protected from zombie detection
        
        Args:
            resource_id: Resource ID (e.g., i-1234567890abcdef)
            resource_name: Resource name tag
            tags: List of tag dicts [{'Key': 'Environment', 'Value': 'production'}]
            user_id: User ID for user-specific exclusions
            
        Returns:
            (is_protected: bool, reason: Optional[str])
        """
        
        # Check 1: User-defined exclusions (highest priority)
        if user_id and resource_id in self.user_exclusions.get(user_id, []):
            return True, "User-marked as protected (false positive feedback)"
        
        # Check 2: Tag-based protection
        if tags:
            for tag in tags:
                tag_key = tag.get('Key', '')
                tag_value = tag.get('Value', '').lower()
                
                if tag_key in self.PROTECTED_TAGS:
                    protected_values = self.PROTECTED_TAGS[tag_key]
                    if tag_value in protected_values:
                        return True, f"Protected by tag: {tag_key}={tag.get('Value')}"
        
        # Check 3: Name pattern matching
        if resource_name:
            name_lower = resource_name.lower()
            
            for pattern in self.PROTECTED_NAME_PATTERNS:
                if re.search(pattern, name_lower):
                    return True, f"Protected by name pattern: matches '{pattern}'"
        
        # Not protected
        return False, None
    
    def mark_as_false_positive(
        self,
        user_id: int,
        resource_id: str,
        resource_name: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """
        Mark a resource as a false positive (user feedback)
        
        Args:
            user_id: User ID
            resource_id: Resource that was incorrectly flagged
            resource_name: Resource name (for logging)
            reason: User's reason for marking as false positive
        """
        if user_id not in self.user_exclusions:
            self.user_exclusions[user_id] = []
        
        if resource_id not in self.user_exclusions[user_id]:
            self.user_exclusions[user_id].append(resource_id)
            
            print(f"✅ Resource marked as protected:")
            print(f"   User: {user_id}")
            print(f"   Resource: {resource_id} ({resource_name})")
            print(f"   Reason: {reason or 'No reason provided'}")
    
    def get_user_exclusions(self, user_id: int) -> List[str]:
        """Get list of resources excluded by user"""
        return self.user_exclusions.get(user_id, [])
    
    def remove_exclusion(self, user_id: int, resource_id: str):
        """Remove a resource from user exclusions"""
        if user_id in self.user_exclusions:
            if resource_id in self.user_exclusions[user_id]:
                self.user_exclusions[user_id].remove(resource_id)
                print(f"✅ Removed exclusion: {resource_id} for user {user_id}")
    
    def get_protection_stats(self) -> Dict:
        """Get statistics about protections"""
        total_exclusions = sum(len(exclusions) for exclusions in self.user_exclusions.values())
        
        return {
            'total_user_exclusions': total_exclusions,
            'users_with_exclusions': len(self.user_exclusions),
            'protected_tag_patterns': len(self.PROTECTED_TAGS),
            'protected_name_patterns': len(self.PROTECTED_NAME_PATTERNS)
        }


# Global instance (singleton)
_protection_service = None

def get_protection_service() -> ResourceProtectionService:
    """Get or create the global protection service instance"""
    global _protection_service
    if _protection_service is None:
        _protection_service = ResourceProtectionService()
    return _protection_service
