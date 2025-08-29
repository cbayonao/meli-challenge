#!/usr/bin/env python3
"""
Command-line interface for AI validation system
Allows validation of scraped data files and individual items
"""

import argparse
import json
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import os

from .ai_validator import AIValidator, ValidationReport, ValidationStatus


class ValidationCLI:
    """Command-line interface for AI validation system"""
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('validation_cli.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def parse_arguments(self) -> argparse.Namespace:
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description='AI-powered data validation for Meli Challenge',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
            Examples:
            # Validate a single JSON file
            python validation_cli.py validate-file data.json --model gpt-3.5-turbo
            
            # Validate multiple files in batch
            python validation_cli.py validate-batch data/ --batch-size 20
            
            # Validate individual item
            python validation_cli.py validate-item '{"title": "test"}'
            
            # Generate validation report
            python validation_cli.py generate-report validation_reports/ --output summary.html
            """
        )
        
        # Global options
        parser.add_argument(
            '--model', '-m',
            default='gpt-3.5-turbo',
            help='OpenAI model to use (default: gpt-3.5-turbo)'
        )

        parser.add_argument(
            '--api-key',
            help='API key for AI provider (or set environment variable)'
        )
        parser.add_argument(
            '--batch-size', '-b',
            type=int,
            default=10,
            help='Batch size for processing (default: 10)'
        )
        parser.add_argument(
            '--output-dir', '-o',
            default='validation_reports',
            help='Output directory for reports (default: validation_reports)'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'csv', 'html'],
            default='json',
            help='Output format for reports (default: json)'
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose logging'
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Validate file command
        file_parser = subparsers.add_parser('validate-file', help='Validate a single JSON file')
        file_parser.add_argument('file_path', help='Path to JSON file to validate')
        file_parser.add_argument('--save-report', action='store_true', help='Save validation report')
        
        # Validate batch command
        batch_parser = subparsers.add_parser('validate-batch', help='Validate multiple files in batch')
        batch_parser.add_argument('input_dir', help='Directory containing JSON files to validate')
        batch_parser.add_argument('--pattern', default='*.json', help='File pattern to match (default: *.json)')
        batch_parser.add_argument('--recursive', '-r', action='store_true', help='Process subdirectories recursively')
        
        # Validate item command
        item_parser = subparsers.add_parser('validate-item', help='Validate a single JSON item')
        item_parser.add_argument('item_json', help='JSON string or file path containing item data')
        
        # Generate report command
        report_parser = subparsers.add_parser('generate-report', help='Generate summary report from validation results')
        report_parser.add_argument('input_dir', help='Directory containing validation reports')
        report_parser.add_argument('--output', help='Output file for summary report')
        
        # Test command
        test_parser = subparsers.add_parser('test', help='Test AI provider connection')
        test_parser.add_argument('--test-item', help='Test item JSON for validation')
        
        return parser.parse_args()
    
    def run(self):
        """Main entry point"""
        args = self.parse_arguments()
        
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        if not args.command:
            self.logger.error("No command specified. Use --help for usage information.")
            sys.exit(1)
        
        try:
            if args.command == 'validate-file':
                self.validate_file(args)
            elif args.command == 'validate-batch':
                self.validate_batch(args)
            elif args.command == 'validate-item':
                self.validate_item(args)
            elif args.command == 'generate-report':
                self.generate_report(args)
            elif args.command == 'test':
                self.test_provider(args)
            else:
                self.logger.error(f"Unknown command: {args.command}")
                sys.exit(1)
                
        except Exception as e:
            self.logger.error(f"Command failed: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def validate_file(self, args):
        """Validate a single JSON file"""
        file_path = Path(args.file_path)
        
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            sys.exit(1)
        
        self.logger.info(f"Validating file: {file_path}")
        
        # Load data
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in file: {e}")
            sys.exit(1)
        
        # Initialize validator
        validator = self._create_validator(args)
        
        # Validate data
        if isinstance(data, list):
            self.logger.info(f"Processing {len(data)} items from file")
            reports = asyncio.run(validator.validate_batch(data))
        else:
            self.logger.info("Processing single item from file")
            reports = [asyncio.run(validator.validate_item(data))]
        
        # Display results
        self._display_validation_results(reports)
        
        # Save reports if requested
        if args.save_report:
            self._save_reports(reports, args.output_dir, args.format)
    
    def validate_batch(self, args):
        """Validate multiple files in batch"""
        input_dir = Path(args.input_dir)
        
        if not input_dir.exists() or not input_dir.is_dir():
            self.logger.error(f"Directory not found: {input_dir}")
            sys.exit(1)
        
        # Find JSON files
        if args.recursive:
            json_files = list(input_dir.rglob(args.pattern))
        else:
            json_files = list(input_dir.glob(args.pattern))
        
        if not json_files:
            self.logger.warning(f"No files found matching pattern: {args.pattern}")
            return
        
        self.logger.info(f"Found {len(json_files)} files to validate")
        
        # Initialize validator
        validator = self._create_validator(args)
        
        all_reports = []
        
        # Process files in batches
        for i in range(0, len(json_files), args.batch_size):
            batch_files = json_files[i:i + args.batch_size]
            self.logger.info(f"Processing batch {i//args.batch_size + 1}: {len(batch_files)} files")
            
            batch_reports = []
            for file_path in batch_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        file_reports = asyncio.run(validator.validate_batch(data))
                    else:
                        file_reports = [asyncio.run(validator.validate_item(data))]
                    
                    batch_reports.extend(file_reports)
                    
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {e}")
                    continue
            
            all_reports.extend(batch_reports)
        
        # Display results
        self._display_validation_results(all_reports)
        
        # Save reports
        self._save_reports(all_reports, args.output_dir, args.format)
    
    def validate_item(self, args):
        """Validate a single JSON item"""
        item_json = args.item_json
        
        # Check if it's a file path
        if Path(item_json).exists():
            with open(item_json, 'r', encoding='utf-8') as f:
                item_json = f.read()
        
        # Parse JSON
        try:
            item = json.loads(item_json)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON: {e}")
            sys.exit(1)
        
        self.logger.info("Validating single item")
        
        # Initialize validator
        validator = self._create_validator(args)
        
        # Validate item
        report = asyncio.run(validator.validate_item(item))
        
        # Display results
        self._display_validation_results([report])
        
        # Save report
        self._save_reports([report], args.output_dir, args.format)
    
    def generate_report(self, args):
        """Generate summary report from validation results"""
        input_dir = Path(args.input_dir)
        
        if not input_dir.exists() or not input_dir.is_dir():
            self.logger.error(f"Directory not found: {input_dir}")
            sys.exit(1)
        
        # Find validation report files
        report_files = list(input_dir.glob('*.json'))
        
        if not report_files:
            self.logger.warning("No validation report files found")
            return
        
        self.logger.info(f"Found {len(report_files)} validation reports")
        
        # Load and analyze reports
        summary = self._analyze_reports(report_files)
        
        # Generate output
        if args.output:
            output_path = Path(args.output)
            if output_path.suffix == '.html':
                self._generate_html_report(summary, output_path)
            else:
                self._generate_json_report(summary, output_path)
        else:
            self._display_summary(summary)
    
    def test_provider(self, args):
        """Test OpenAI provider connection"""
        self.logger.info("Testing OpenAI provider connection")
        
        # Initialize validator
        validator = self._create_validator(args)
        
        # Test item
        test_item = {
            'title': 'Test Product',
            'pub_url': 'https://mercadolibre.com.uy/test',
            'seller': 'Test Seller',
            'price': 100.0
        }
        
        if args.test_item:
            try:
                test_item = json.loads(args.test_item)
            except json.JSONDecodeError:
                self.logger.error("Invalid test item JSON")
                sys.exit(1)
        
        try:
            # Test validation
            report = asyncio.run(validator.validate_item(test_item))
            
            self.logger.info("✅ Provider connection successful!")
            self.logger.info(f"Validation completed: {report.summary}")
            
            # Display test results
            self._display_validation_results([report])
            
        except Exception as e:
            self.logger.error(f"❌ Provider connection failed: {e}")
            sys.exit(1)
    
    def _create_validator(self, args) -> AIValidator:
        """Create OpenAI validator instance"""
        api_key = args.api_key or self._get_api_key_from_env()
        
        if not api_key:
            self.logger.error("No OpenAI API key found")
            self.logger.error("Set OPENAI_API_KEY environment variable or use --api-key")
            sys.exit(1)
        
        return AIValidator(
            api_key=api_key,
            model=args.model,
            batch_size=args.batch_size
        )
    
    def _get_api_key_from_env(self) -> Optional[str]:
        """Get OpenAI API key from environment variable"""
        return os.getenv('OPENAI_API_KEY')
    
    def _display_validation_results(self, reports: List[ValidationReport]):
        """Display validation results in console"""
        total_items = len(reports)
        total_passed = sum(1 for r in reports if r.overall_status == ValidationStatus.PASSED)
        total_failed = sum(1 for r in reports if r.overall_status == ValidationStatus.FAILED)
        total_warnings = sum(1 for r in reports if r.overall_status == ValidationStatus.WARNING)
        
        print(f"\n{'='*60}")
        print("VALIDATION RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"Total Items: {total_items}")
        print(f"Passed: {total_passed} ✅")
        print(f"Failed: {total_failed} ❌")
        print(f"Warnings: {total_warnings} ⚠️")
        print(f"{'='*60}")
        
        # Display detailed results for failed items
        failed_reports = [r for r in reports if r.overall_status == ValidationStatus.FAILED]
        if failed_reports:
            print("\nFAILED VALIDATIONS:")
            print("-" * 40)
            for report in failed_reports[:5]:  # Show first 5 failures
                print(f"Item: {report.item_id}")
                print(f"Summary: {report.summary}")
                if report.recommendations:
                    print(f"Recommendations: {', '.join(report.recommendations[:2])}")
                print()
        
        # Display AI analysis if available
        ai_reports = [r for r in reports if r.ai_analysis and 'unavailable' not in r.ai_analysis.lower()]
        if ai_reports:
            print("\nAI ANALYSIS HIGHLIGHTS:")
            print("-" * 40)
            for report in ai_reports[:3]:  # Show first 3 AI analyses
                print(f"Item: {report.item_id}")
                print(f"Analysis: {report.ai_analysis[:200]}...")
                print()
    
    def _save_reports(self, reports: List[ValidationReport], output_dir: str, format: str):
        """Save validation reports to files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'json':
            # Save individual reports
            for i, report in enumerate(reports):
                filename = f"validation_report_{i}_{timestamp}.json"
                filepath = output_path / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self._report_to_dict(report), f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"Report saved: {filepath}")
            
            # Save batch summary
            summary_file = output_path / f"validation_summary_{timestamp}.json"
            summary = self._create_summary(reports)
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Summary saved: {summary_file}")
            
        elif format == 'csv':
            # Save as CSV
            csv_file = output_path / f"validation_results_{timestamp}.csv"
            self._save_csv_reports(reports, csv_file)
            self.logger.info(f"CSV report saved: {csv_file}")
            
        elif format == 'html':
            # Save as HTML
            html_file = output_path / f"validation_report_{timestamp}.html"
            self._save_html_reports(reports, html_file)
            self.logger.info(f"HTML report saved: {html_file}")
    
    def _report_to_dict(self, report: ValidationReport) -> Dict[str, Any]:
        """Convert validation report to dictionary"""
        return {
            'item_id': report.item_id,
            'timestamp': report.timestamp,
            'total_validations': report.total_validations,
            'passed_validations': report.passed_validations,
            'failed_validations': report.failed_validations,
            'warning_validations': report.warning_validations,
            'overall_status': report.overall_status.value,
            'summary': report.summary,
            'ai_analysis': report.ai_analysis,
            'recommendations': report.recommendations,
            'results': [
                {
                    'field_name': r.field_name,
                    'status': r.status.value,
                    'level': r.level.value,
                    'message': r.message,
                    'expected_value': r.expected_value,
                    'actual_value': r.actual_value,
                    'suggestion': r.suggestion,
                    'confidence': r.confidence,
                    'timestamp': r.timestamp
                }
                for r in report.results
            ]
        }
    
    def _create_summary(self, reports: List[ValidationReport]) -> Dict[str, Any]:
        """Create summary of validation results"""
        total_items = len(reports)
        total_passed = sum(1 for r in reports if r.overall_status == ValidationStatus.PASSED)
        total_failed = sum(1 for r in reports if r.overall_status == ValidationStatus.FAILED)
        total_warnings = sum(1 for r in reports if r.overall_status == ValidationStatus.WARNING)
        
        # Collect common issues
        all_results = []
        for report in reports:
            all_results.extend(report.results)
        
        issue_counts = {}
        for result in all_results:
            if result.status == ValidationStatus.FAILED:
                issue_key = f"{result.field_name}: {result.message[:50]}..."
                issue_counts[issue_key] = issue_counts.get(issue_key, 0) + 1
        
        # Top issues
        top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_items': total_items,
            'summary': {
                'passed': total_passed,
                'failed': total_failed,
                'warnings': total_warnings,
                'success_rate': (total_passed / total_items * 100) if total_items > 0 else 0
            },
            'top_issues': top_issues,
            'recommendations': self._generate_recommendations(reports)
        }
    
    def _generate_recommendations(self, reports: List[ValidationReport]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        failed_reports = [r for r in reports if r.overall_status == ValidationStatus.FAILED]
        
        if failed_reports:
            # Check for common patterns
            missing_fields = set()
            invalid_urls = 0
            price_issues = 0
            
            for report in failed_reports:
                for result in report.results:
                    if result.status == ValidationStatus.FAILED:
                        if 'missing' in result.message.lower():
                            missing_fields.add(result.field_name)
                        elif 'url' in result.field_name.lower():
                            invalid_urls += 1
                        elif 'price' in result.field_name.lower():
                            price_issues += 1
            
            if missing_fields:
                recommendations.append(f"Ensure required fields are present: {', '.join(missing_fields)}")
            
            if invalid_urls > len(failed_reports) * 0.5:
                recommendations.append("Review URL extraction logic - many invalid URLs detected")
            
            if price_issues > len(failed_reports) * 0.3:
                recommendations.append("Review price extraction and normalization logic")
        
        if not recommendations:
            recommendations.append("Data quality looks good! Continue monitoring for any new patterns.")
        
        return recommendations
    
    def _save_csv_reports(self, reports: List[ValidationReport], filepath: Path):
        """Save validation reports as CSV"""
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Item ID', 'Status', 'Total Validations', 'Passed', 'Failed', 'Warnings',
                'Summary', 'AI Analysis', 'Recommendations'
            ])
            
            # Write data
            for report in reports:
                writer.writerow([
                    report.item_id,
                    report.overall_status.value,
                    report.total_validations,
                    report.passed_validations,
                    report.failed_validations,
                    report.warning_validations,
                    report.summary[:100] + "..." if len(report.summary) > 100 else report.summary,
                    report.ai_analysis[:100] + "..." if len(report.ai_analysis) > 100 else report.ai_analysis,
                    '; '.join(report.recommendations[:3])
                ])
    
    def _save_html_reports(self, reports: List[ValidationReport], filepath: Path):
        """Save validation reports as HTML"""
        html_content = self._generate_html_content(reports)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_html_content(self, reports: List[ValidationReport]) -> str:
        """Generate HTML content for validation reports"""
        summary = self._create_summary(reports)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Validation Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .issues {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .recommendations {{ background-color: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .warning {{ color: orange; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Validation Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Items: {summary['total_items']}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Passed: <span class="passed">{summary['summary']['passed']}</span></p>
        <p>Failed: <span class="failed">{summary['summary']['failed']}</span></p>
        <p>Warnings: <span class="warning">{summary['summary']['warnings']}</span></p>
        <p>Success Rate: {summary['summary']['success_rate']:.1f}%</p>
    </div>
    
    <div class="issues">
        <h2>Top Issues</h2>
        <table>
            <tr><th>Issue</th><th>Count</th></tr>
            {chr(10).join([f'<tr><td>{issue}</td><td>{count}</td></tr>' for issue, count in summary['top_issues']])}
        </table>
    </div>
    
    <div class="recommendations">
        <h2>Recommendations</h2>
        <ul>
            {chr(10).join([f'<li>{rec}</li>' for rec in summary['recommendations']])}
        </ul>
    </div>
    
    <h2>Detailed Results</h2>
    <table>
        <tr>
            <th>Item ID</th>
            <th>Status</th>
            <th>Summary</th>
            <th>AI Analysis</th>
        </tr>
        {chr(10).join([
            f'<tr><td>{r.item_id}</td><td class="{r.overall_status.value}">{r.overall_status.value}</td><td>{r.summary}</td><td>{r.ai_analysis[:100]}...</td></tr>'
            for r in reports[:50]  # Limit to first 50 for HTML
        ])}
    </table>
</body>
</html>
"""
        
        return html
    
    def _analyze_reports(self, report_files: List[Path]) -> Dict[str, Any]:
        """Analyze validation report files"""
        all_reports = []
        
        for file_path in report_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_reports.append(data)
            except Exception as e:
                self.logger.warning(f"Failed to load report {file_path}: {e}")
        
        # Convert back to ValidationReport objects for analysis
        # (This is a simplified approach - in production you'd want proper deserialization)
        return {
            'total_files': len(report_files),
            'successful_loads': len(all_reports),
            'failed_loads': len(report_files) - len(all_reports)
        }
    
    def _display_summary(self, summary: Dict[str, Any]):
        """Display summary in console"""
        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total Files: {summary['total_files']}")
        print(f"Successfully Loaded: {summary['successful_loads']}")
        print(f"Failed to Load: {summary['failed_loads']}")
        print(f"{'='*60}")


def main():
    """Main entry point"""
    cli = ValidationCLI()
    cli.run()


if __name__ == '__main__':
    main()
