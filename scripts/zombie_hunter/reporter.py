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
    
    def generate_report(self, zombies, cost_summary, stats):
        """Generate report in specified format"""
        report_format = self.config['reporting']['format']
        
        if report_format == 'console':
            self._print_console_report(zombies, cost_summary, stats)
        elif report_format == 'json':
            self._generate_json_report(zombies, cost_summary, stats)
        elif report_format == 'csv':
            self._generate_csv_report(zombies)
        elif report_format == 'html':
            self._generate_html_report(zombies, cost_summary, stats)
        
        # Save to file if configured
        if self.config['reporting']['save_to_file']:
            self._save_reports(zombies, cost_summary, stats)
    
    def _print_console_report(self, zombies, cost_summary, stats):
        """Print report to console"""
        print("\n" + "="*80)
        print("🧟 ZOMBIE RESOURCE HUNTER - SCAN RESULTS")
        print("="*80)
        
        # Summary
        print(f"\n📊 SUMMARY")
        print(f"   Total Zombie Resources: {stats['total_zombies']}")
        print(f"   Potential Monthly Savings: ${cost_summary['total_monthly_savings']:.2f}")
        print(f"   Potential Annual Savings: ${cost_summary['total_annual_savings']:.2f}")
        
        # By resource type
        print(f"\n📦 BY RESOURCE TYPE")
        for resource_type, count in stats['by_type'].items():
            cost = cost_summary['cost_by_type'].get(resource_type, 0)
            print(f"   {resource_type}: {count} resources (${cost:.2f}/month)")
        
        # By region
        print(f"\n🌍 BY REGION")
        for region, count in stats['by_region'].items():
            print(f"   {region}: {count} resources")
        
        # Detailed findings
        if zombies:
            print(f"\n🔍 DETAILED FINDINGS\n")
            
            # Group by type
            by_type = {}
            for zombie in zombies:
                resource_type = zombie['resource_type']
                if resource_type not in by_type:
                    by_type[resource_type] = []
                by_type[resource_type].append(zombie)
            
            for resource_type, resources in by_type.items():
                print(f"\n{resource_type} Resources ({len(resources)}):")
                print("-" * 80)
                
                # Prepare table data
                headers = ['Resource ID', 'Name', 'Region', 'Status', 'Reason', 'Monthly Cost']
                rows = []
                
                for r in resources:
                    rows.append([
                        r['resource_id'][:30],
                        r['name'][:20],
                        r['region'],
                        r['status'],
                        r['reason'][:40],
                        f"${r.get('estimated_monthly_cost', 0):.2f}"
                    ])
                
                print(tabulate(rows, headers=headers, tablefmt='grid'))
        
        print("\n" + "="*80)
        print(f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
    
    def _generate_json_report(self, zombies, cost_summary, stats):
        """Generate JSON report"""
        report = {
            'scan_time': datetime.now().isoformat(),
            'summary': {
                'total_zombies': stats['total_zombies'],
                'cost_summary': cost_summary,
                'stats': stats
            },
            'zombies': zombies
        }
        
        print(json.dumps(report, indent=2, default=str))
    
    def _generate_csv_report(self, zombies):
        """Generate CSV report"""
        if not zombies:
            print("No zombies found, skipping CSV generation")
            return
        
        # Get all unique keys
        all_keys = set()
        for zombie in zombies:
            all_keys.update(zombie.keys())
        
        headers = sorted(list(all_keys))
        
        # Print to console (in real scenario, this would write to file)
        print(','.join(headers))
        for zombie in zombies:
            row = [str(zombie.get(key, '')) for key in headers]
            print(','.join(row))
    
    def _generate_html_report(self, zombies, cost_summary, stats):
        """Generate HTML report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Zombie Resource Hunter Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .summary {{ background: #f0f0f0; padding: 15px; margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>🧟 Zombie Resource Hunter Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Zombie Resources: {stats['total_zombies']}</p>
                <p>Potential Monthly Savings: ${cost_summary['total_monthly_savings']:.2f}</p>
                <p>Potential Annual Savings: ${cost_summary['total_annual_savings']:.2f}</p>
            </div>
            
            <h2>Detailed Findings</h2>
            <table>
                <tr>
                    <th>Type</th>
                    <th>Resource ID</th>
                    <th>Name</th>
                    <th>Region</th>
                    <th>Status</th>
                    <th>Reason</th>
                    <th>Monthly Cost</th>
                </tr>
        """
        
        for zombie in zombies:
            html += f"""
                <tr>
                    <td>{zombie['resource_type']}</td>
                    <td>{zombie['resource_id']}</td>
                    <td>{zombie['name']}</td>
                    <td>{zombie['region']}</td>
                    <td>{zombie['status']}</td>
                    <td>{zombie['reason']}</td>
                    <td>${zombie.get('estimated_monthly_cost', 0):.2f}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        print(html)
    
    def _save_reports(self, zombies, cost_summary, stats):
        """Save reports to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON
        json_file = os.path.join(self.output_dir, f'scan_results_{timestamp}.json')
        with open(json_file, 'w') as f:
            report = {
                'scan_time': datetime.now().isoformat(),
                'summary': {
                    'total_zombies': stats['total_zombies'],
                    'cost_summary': cost_summary,
                    'stats': stats
                },
                'zombies': zombies
            }
            json.dump(report, f, indent=2, default=str)
        print(f"✅ JSON report saved to: {json_file}")
        
        # Save CSV
        if zombies:
            csv_file = os.path.join(self.output_dir, f'scan_results_{timestamp}.csv')
            all_keys = set()
            for zombie in zombies:
                all_keys.update(zombie.keys())
            headers = sorted(list(all_keys))
            
            with open(csv_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(zombies)
            print(f"✅ CSV report saved to: {csv_file}")