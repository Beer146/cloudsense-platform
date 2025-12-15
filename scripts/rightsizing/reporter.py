"""
Reporter - Generates reports in various formats
"""

import json
import csv
from datetime import datetime
from tabulate import tabulate
import os


class Reporter:
    def __init__(self, config):
        self.config = config
        self.output_dir = config['reporting']['output_dir']
        
        # Create output directory if it doesn't exist
        if config['reporting']['save_to_file']:
            os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_report(self, ec2_recs, ri_recs, savings_summary, stats):
        """Generate report in specified format"""
        report_format = self.config['reporting']['format']
        
        if report_format == 'console':
            self._print_console_report(ec2_recs, ri_recs, savings_summary, stats)
        elif report_format == 'json':
            self._generate_json_report(ec2_recs, ri_recs, savings_summary, stats)
        elif report_format == 'csv':
            self._generate_csv_report(ec2_recs, ri_recs)
        elif report_format == 'html':
            self._generate_html_report(ec2_recs, ri_recs, savings_summary, stats)
        
        # Save to file if configured
        if self.config['reporting']['save_to_file']:
            self._save_reports(ec2_recs, ri_recs, savings_summary, stats)
    
    def _print_console_report(self, ec2_recs, ri_recs, savings_summary, stats):
        """Print report to console"""
        print("\n" + "="*100)
        print("💰 RIGHT-SIZING RECOMMENDATION ENGINE - ANALYSIS RESULTS")
        print("="*100)
        
        # Summary
        print(f"\n📊 EXECUTIVE SUMMARY")
        print(f"   Total Recommendations: {stats['total_recommendations']}")
        print(f"   Potential Monthly Savings: ${savings_summary['total']['monthly_savings']:.2f}")
        print(f"   Potential Annual Savings: ${savings_summary['total']['annual_savings']:.2f}")
        
        # Breakdown
        print(f"\n💡 SAVINGS BREAKDOWN")
        ec2_savings = savings_summary['ec2_rightsizing']
        print(f"   EC2 Right-Sizing: {ec2_savings['count']} recommendations → ${ec2_savings['annual_savings']:.2f}/year")
        
        ri_savings = savings_summary['reserved_instances']
        print(f"   Reserved Instances: {ri_savings['count']} recommendations → ${ri_savings['annual_savings']:.2f}/year")
        
        # By strategy
        print(f"\n📈 BY STRATEGY")
        for strategy, count in stats['by_strategy'].items():
            print(f"   {strategy.replace('_', ' ').title()}: {count} recommendations")
        
        # By region
        print(f"\n🌍 BY REGION")
        for region, count in stats['by_region'].items():
            print(f"   {region}: {count} instances")
        
        # EC2 Right-Sizing Details
        if ec2_recs:
            print(f"\n🔧 EC2 RIGHT-SIZING RECOMMENDATIONS ({len(ec2_recs)} total)\n")
            
            # Group by strategy
            downsize_recs = [r for r in ec2_recs if r['strategy'] == 'downsize']
            family_recs = [r for r in ec2_recs if r['strategy'] == 'family_switch']
            
            if downsize_recs:
                print("   DOWNSIZE RECOMMENDATIONS:")
                print("-" * 100)
                headers = ['Instance ID', 'Name', 'Current', 'Recommended', 'CPU P95', 'Monthly Savings']
                rows = []
                
                for r in downsize_recs[:10]:  # Top 10
                    rows.append([
                        r['instance_id'][:19],
                        r['name'][:15],
                        r['current_type'],
                        r['recommended_type'],
                        f"{r['cpu_utilization']['p95']:.1f}%",
                        f"${r['monthly_savings']:.2f}"
                    ])
                
                print(tabulate(rows, headers=headers, tablefmt='grid'))
                if len(downsize_recs) > 10:
                    print(f"   ... and {len(downsize_recs) - 10} more")
                print()
            
            if family_recs:
                print("   FAMILY SWITCH RECOMMENDATIONS (Intel → AMD):")
                print("-" * 100)
                headers = ['Instance ID', 'Name', 'Current', 'Recommended', 'Monthly Savings']
                rows = []
                
                for r in family_recs[:10]:  # Top 10
                    rows.append([
                        r['instance_id'][:19],
                        r['name'][:15],
                        r['current_type'],
                        r['recommended_type'],
                        f"${r['monthly_savings']:.2f}"
                    ])
                
                print(tabulate(rows, headers=headers, tablefmt='grid'))
                if len(family_recs) > 10:
                    print(f"   ... and {len(family_recs) - 10} more")
                print()
        
        # Reserved Instance Recommendations
        if ri_recs:
            print(f"\n💳 RESERVED INSTANCE RECOMMENDATIONS ({len(ri_recs)} total)\n")
            print("-" * 100)
            
            headers = ['Region', 'Instance Type', 'Count', 'Term', 'Annual Savings', 'Upfront Payment']
            rows = []
            
            for r in ri_recs[:10]:  # Top 10
                rows.append([
                    r['region'],
                    r['instance_type'],
                    r['instance_count'],
                    f"{r['term_years']} year",
                    f"${r['annual_savings']:.2f}",
                    f"${r['upfront_payment']:.2f}"
                ])
            
            print(tabulate(rows, headers=headers, tablefmt='grid'))
            if len(ri_recs) > 10:
                print(f"   ... and {len(ri_recs) - 10} more")
        
        print("\n" + "="*100)
        print(f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*100 + "\n")
    
    def _generate_json_report(self, ec2_recs, ri_recs, savings_summary, stats):
        """Generate JSON report"""
        report = {
            'scan_time': datetime.now().isoformat(),
            'summary': {
                'total_recommendations': stats['total_recommendations'],
                'savings': savings_summary,
                'stats': stats
            },
            'ec2_recommendations': ec2_recs,
            'ri_recommendations': ri_recs
        }
        
        print(json.dumps(report, indent=2, default=str))
    
    def _generate_csv_report(self, ec2_recs, ri_recs):
        """Generate CSV report"""
        # EC2 recommendations
        if ec2_recs:
            print("EC2 Recommendations:")
            headers = ['instance_id', 'name', 'region', 'current_type', 'recommended_type', 
                      'strategy', 'monthly_savings', 'annual_savings']
            print(','.join(headers))
            
            for rec in ec2_recs:
                row = [
                    rec['instance_id'],
                    rec['name'],
                    rec['region'],
                    rec['current_type'],
                    rec['recommended_type'],
                    rec['strategy'],
                    f"{rec['monthly_savings']:.2f}",
                    f"{rec['annual_savings']:.2f}"
                ]
                print(','.join(str(x) for x in row))
    
    def _generate_html_report(self, ec2_recs, ri_recs, savings_summary, stats):
        """Generate HTML report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Right-Sizing Recommendations</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .summary {{ background: #f0f0f0; padding: 15px; margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .savings {{ color: green; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>💰 Right-Sizing Recommendation Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <p>Total Recommendations: {stats['total_recommendations']}</p>
                <p class="savings">Potential Annual Savings: ${savings_summary['total']['annual_savings']:.2f}</p>
            </div>
            
            <h2>EC2 Right-Sizing Recommendations</h2>
            <table>
                <tr>
                    <th>Instance ID</th>
                    <th>Current Type</th>
                    <th>Recommended Type</th>
                    <th>Strategy</th>
                    <th>Monthly Savings</th>
                </tr>
        """
        
        for rec in ec2_recs:
            html += f"""
                <tr>
                    <td>{rec['instance_id']}</td>
                    <td>{rec['current_type']}</td>
                    <td>{rec['recommended_type']}</td>
                    <td>{rec['strategy']}</td>
                    <td class="savings">${rec['monthly_savings']:.2f}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        print(html)
    
    def _save_reports(self, ec2_recs, ri_recs, savings_summary, stats):
        """Save reports to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON
        json_file = os.path.join(self.output_dir, f'rightsizing_report_{timestamp}.json')
        with open(json_file, 'w') as f:
            report = {
                'scan_time': datetime.now().isoformat(),
                'summary': {
                    'total_recommendations': stats['total_recommendations'],
                    'savings': savings_summary,
                    'stats': stats
                },
                'ec2_recommendations': ec2_recs,
                'ri_recommendations': ri_recs
            }
            json.dump(report, f, indent=2, default=str)
        print(f"✅ JSON report saved to: {json_file}")
        
        # Save CSV
        csv_file = os.path.join(self.output_dir, f'rightsizing_report_{timestamp}.csv')
        with open(csv_file, 'w', newline='') as f:
            if ec2_recs:
                headers = ['instance_id', 'name', 'region', 'current_type', 'recommended_type', 
                          'strategy', 'monthly_savings', 'annual_savings']
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(ec2_recs)
        print(f"✅ CSV report saved to: {csv_file}")