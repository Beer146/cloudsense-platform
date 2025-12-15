"""
Cost Calculator - Estimates potential savings from cleaning up zombie resources
"""


class CostCalculator:
    def __init__(self):
        pass
    
    def calculate_total_savings(self, all_zombies):
        """Calculate total potential monthly savings"""
        total_cost = 0
        cost_by_type = {}
        
        for zombie in all_zombies:
            resource_type = zombie['resource_type']
            cost = zombie.get('estimated_monthly_cost', 0)
            
            total_cost += cost
            
            if resource_type not in cost_by_type:
                cost_by_type[resource_type] = 0
            cost_by_type[resource_type] += cost
        
        return {
            'total_monthly_savings': total_cost,
            'total_annual_savings': total_cost * 12,
            'cost_by_type': cost_by_type,
            'resource_count': len(all_zombies)
        }
    
    def get_summary_stats(self, all_zombies):
        """Get summary statistics about zombie resources"""
        stats = {
            'total_zombies': len(all_zombies),
            'by_type': {},
            'by_region': {},
            'by_status': {}
        }
        
        for zombie in all_zombies:
            resource_type = zombie['resource_type']
            region = zombie['region']
            status = zombie['status']
            
            # Count by type
            if resource_type not in stats['by_type']:
                stats['by_type'][resource_type] = 0
            stats['by_type'][resource_type] += 1
            
            # Count by region
            if region not in stats['by_region']:
                stats['by_region'][region] = 0
            stats['by_region'][region] += 1
            
            # Count by status
            if status not in stats['by_status']:
                stats['by_status'][status] = 0
            stats['by_status'][status] += 1
        
        return stats