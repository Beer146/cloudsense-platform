"""
Cost Optimizer - Combines all recommendations and calculates total savings
"""


class CostOptimizer:
    def __init__(self, config):
        self.config = config
    
    def calculate_total_savings(self, ec2_recommendations, ri_recommendations):
        """Calculate total potential savings from all recommendations"""
        
        # EC2 right-sizing savings
        ec2_monthly_savings = sum(r['monthly_savings'] for r in ec2_recommendations)
        ec2_annual_savings = ec2_monthly_savings * 12
        
        # RI savings
        ri_monthly_savings = sum(r['monthly_savings'] for r in ri_recommendations)
        ri_annual_savings = sum(r['annual_savings'] for r in ri_recommendations)
        
        # Total
        total_monthly_savings = ec2_monthly_savings + ri_monthly_savings
        total_annual_savings = ec2_annual_savings + ri_annual_savings
        
        return {
            'ec2_rightsizing': {
                'count': len(ec2_recommendations),
                'monthly_savings': ec2_monthly_savings,
                'annual_savings': ec2_annual_savings
            },
            'reserved_instances': {
                'count': len(ri_recommendations),
                'monthly_savings': ri_monthly_savings,
                'annual_savings': ri_annual_savings
            },
            'total': {
                'monthly_savings': total_monthly_savings,
                'annual_savings': total_annual_savings
            }
        }
    
    def get_summary_stats(self, ec2_recommendations, ri_recommendations):
        """Get summary statistics"""
        
        stats = {
            'total_recommendations': len(ec2_recommendations) + len(ri_recommendations),
            'by_strategy': {},
            'by_region': {}
        }
        
        # Count by strategy
        for rec in ec2_recommendations:
            strategy = rec['strategy']
            if strategy not in stats['by_strategy']:
                stats['by_strategy'][strategy] = 0
            stats['by_strategy'][strategy] += 1
        
        if ri_recommendations:
            stats['by_strategy']['reserved_instances'] = len(ri_recommendations)
        
        # Count by region
        for rec in ec2_recommendations:
            region = rec['region']
            if region not in stats['by_region']:
                stats['by_region'][region] = 0
            stats['by_region'][region] += 1
        
        for rec in ri_recommendations:
            region = rec['region']
            if region not in stats['by_region']:
                stats['by_region'][region] = 0
            stats['by_region'][region] += len(rec['instances'])
        
        return stats