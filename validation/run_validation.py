#!/usr/bin/env python3
"""
Sample validation script for Meli Challenge
Demonstrates usage of the AI validation system
"""

import asyncio
import json
import os
from pathlib import Path
from typing import List, Dict, Any

from ai_validator import AIValidator, ValidationReport, ValidationStatus


def load_sample_data() -> List[Dict[str, Any]]:
    """Load sample data for validation"""
    sample_items = [
        {
            "title": "iPhone 15 Pro Max 256GB - Negro",
            "pub_url": "https://articulo.mercadolibre.com.uy/MLU-123456789-iphone-15-pro-max-negro",
            "seller": "Apple Store Uruguay",
            "price": 1299.99,
            "currency": "USD",
            "original_price": 1499.99,
            "discount_percentage": 13.33,
            "reviews_count": 45,
            "rating": 4.8,
            "availability": "In Stock",
            "features": [
                "Pantalla Super Retina XDR de 6.7 pulgadas",
                "Chip A17 Pro con Neural Engine",
                "Sistema de cámara triple de 48MP"
            ],
            "images": [
                {"url": "https://http2.mlstatic.com/D_Q_NP_2X_123456-MLA123456789_012024-R.webp"},
                {"url": "https://http2.mlstatic.com/D_Q_NP_2X_789012-MLA123456789_012024-F.webp"}
            ],
            "description": "El iPhone 15 Pro Max representa lo último en innovación de Apple..."
        },
        {
            "title": "",
            "pub_url": "https://example.com/invalid-product",
            "seller": "Por ",
            "price": -50.0,
            "currency": "UYU"
        },
        {
            "title": "Product",
            "pub_url": "https://articulo.mercadolibre.com.uy/MLU-987654321-generic-product",
            "seller": "Generic Seller",
            "price": 999999.99,
            "original_price": 1000000.00,
            "discount_percentage": 0.01
        },
        {
            "title": "Samsung Galaxy S24 Ultra 512GB",
            "pub_url": "https://articulo.mercadolibre.com.uy/MLU-555666777-samsung-galaxy-s24-ultra",
            "seller": "Samsung Uruguay",
            "price": 1199.99,
            "currency": "USD",
            "reviews_count": 32,
            "rating": 4.9,
            "availability": "Limited Stock",
            "features": [
                "Pantalla Dynamic AMOLED 2X de 6.8 pulgadas",
                "Chip Snapdragon 8 Gen 3",
                "Cámara principal de 200MP"
            ],
            "images": [
                {"url": "https://http2.mlstatic.com/D_Q_NP_2X_111222-MLA555666777_012024-R.webp"}
            ],
            "description": "El Samsung Galaxy S24 Ultra redefine la experiencia móvil..."
        }
    ]
    
    return sample_items


async def validate_sample_data(api_key: str = None):
    """Validate sample data using OpenAI validation"""
    
    # Initialize validator
    validator = AIValidator(
        api_key=api_key,
        model="gpt-3.5-turbo",
        batch_size=2
    )
    
    # Load sample data
    sample_items = load_sample_data()
    
    print(f"🔍 Starting validation of {len(sample_items)} sample items using OpenAI")
    print("=" * 80)
    
    # Validate items in batch
    validation_reports = await validator.validate_batch(sample_items)
    
    # Display results
    display_validation_results(validation_reports)
    
    # Save reports
    save_validation_reports(validation_reports)
    
    return validation_reports


def display_validation_results(reports: List[ValidationReport]):
    """Display validation results in a formatted way"""
    
    print("\n📊 VALIDATION RESULTS SUMMARY")
    print("=" * 80)
    
    total_items = len(reports)
    total_passed = sum(1 for r in reports if r.overall_status == ValidationStatus.PASSED)
    total_failed = sum(1 for r in reports if r.overall_status == ValidationStatus.FAILED)
    total_warnings = sum(1 for r in reports if r.overall_status == ValidationStatus.WARNING)
    
    print(f"Total Items: {total_items}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Warnings: {total_warnings}")
    print(f"Success Rate: {(total_passed / total_items * 100):.1f}%")
    
    print("\n" + "=" * 80)
    
    # Display detailed results for each item
    for i, report in enumerate(reports, 1):
        print(f"\n Item {i}: {report.item_id}")
        print(f"Status: {get_status_emoji(report.overall_status)} {report.overall_status.value.upper()}")
        print(f"Summary: {report.summary}")
        
        if report.ai_analysis and 'unavailable' not in report.ai_analysis.lower():
            print(f"AI Analysis: {report.ai_analysis[:150]}...")
        
        if report.recommendations:
            print("Recommendations:")
            for rec in report.recommendations[:3]:
                print(f"   • {rec}")
        
        # Show failed validations
        failed_results = [r for r in report.results if r.status == ValidationStatus.FAILED]
        if failed_results:
            print("❌ Failed Validations:")
            for result in failed_results:
                print(f"   • {result.field_name}: {result.message}")
                if result.suggestion:
                    print(f"     Suggestion: {result.suggestion}")
        
        print("-" * 60)


def get_status_emoji(status: ValidationStatus) -> str:
    """Get emoji for validation status"""
    emoji_map = {
        ValidationStatus.PASSED: "✅",
        ValidationStatus.FAILED: "❌",
        ValidationStatus.WARNING: "⚠️",
        ValidationStatus.SKIPPED: "⏭️"
    }
    return emoji_map.get(status, "❓")


def save_validation_reports(reports: List[ValidationReport]):
    """Save validation reports to files"""
    
    # Create output directory
    output_dir = Path("validation_reports")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = reports[0].timestamp.split('T')[0] if reports else "unknown"
    
    # Save individual reports
    for i, report in enumerate(reports):
        filename = f"validation_report_{i+1}_{timestamp}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_to_dict(report), f, indent=2, ensure_ascii=False)
        
        print(f"Report saved: {filepath}")
    
    # Save summary
    summary_file = output_dir / f"validation_summary_{timestamp}.json"
    summary = create_summary(reports)
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"Summary saved: {summary_file}")


def report_to_dict(report: ValidationReport) -> Dict[str, Any]:
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


def create_summary(reports: List[ValidationReport]) -> Dict[str, Any]:
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
    top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        'timestamp': reports[0].timestamp if reports else None,
        'total_items': total_items,
        'summary': {
            'passed': total_passed,
            'failed': total_failed,
            'warnings': total_warnings,
            'success_rate': (total_passed / total_items * 100) if total_items > 0 else 0
        },
        'top_issues': top_issues,
        'recommendations': generate_recommendations(reports)
    }


def generate_recommendations(reports: List[ValidationReport]) -> List[str]:
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


async def main():
    """Main function"""
    
    print("AI Validation System for Meli Challenge")
    print("=" * 80)
    
    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("No OpenAI API key found!")
        print("Please set the OPENAI_API_KEY environment variable:")
        print("  - OPENAI_API_KEY (for OpenAI)")
        print("\nExample:")
        print("  export OPENAI_API_KEY='your_api_key_here'")
        return
    
    print(f"🔑 Using OpenAI API")
    print(f"📁 Sample data will be validated and reports saved to 'validation_reports/' directory")
    
    try:
        # Run validation
        reports = await validate_sample_data(api_key)
        
        print("\n🎉 Validation completed successfully!")
        print(f"📊 Check the 'validation_reports/' directory for detailed results")
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        print("Please check your API key and internet connection")


if __name__ == "__main__":
    # Run the validation
    asyncio.run(main())
