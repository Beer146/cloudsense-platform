"""
EC2 Recommender - Suggests right-sizing and instance family optimizations
"""


class EC2Recommender:
    def __init__(self, config):
        self.config = config
        self.cpu_threshold = config['ec2']['cpu_underutilized_threshold']
        self.min_savings = config['ec2']['min_savings_threshold']
        self.allowed_families = config['ec2']['allowed_families']
        
        # Instance type hierarchy for downsizing
        self.instance_sizes = ['nano', 'micro', 'small', 'medium', 'large', 'xlarge', '2xlarge', '4xlarge', '8xlarge']
        
        # Price mapping (simplified - in production, use AWS Pricing API)
        self.pricing = self._build_pricing_map()
    
    def generate_recommendations(self, analysis_results):
        """Generate right-sizing recommendations for EC2 instances"""
        print("💡 Generating EC2 recommendations...\n")
        
        recommendations = []
        
        for analysis in analysis_results:
            instance_id = analysis['instance_id']
            current_type = analysis['instance_type']
            cpu_metrics = analysis['metrics']['cpu_utilization']
            
            if not cpu_metrics:
                continue
            
            # Check if instance is underutilized
            avg_cpu = cpu_metrics['average']
            p95_cpu = cpu_metrics['p95']
            
            if p95_cpu < self.cpu_threshold:
                # Generate recommendations
                recs = self._find_better_instance_types(
                    analysis, current_type, p95_cpu
                )
                
                if recs:
                    recommendations.extend(recs)
        
        # Sort by potential savings
        recommendations.sort(key=lambda x: x['monthly_savings'], reverse=True)
        
        print(f"✅ Generated {len(recommendations)} recommendations\n")
        return recommendations
    
    def _find_better_instance_types(self, analysis, current_type, p95_cpu):
        """Find better instance types based on utilization"""
        recommendations = []
        current_cost = analysis['current_cost']
        
        # Parse current instance type
        parts = current_type.split('.')
        if len(parts) != 2:
            return recommendations
        
        current_family = parts[0]
        current_size = parts[1]
        
        # Strategy 1: Downsize within same family
        downsize_rec = self._recommend_downsize(
            analysis, current_family, current_size, current_cost, p95_cpu
        )
        if downsize_rec:
            recommendations.append(downsize_rec)
        
        # Strategy 2: Switch to cheaper family
        family_rec = self._recommend_family_switch(
            analysis, current_family, current_size, current_cost, p95_cpu
        )
        if family_rec:
            recommendations.append(family_rec)
        
        return recommendations
    
    def _recommend_downsize(self, analysis, family, current_size, current_cost, p95_cpu):
        """Recommend a smaller instance size in the same family"""
        if current_size not in self.instance_sizes:
            return None
        
        current_index = self.instance_sizes.index(current_size)
        
        # Can we go smaller?
        if current_index == 0:
            return None
        
        # Suggest one size smaller
        recommended_size = self.instance_sizes[current_index - 1]
        recommended_type = f"{family}.{recommended_size}"
        
        # Calculate savings
        recommended_cost = self.pricing.get(recommended_type, current_cost * 0.5)
        monthly_savings = current_cost - recommended_cost
        
        if monthly_savings < self.min_savings:
            return None
        
        return {
            'instance_id': analysis['instance_id'],
            'name': analysis['name'],
            'region': analysis['region'],
            'current_type': f"{family}.{current_size}",
            'recommended_type': recommended_type,
            'strategy': 'downsize',
            'reason': f'P95 CPU usage is {p95_cpu:.1f}%, can downsize safely',
            'current_monthly_cost': current_cost,
            'recommended_monthly_cost': recommended_cost,
            'monthly_savings': monthly_savings,
            'annual_savings': monthly_savings * 12,
            'cpu_utilization': {
                'average': analysis['metrics']['cpu_utilization']['average'],
                'p95': p95_cpu,
                'max': analysis['metrics']['cpu_utilization']['max']
            }
        }
    
    def _recommend_family_switch(self, analysis, current_family, current_size, current_cost, p95_cpu):
        """Recommend switching to a cheaper instance family"""
        # Only recommend switching from premium families to budget families
        premium_to_budget = {
            'm5': 'm5a',
            'c5': 'c5a',
            'r5': 'r5a',
            't3': 't3a'
        }
        
        if current_family not in premium_to_budget:
            return None
        
        budget_family = premium_to_budget[current_family]
        
        if budget_family not in self.allowed_families:
            return None
        
        recommended_type = f"{budget_family}.{current_size}"
        
        # AMD instances are typically 10% cheaper
        recommended_cost = current_cost * 0.90
        monthly_savings = current_cost - recommended_cost
        
        if monthly_savings < self.min_savings:
            return None
        
        return {
            'instance_id': analysis['instance_id'],
            'name': analysis['name'],
            'region': analysis['region'],
            'current_type': f"{current_family}.{current_size}",
            'recommended_type': recommended_type,
            'strategy': 'family_switch',
            'reason': f'Switch to AMD-based {budget_family} for same performance at lower cost',
            'current_monthly_cost': current_cost,
            'recommended_monthly_cost': recommended_cost,
            'monthly_savings': monthly_savings,
            'annual_savings': monthly_savings * 12,
            'cpu_utilization': {
                'average': analysis['metrics']['cpu_utilization']['average'],
                'p95': p95_cpu,
                'max': analysis['metrics']['cpu_utilization']['max']
            }
        }
    
    def _build_pricing_map(self):
        """Build simplified pricing map (in production, use AWS Pricing API)"""
        return {
            # T3 family
            't3.nano': 0.0052 * 730,
            't3.micro': 0.0104 * 730,
            't3.small': 0.0208 * 730,
            't3.medium': 0.0416 * 730,
            't3.large': 0.0832 * 730,
            't3.xlarge': 0.1664 * 730,
            't3.2xlarge': 0.3328 * 730,
            
            # T3a family (AMD)
            't3a.nano': 0.0047 * 730,
            't3a.micro': 0.0094 * 730,
            't3a.small': 0.0188 * 730,
            't3a.medium': 0.0376 * 730,
            't3a.large': 0.0752 * 730,
            't3a.xlarge': 0.1504 * 730,
            't3a.2xlarge': 0.3008 * 730,
            
            # M5 family
            'm5.large': 0.096 * 730,
            'm5.xlarge': 0.192 * 730,
            'm5.2xlarge': 0.384 * 730,
            'm5.4xlarge': 0.768 * 730,
            
            # M5a family (AMD)
            'm5a.large': 0.086 * 730,
            'm5a.xlarge': 0.172 * 730,
            'm5a.2xlarge': 0.344 * 730,
            'm5a.4xlarge': 0.688 * 730,
            
            # C5 family
            'c5.large': 0.085 * 730,
            'c5.xlarge': 0.17 * 730,
            'c5.2xlarge': 0.34 * 730,
            'c5.4xlarge': 0.68 * 730,
            
            # C5a family (AMD)
            'c5a.large': 0.077 * 730,
            'c5a.xlarge': 0.154 * 730,
            'c5a.2xlarge': 0.308 * 730,
            'c5a.4xlarge': 0.616 * 730,
            
            # R5 family
            'r5.large': 0.126 * 730,
            'r5.xlarge': 0.252 * 730,
            'r5.2xlarge': 0.504 * 730,
            
            # R5a family (AMD)
            'r5a.large': 0.113 * 730,
            'r5a.xlarge': 0.226 * 730,
            'r5a.2xlarge': 0.452 * 730,
        }