#!/usr/bin/env python3
"""
Generative AI Validation System for Meli Challenge
Uses AI models to validate data quality, completeness, and consistency
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
from dataclasses import dataclass, asdict
from enum import Enum

# OpenAI import
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class ValidationLevel(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationStatus(Enum):
    """Validation result status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class ValidationResult:
    """Individual validation result"""
    field_name: str
    status: ValidationStatus
    level: ValidationLevel
    message: str
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    suggestion: Optional[str] = None
    confidence: float = 1.0
    timestamp: str = ""


@dataclass
class ValidationReport:
    """Complete validation report"""
    item_id: str
    timestamp: str
    total_validations: int
    passed_validations: int
    failed_validations: int
    warning_validations: int
    overall_status: ValidationStatus
    results: List[ValidationResult]
    summary: str
    ai_analysis: str
    recommendations: List[str]


class AIValidator:
    """
    Generative AI-powered data validator for scraped items
    Supports multiple AI providers and validation strategies
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "gpt-3.5-turbo",
                 batch_size: int = 10,
                 max_retries: int = 3):
        """
        Initialize OpenAI validator
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use for validation (default: gpt-3.5-turbo)
            batch_size: Number of items to validate in batch
            max_retries: Maximum retry attempts for API calls
        """
        self.provider = "openai"
        self.api_key = api_key
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI client
        self._init_ai_client()
        
        # Validation rules and thresholds
        self.validation_rules = self._load_validation_rules()
        
    def _init_ai_client(self):
        """Initialize OpenAI client"""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Install with: pip install openai")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules and thresholds"""
        return {
            "price_ranges": {
                "min_price": 0.01,
                "max_price": 1000000.0,
                "currency_required": True
            },
            "url_patterns": {
                "mercadolibre_pattern": r"https?://(?:www\.)?(?:mercadolibre\.com\.uy|articulo\.mercadolibre\.com\.uy|listado\.mercadolibre\.com\.uy)",
                "image_pattern": r"https?://.*\.(?:jpg|jpeg|png|webp|gif)(?:\?.*)?$"
            },
            "field_requirements": {
                "required_fields": ["title", "pub_url", "seller", "price"],
                "optional_fields": ["original_price", "currency", "reviews_count", "rating", "availability", "features", "images", "description"]
            },
            "data_consistency": {
                "discount_tolerance": 0.01,  # 1% tolerance for discount calculations
                "price_consistency": True,
                "seller_format": True
            }
        }
    
    async def validate_item(self, item: Dict[str, Any]) -> ValidationReport:
        """
        Validate a single scraped item using AI and rule-based validation
        
        Args:
            item: Scraped item dictionary
            
        Returns:
            ValidationReport with detailed results
        """
        item_id = item.get('url_id', item.get('pub_url', 'unknown'))
        timestamp = datetime.now().isoformat()
        
        # Perform rule-based validations
        rule_results = self._validate_rules(item)
        
        # Perform AI-based validations
        ai_results = await self._validate_with_ai(item)
        
        # Combine results
        all_results = rule_results + ai_results
        
        # Calculate statistics
        total_validations = len(all_results)
        passed_validations = len([r for r in all_results if r.status == ValidationStatus.PASSED])
        failed_validations = len([r for r in all_results if r.status == ValidationStatus.FAILED])
        warning_validations = len([r for r in all_results if r.status == ValidationStatus.WARNING])
        
        # Determine overall status
        if failed_validations > 0:
            overall_status = ValidationStatus.FAILED
        elif warning_validations > 0:
            overall_status = ValidationStatus.WARNING
        else:
            overall_status = ValidationStatus.PASSED
        
        # Generate AI analysis and recommendations
        ai_analysis, recommendations = await self._generate_ai_analysis(item, all_results)
        
        # Create summary
        summary = self._generate_summary(all_results)
        
        return ValidationReport(
            item_id=item_id,
            timestamp=timestamp,
            total_validations=total_validations,
            passed_validations=passed_validations,
            failed_validations=failed_validations,
            warning_validations=warning_validations,
            overall_status=overall_status,
            results=all_results,
            summary=summary,
            ai_analysis=ai_analysis,
            recommendations=recommendations
        )
    
    def _validate_rules(self, item: Dict[str, Any]) -> List[ValidationResult]:
        """Perform rule-based validations"""
        results = []
        
        # Validate required fields
        for field in self.validation_rules["field_requirements"]["required_fields"]:
            if field not in item or not item[field]:
                results.append(ValidationResult(
                    field_name=field,
                    status=ValidationStatus.FAILED,
                    level=ValidationLevel.ERROR,
                    message=f"Required field '{field}' is missing or empty",
                    actual_value=item.get(field),
                    timestamp=datetime.now().isoformat()
                ))
            else:
                results.append(ValidationResult(
                    field_name=field,
                    status=ValidationStatus.PASSED,
                    level=ValidationLevel.INFO,
                    message=f"Required field '{field}' is present",
                    actual_value=item.get(field),
                    timestamp=datetime.now().isoformat()
                ))
        
        # Validate price format and range
        if 'price' in item and item['price'] is not None:
            try:
                price = float(item['price'])
                if price < self.validation_rules["price_ranges"]["min_price"]:
                    results.append(ValidationResult(
                        field_name="price",
                        status=ValidationStatus.WARNING,
                        level=ValidationLevel.WARNING,
                        message=f"Price {price} is below minimum threshold",
                        expected_value=f">= {self.validation_rules['price_ranges']['min_price']}",
                        actual_value=price,
                        suggestion="Verify if this is a valid price or data error",
                        timestamp=datetime.now().isoformat()
                    ))
                elif price > self.validation_rules["price_ranges"]["max_price"]:
                    results.append(ValidationResult(
                        field_name="price",
                        status=ValidationStatus.WARNING,
                        level=ValidationLevel.WARNING,
                        message=f"Price {price} is above maximum threshold",
                        expected_value=f"<= {self.validation_rules['price_ranges']['max_price']}",
                        actual_value=price,
                        suggestion="Verify if this is a valid price or data error",
                        timestamp=datetime.now().isoformat()
                    ))
                else:
                    results.append(ValidationResult(
                        field_name="price",
                        status=ValidationStatus.PASSED,
                        level=ValidationLevel.INFO,
                        message=f"Price {price} is within valid range",
                        actual_value=price,
                        timestamp=datetime.now().isoformat()
                    ))
            except (ValueError, TypeError):
                results.append(ValidationResult(
                    field_name="price",
                    status=ValidationStatus.FAILED,
                    level=ValidationLevel.ERROR,
                    message="Price is not a valid number",
                    actual_value=item.get('price'),
                    suggestion="Ensure price is a numeric value",
                    timestamp=datetime.now().isoformat()
                ))
        
        # Validate URL format
        if 'pub_url' in item and item['pub_url']:
            url = item['pub_url']
            pattern = self.validation_rules["url_patterns"]["mercadolibre_pattern"]
            if re.match(pattern, url):
                results.append(ValidationResult(
                    field_name="pub_url",
                    status=ValidationStatus.PASSED,
                    level=ValidationLevel.INFO,
                    message="URL format is valid MercadoLibre URL",
                    actual_value=url,
                    timestamp=datetime.now().isoformat()
                ))
            else:
                results.append(ValidationResult(
                    field_name="pub_url",
                    status=ValidationStatus.FAILED,
                    level=ValidationLevel.ERROR,
                    message="URL format is not a valid MercadoLibre URL",
                    actual_value=url,
                    suggestion="Verify URL format and domain",
                    timestamp=datetime.now().isoformat()
                ))
        
        # Validate discount consistency
        if all(field in item for field in ['price', 'original_price']):
            try:
                price = float(item['price'])
                original_price = float(item['original_price'])
                
                if original_price > 0:
                    calculated_discount = ((original_price - price) / original_price) * 100
                    
                    # Check if discount calculation is consistent
                    if 'discount_percentage' in item and item['discount_percentage'] is not None:
                        stored_discount = float(item['discount_percentage'])
                        difference = abs(calculated_discount - stored_discount)
                        
                        if difference > self.validation_rules["data_consistency"]["discount_tolerance"]:
                            results.append(ValidationResult(
                                field_name="discount_percentage",
                                status=ValidationStatus.WARNING,
                                level=ValidationLevel.WARNING,
                                message=f"Discount calculation mismatch: calculated {calculated_discount:.2f}% vs stored {stored_discount:.2f}%",
                                expected_value=f"{calculated_discount:.2f}%",
                                actual_value=f"{stored_discount:.2f}%",
                                suggestion="Recalculate discount percentage",
                                timestamp=datetime.now().isoformat()
                            ))
                        else:
                            results.append(ValidationResult(
                                field_name="discount_percentage",
                                status=ValidationStatus.PASSED,
                                level=ValidationLevel.INFO,
                                message="Discount calculation is consistent",
                                actual_value=f"{stored_discount:.2f}%",
                                timestamp=datetime.now().isoformat()
                            ))
            except (ValueError, TypeError):
                pass
        
        # Validate image URLs
        if 'images' in item and isinstance(item['images'], list):
            for i, image in enumerate(item['images']):
                if isinstance(image, dict) and 'url' in image:
                    image_url = image['url']
                    pattern = self.validation_rules["url_patterns"]["image_pattern"]
                    if re.match(pattern, image_url):
                        results.append(ValidationResult(
                            field_name=f"images[{i}].url",
                            status=ValidationStatus.PASSED,
                            level=ValidationLevel.INFO,
                            message="Image URL format is valid",
                            actual_value=image_url,
                            timestamp=datetime.now().isoformat()
                        ))
                    else:
                        results.append(ValidationResult(
                            field_name=f"images[{i}].url",
                            status=ValidationStatus.WARNING,
                            level=ValidationLevel.WARNING,
                            message="Image URL format may be invalid",
                            actual_value=image_url,
                            suggestion="Verify image URL format",
                            timestamp=datetime.now().isoformat()
                        ))
        
        return results
    
    async def _validate_with_ai(self, item: Dict[str, Any]) -> List[ValidationResult]:
        """Perform AI-based validations"""
        results = []
        
        try:
            # Prepare prompt for AI validation
            prompt = self._create_validation_prompt(item)
            
            # Get AI response
            ai_response = await self._call_ai_api(prompt)
            
            # Parse AI response
            ai_results = self._parse_ai_response(ai_response)
            results.extend(ai_results)
            
        except Exception as e:
            self.logger.error(f"AI validation failed: {e}")
            results.append(ValidationResult(
                field_name="ai_validation",
                status=ValidationStatus.SKIPPED,
                level=ValidationLevel.WARNING,
                message=f"AI validation failed: {str(e)}",
                suggestion="Check AI provider configuration and API key",
                timestamp=datetime.now().isoformat()
            ))
        
        return results
    
    def _create_validation_prompt(self, item: Dict[str, Any]) -> str:
        """Create prompt for AI validation"""
        prompt = f"""
        You are a data quality expert analyzing scraped product data from MercadoLibre Uruguay.
        
        Please analyze the following product data and identify any quality issues, inconsistencies, or potential errors:
        
        Product Data:
        {json.dumps(item, indent=2, ensure_ascii=False)}
        
        Please provide validation results in the following JSON format:
        {{
            "validations": [
                {{
                    "field_name": "field_name",
                    "issue_type": "missing|inconsistent|invalid|outlier|suspicious",
                    "severity": "low|medium|high|critical",
                    "description": "Detailed description of the issue",
                    "suggestion": "How to fix or improve this data",
                    "confidence": 0.95
                }}
            ],
            "overall_assessment": "Brief overall assessment of data quality",
            "recommendations": ["List of specific recommendations for improvement"]
        }}
        
        Focus on:
        1. Data completeness and missing fields
        2. Data consistency (e.g., price calculations, seller information)
        3. Data format validity (URLs, images, prices)
        4. Outliers or suspicious values
        5. Business logic consistency
        
        Be specific and provide actionable feedback.
        """
        return prompt
    
    async def _call_ai_api(self, prompt: str) -> str:
        """Call OpenAI API with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0.1
                )
                return response.choices[0].message.content
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception("All AI API call attempts failed")
    
    def _parse_ai_response(self, ai_response: str) -> List[ValidationResult]:
        """Parse AI response into validation results"""
        results = []
        
        try:
            # Try to extract JSON from response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start != -1 and json_end != 0:
                json_str = ai_response[json_start:json_end]
                ai_data = json.loads(json_str)
                
                # Parse validations
                for validation in ai_data.get('validations', []):
                    # Map AI severity to validation level
                    severity_map = {
                        'low': ValidationLevel.INFO,
                        'medium': ValidationLevel.WARNING,
                        'high': ValidationLevel.ERROR,
                        'critical': ValidationLevel.CRITICAL
                    }
                    
                    level = severity_map.get(validation.get('severity', 'medium'), ValidationLevel.WARNING)
                    
                    # Determine status based on issue type
                    issue_type = validation.get('issue_type', '')
                    if issue_type in ['missing', 'invalid', 'critical']:
                        status = ValidationStatus.FAILED
                    elif issue_type in ['inconsistent', 'outlier', 'suspicious']:
                        status = ValidationStatus.WARNING
                    else:
                        status = ValidationStatus.PASSED
                    
                    results.append(ValidationResult(
                        field_name=validation.get('field_name', 'unknown'),
                        status=status,
                        level=level,
                        message=validation.get('description', 'AI validation result'),
                        suggestion=validation.get('suggestion'),
                        confidence=validation.get('confidence', 0.8),
                        timestamp=datetime.now().isoformat()
                    ))
        
        except Exception as e:
            self.logger.error(f"Failed to parse AI response: {e}")
            results.append(ValidationResult(
                field_name="ai_parsing",
                status=ValidationStatus.SKIPPED,
                level=ValidationLevel.WARNING,
                message=f"Failed to parse AI response: {str(e)}",
                actual_value=ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
                timestamp=datetime.now().isoformat()
            ))
        
        return results
    
    async def _generate_ai_analysis(self, item: Dict[str, Any], results: List[ValidationResult]) -> Tuple[str, List[str]]:
        """Generate AI analysis and recommendations"""
        try:
            # Create analysis prompt
            prompt = f"""
            Based on the following validation results for a scraped product, provide:
            1. A brief analysis of the overall data quality
            2. Specific recommendations for improvement
            
            Product: {item.get('title', 'Unknown')}
            Validation Results: {len(results)} total, {len([r for r in results if r.status == ValidationStatus.FAILED])} failed
            
            Key Issues Found:
            {chr(10).join([f"- {r.field_name}: {r.message}" for r in results if r.status == ValidationStatus.FAILED][:5])}
            
            Please provide:
            1. A 2-3 sentence analysis of the data quality
            2. 3-5 specific, actionable recommendations
            
            Format as JSON:
            {{
                "analysis": "Brief analysis text",
                "recommendations": ["rec1", "rec2", "rec3"]
            }}
            """
            
            # Get AI response
            ai_response = await self._call_ai_api(prompt)
            
            # Parse response
            try:
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_str = ai_response[json_start:json_end]
                    ai_data = json.loads(json_str)
                    return ai_data.get('analysis', 'AI analysis unavailable'), ai_data.get('recommendations', [])
            except:
                pass
            
            # Fallback parsing
            return f"AI analysis: {ai_response[:200]}...", ["Review validation results for specific issues"]
            
        except Exception as e:
            self.logger.error(f"AI analysis generation failed: {e}")
            return "AI analysis unavailable due to technical issues", ["Review validation results manually"]
    
    def _generate_summary(self, results: List[ValidationResult]) -> str:
        """Generate human-readable summary of validation results"""
        total = len(results)
        passed = len([r for r in results if r.status == ValidationStatus.PASSED])
        failed = len([r for r in results if r.status == ValidationStatus.FAILED])
        warnings = len([r for r in results if r.status == ValidationStatus.WARNING])
        
        summary = f"Validation Summary: {passed}/{total} passed, {failed} failed, {warnings} warnings"
        
        if failed > 0:
            critical_issues = [r for r in results if r.level == ValidationLevel.CRITICAL and r.status == ValidationStatus.FAILED]
            if critical_issues:
                summary += f". {len(critical_issues)} critical issues detected."
        
        return summary
    
    async def validate_batch(self, items: List[Dict[str, Any]]) -> List[ValidationReport]:
        """Validate multiple items in batch"""
        reports = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_reports = await asyncio.gather(*[self.validate_item(item) for item in batch])
            reports.extend(batch_reports)
            
            # Add delay between batches to avoid rate limiting
            if i + self.batch_size < len(items):
                await asyncio.sleep(1)
        
        return reports
    
    def export_report(self, report: ValidationReport, format: str = "json") -> str:
        """Export validation report in specified format"""
        if format.lower() == "json":
            return json.dumps(asdict(report), indent=2, ensure_ascii=False)
        elif format.lower() == "csv":
            # Simple CSV export
            csv_lines = [
                "Field,Status,Level,Message,Expected,Actual,Suggestion,Confidence,Timestamp"
            ]
            for result in report.results:
                csv_lines.append(f'"{result.field_name}","{result.status.value}","{result.level.value}","{result.message}","{result.expected_value or ""}","{result.actual_value or ""}","{result.suggestion or ""}","{result.confidence}","{result.timestamp}"')
            return "\n".join(csv_lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Convenience function for synchronous usage
def validate_item_sync(item: Dict[str, Any], **kwargs) -> ValidationReport:
    """Synchronous wrapper for validate_item"""
    validator = AIValidator(**kwargs)
    return asyncio.run(validator.validate_item(item))


def validate_batch_sync(items: List[Dict[str, Any]], **kwargs) -> List[ValidationReport]:
    """Synchronous wrapper for validate_batch"""
    validator = AIValidator(**kwargs)
    return asyncio.run(validator.validate_batch(items))
