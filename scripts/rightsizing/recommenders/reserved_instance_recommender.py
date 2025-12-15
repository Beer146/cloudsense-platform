"""
Reserved Instance Recommender - Suggests RI purchases based on usage patterns
"""

from collections import defaultdict


class ReservedInstanceRecommender:
    def __init__(self, config):
        self.config = config
        self.min_utilization = config['reserved_instances']['min_utilization']
        self.term_years = config['reserved_instances']['term_years']
        self.payment_option = config['reserved_instances']['payment_option']
        
        # RI discount rates (simplified)
        self.discount_rates = {
            1: {  # 1-year term
                'all_upfront': 0.40,      # 40% discount
                'partial_upfront': 0.35,   # 35% discount
                'no_upfront': 0.30         # 30% discount
            },
            3: {  # 3-year term
                'all_upfront': 0.60,      # 60% discount
                'partial_upfront': 0.55,   # 55% discount
                'no_upfront': 0.50         # 50% discount
            }
        }
    
    def generate_recommendations(self, analysis_results):
        """Generate Reserved Instance purchase recommendations"""
        print("💡 Generating Reserved Instance recommendations...\n")
        
        # Group instances by type and region
        instance_groups = self._group_instances(analysis_results)
        
        recommendations = []
        
        for key, instances in instance_groups.items():
            region, instance_type = key
            count = len(instances)
            
            # Only recommend RI if we have consistent usage
            if count > 0:
                rec = self._create_ri_recommendation(
                    region, instance_type, instances
                )
                if rec:
                    recommendations.append(rec)
        
        # Sort by potential savings
        recommendations.sort(key=lambda x: x['annual_savings'], reverse=True)
        
        print(f"✅ Generated {len(recommendations)} RI recommendations\n")
        return recommendations
    
    def _group_instances(self, analysis_results):
        """Group instances by type and region"""
        groups = defaultdict(list)
        
        for analysis in analysis_results:
            key = (analysis['region'], analysis['instance_type'])
            groups[key].append(analysis)
        
        return groups
    
    def _create_ri_recommendation(self, region, instance_type, instances):
        """Create RI recommendation for a group of instances"""
        count = len(instances)
        
        # Calculate average monthly cost
        total_monthly_cost = sum(inst['current_cost'] for inst in instances)
        
        # Calculate RI discount
        discount_rate = self.discount_rates[self.term_years][self.payment_option]
        
        # RI monthly cost (after discount)
        ri_monthly_cost = total_monthly_cost * (1 - discount_rate)
        
        # Calculate savings
        monthly_savings = total_monthly_cost - ri_monthly_cost
        annual_savings = monthly_savings * 12
        total_savings = annual_savings * self.term_years
        
        # Calculate upfront payment
        upfront_payment = self._calculate_upfront_payment(
            total_monthly_cost, discount_rate
        )
        
        return {
            'region': region,
            'instance_type': instance_type,
            'instance_count': count,
            'term_years': self.term_years,
            'payment_option': self.payment_option,
            'current_monthly_cost': total_monthly_cost,
            'ri_monthly_cost': ri_monthly_cost,
            'monthly_savings': monthly_savings,
            'annual_savings': annual_savings,
            'total_savings_over_term': total_savings,
            'upfront_payment': upfront_payment,
            'discount_rate': discount_rate * 100,
            'instances': [
                {
                    'instance_id': inst['instance_id'],
                    'name': inst['name']
                }
                for inst in instances
            ]
        }
    
    def _calculate_upfront_payment(self, monthly_cost, discount_rate):
        """Calculate upfront payment based on payment option"""
        annual_cost = monthly_cost * 12
        term_cost = annual_cost * self.term_years
        ri_term_cost = term_cost * (1 - discount_rate)
        
        if self.payment_option == 'all_upfront':
            return ri_term_cost
        elif self.payment_option == 'partial_upfront':
            return ri_term_cost * 0.5  # 50% upfront
        else:  # no_upfront
            return 0