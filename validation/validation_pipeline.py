#!/usr/bin/env python3
"""
Validation Pipeline for Scrapy
Integrates AI validation system into the Scrapy pipeline
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
from pathlib import Path

from scrapy import signals
from scrapy.exceptions import DropItem

from .ai_validator import AIValidator, ValidationReport, ValidationStatus


class ValidationPipeline:
    """
    Scrapy pipeline that validates scraped items using AI and rule-based validation
    """
    
    def __init__(self, 
                 enable_ai_validation: bool = True,
                 ai_provider: str = "openai",
                 ai_model: str = "gpt-4",
                 batch_size: int = 10,
                 save_reports: bool = True,
                 reports_dir: str = "validation_reports",
                 drop_invalid_items: bool = False,
                 log_level: str = "INFO"):
        """
        Initialize validation pipeline
        
        Args:
            enable_ai_validation: Whether to enable AI-based validation
            ai_provider: AI provider to use
            ai_model: AI model to use
            batch_size: Number of items to validate in batch
            save_reports: Whether to save validation reports to files
            reports_dir: Directory to save validation reports
            drop_invalid_items: Whether to drop items that fail validation
            log_level: Logging level for validation pipeline
        """
        self.enable_ai_validation = enable_ai_validation
        self.ai_provider = ai_provider
        self.ai_model = ai_model
        self.batch_size = batch_size
        self.save_reports = save_reports
        self.reports_dir = Path(reports_dir)
        self.drop_invalid_items = drop_invalid_items
        self.log_level = log_level
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Initialize AI validator if enabled
        self.validator = None
        if self.enable_ai_validation:
            self._init_validator()
        
        # Create reports directory
        if self.save_reports:
            self.reports_dir.mkdir(exist_ok=True)
        
        # Statistics
        self.stats = {
            'items_processed': 0,
            'items_passed': 0,
            'items_failed': 0,
            'items_warning': 0,
            'validation_errors': 0,
            'ai_validation_errors': 0
        }
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create pipeline from crawler settings"""
        return cls(
            enable_ai_validation=crawler.settings.getbool('VALIDATION_ENABLE_AI', True),
            ai_provider=crawler.settings.get('VALIDATION_AI_PROVIDER', 'openai'),
            ai_model=crawler.settings.get('VALIDATION_AI_MODEL', 'gpt-4'),
            batch_size=crawler.settings.getint('VALIDATION_BATCH_SIZE', 10),
            save_reports=crawler.settings.getbool('VALIDATION_SAVE_REPORTS', True),
            reports_dir=crawler.settings.get('VALIDATION_REPORTS_DIR', 'validation_reports'),
            drop_invalid_items=crawler.settings.getbool('VALIDATION_DROP_INVALID', False),
            log_level=crawler.settings.get('VALIDATION_LOG_LEVEL', 'INFO')
        )
    
    def _init_validator(self):
        """Initialize AI validator with configuration"""
        try:
            # Get API key from environment or settings
            api_key = os.getenv(f'{self.ai_provider.upper()}_API_KEY')
            
            if not api_key:
                self.logger.warning(f"No API key found for {self.ai_provider}. AI validation will be disabled.")
                self.enable_ai_validation = False
                return
            
            self.validator = AIValidator(
                provider=self.ai_provider,
                api_key=api_key,
                model=self.ai_model,
                batch_size=self.batch_size
            )
            
            self.logger.info(f"AI validator initialized with {self.ai_provider} provider")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI validator: {e}")
            self.enable_ai_validation = False
    
    def open_spider(self, spider):
        """Called when spider opens"""
        self.logger.info(f"Validation pipeline opened for spider: {spider.name}")
        
        # Add validation stats to spider stats
        spider.crawler.stats.set_value('validation/items_processed', 0)
        spider.crawler.stats.set_value('validation/items_passed', 0)
        spider.crawler.stats.set_value('validation/items_failed', 0)
        spider.crawler.stats.set_value('validation/items_warning', 0)
        spider.crawler.stats.set_value('validation/errors', 0)
    
    def close_spider(self, spider):
        """Called when spider closes"""
        self.logger.info(f"Validation pipeline closed for spider: {spider.name}")
        self.logger.info(f"Validation Statistics: {json.dumps(self.stats, indent=2)}")
        
        # Update final stats
        spider.crawler.stats.set_value('validation/items_processed', self.stats['items_processed'])
        spider.crawler.stats.set_value('validation/items_passed', self.stats['items_passed'])
        spider.crawler.stats.set_value('validation/items_failed', self.stats['items_failed'])
        spider.crawler.stats.set_value('validation/items_warning', self.stats['items_warning'])
        spider.crawler.stats.set_value('validation/errors', self.stats['validation_errors'])
    
    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """
        Process item through validation pipeline
        
        Args:
            item: Scraped item to validate
            spider: Spider instance
            
        Returns:
            Item with validation results added
        """
        try:
            self.stats['items_processed'] += 1
            
            # Add validation metadata
            item['validation_metadata'] = {
                'validated_at': datetime.now().isoformat(),
                'validation_pipeline': True,
                'ai_validation_enabled': self.enable_ai_validation
            }
            
            # Perform validation
            if self.enable_ai_validation and self.validator:
                validation_report = self._validate_item_async(item)
            else:
                validation_report = self._validate_item_basic(item)
            
            # Add validation results to item
            item['validation_report'] = self._report_to_dict(validation_report)
            
            # Update statistics
            self._update_stats(validation_report)
            
            # Handle validation results
            if validation_report.overall_status == ValidationStatus.FAILED:
                if self.drop_invalid_items:
                    self.logger.warning(f"Dropping invalid item: {item.get('title', 'Unknown')}")
                    raise DropItem(f"Item failed validation: {validation_report.summary}")
                else:
                    self.logger.warning(f"Item validation failed: {validation_report.summary}")
            
            # Save validation report if enabled
            if self.save_reports:
                self._save_validation_report(validation_report, spider)
            
            return item
            
        except Exception as e:
            self.stats['validation_errors'] += 1
            self.logger.error(f"Validation pipeline error: {e}")
            
            # Add error information to item
            item['validation_error'] = {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            return item
    
    def _validate_item_async(self, item: Dict[str, Any]) -> ValidationReport:
        """Validate item using async AI validator"""
        try:
            # Run async validation in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                validation_report = loop.run_until_complete(
                    self.validator.validate_item(item)
                )
            finally:
                loop.close()
            
            return validation_report
            
        except Exception as e:
            self.logger.error(f"AI validation failed: {e}")
            self.stats['ai_validation_errors'] += 1
            
            # Fallback to basic validation
            return self._validate_item_basic(item)
    
    def _validate_item_basic(self, item: Dict[str, Any]) -> ValidationReport:
        """Perform basic rule-based validation without AI"""
        from .ai_validator import ValidationResult, ValidationReport, ValidationStatus, ValidationLevel
        
        results = []
        
        # Basic field validation
        required_fields = ['title', 'pub_url', 'seller', 'price']
        for field in required_fields:
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
        
        # Basic price validation
        if 'price' in item and item['price'] is not None:
            try:
                price = float(item['price'])
                if price < 0:
                    results.append(ValidationResult(
                        field_name="price",
                        status=ValidationStatus.FAILED,
                        level=ValidationLevel.ERROR,
                        message="Price cannot be negative",
                        actual_value=price,
                        timestamp=datetime.now().isoformat()
                    ))
                else:
                    results.append(ValidationResult(
                        field_name="price",
                        status=ValidationStatus.PASSED,
                        level=ValidationLevel.INFO,
                        message="Price is valid",
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
                    timestamp=datetime.now().isoformat()
                ))
        
        # Calculate statistics
        total_validations = len(results)
        passed_validations = len([r for r in results if r.status == ValidationStatus.PASSED])
        failed_validations = len([r for r in results if r.status == ValidationStatus.FAILED])
        warning_validations = len([r for r in results if r.status == ValidationStatus.WARNING])
        
        # Determine overall status
        if failed_validations > 0:
            overall_status = ValidationStatus.FAILED
        elif warning_validations > 0:
            overall_status = ValidationStatus.WARNING
        else:
            overall_status = ValidationStatus.PASSED
        
        # Create basic report
        return ValidationReport(
            item_id=item.get('url_id', item.get('pub_url', 'unknown')),
            timestamp=datetime.now().isoformat(),
            total_validations=total_validations,
            passed_validations=passed_validations,
            failed_validations=failed_validations,
            warning_validations=warning_validations,
            overall_status=overall_status,
            results=results,
            summary=f"Basic validation: {passed_validations}/{total_validations} passed, {failed_validations} failed",
            ai_analysis="AI validation not enabled - using basic rule-based validation",
            recommendations=["Enable AI validation for more comprehensive analysis"]
        )
    
    def _report_to_dict(self, report: ValidationReport) -> Dict[str, Any]:
        """Convert validation report to dictionary for JSON serialization"""
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
    
    def _update_stats(self, report: ValidationReport):
        """Update validation statistics"""
        if report.overall_status == ValidationStatus.PASSED:
            self.stats['items_passed'] += 1
        elif report.overall_status == ValidationStatus.FAILED:
            self.stats['items_failed'] += 1
        elif report.overall_status == ValidationStatus.WARNING:
            self.stats['items_warning'] += 1
    
    def _save_validation_report(self, report: ValidationReport, spider):
        """Save validation report to file"""
        try:
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            item_id = report.item_id.replace('/', '_').replace(':', '_')[:50]
            filename = f"{spider.name}_{item_id}_{timestamp}.json"
            filepath = self.reports_dir / filename
            
            # Save report
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._report_to_dict(report), f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Validation report saved: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to save validation report: {e}")


class BatchValidationPipeline:
    """
    Pipeline that validates items in batches for better AI performance
    """
    
    def __init__(self, 
                 batch_size: int = 50,
                 enable_ai_validation: bool = True,
                 ai_provider: str = "openai",
                 ai_model: str = "gpt-4",
                 save_reports: bool = True,
                 reports_dir: str = "validation_reports"):
        """
        Initialize batch validation pipeline
        
        Args:
            batch_size: Number of items to collect before validation
            enable_ai_validation: Whether to enable AI-based validation
            ai_provider: AI provider to use
            ai_model: AI model to use
            save_reports: Whether to save validation reports
            reports_dir: Directory to save validation reports
        """
        self.batch_size = batch_size
        self.enable_ai_validation = enable_ai_validation
        self.ai_provider = ai_provider
        self.ai_model = ai_model
        self.save_reports = save_reports
        self.reports_dir = Path(reports_dir)
        
        # Initialize validator
        self.validator = None
        if self.enable_ai_validation:
            self._init_validator()
        
        # Create reports directory
        if self.save_reports:
            self.reports_dir.mkdir(exist_ok=True)
        
        # Item buffer
        self.item_buffer = []
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create pipeline from crawler settings"""
        return cls(
            batch_size=crawler.settings.getint('VALIDATION_BATCH_SIZE', 50),
            enable_ai_validation=crawler.settings.getbool('VALIDATION_ENABLE_AI', True),
            ai_provider=crawler.settings.get('VALIDATION_AI_PROVIDER', 'openai'),
            ai_model=crawler.settings.get('VALIDATION_AI_MODEL', 'gpt-4'),
            save_reports=crawler.settings.getbool('VALIDATION_SAVE_REPORTS', True),
            reports_dir=crawler.settings.get('VALIDATION_REPORTS_DIR', 'validation_reports')
        )
    
    def _init_validator(self):
        """Initialize AI validator"""
        try:
            api_key = os.getenv(f'{self.ai_provider.upper()}_API_KEY')
            if not api_key:
                self.logger.warning(f"No API key found for {self.ai_provider}")
                self.enable_ai_validation = False
                return
            
            self.validator = AIValidator(
                provider=self.ai_provider,
                api_key=api_key,
                model=self.ai_model,
                batch_size=self.batch_size
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI validator: {e}")
            self.enable_ai_validation = False
    
    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Add item to buffer and process batch when full"""
        # Add validation metadata
        item['validation_metadata'] = {
            'validated_at': datetime.now().isoformat(),
            'validation_pipeline': 'batch',
            'ai_validation_enabled': self.enable_ai_validation
        }
        
        # Add to buffer
        self.item_buffer.append(item)
        
        # Process batch if full
        if len(self.item_buffer) >= self.batch_size:
            self._process_batch(spider)
        
        return item
    
    def _process_batch(self, spider):
        """Process current batch of items"""
        if not self.item_buffer:
            return
        
        try:
            self.logger.info(f"Processing validation batch of {len(self.item_buffer)} items")
            
            # Validate batch
            if self.enable_ai_validation and self.validator:
                validation_reports = self._validate_batch_async(self.item_buffer)
            else:
                validation_reports = self._validate_batch_basic(self.item_buffer)
            
            # Add validation results to items
            for item, report in zip(self.item_buffer, validation_reports):
                item['validation_report'] = self._report_to_dict(report)
                
                # Save individual reports if enabled
                if self.save_reports:
                    self._save_validation_report(report, spider)
            
            # Clear buffer
            self.item_buffer = []
            
        except Exception as e:
            self.logger.error(f"Batch validation failed: {e}")
            # Clear buffer on error to prevent memory issues
            self.item_buffer = []
    
    def _validate_batch_async(self, items: List[Dict[str, Any]]) -> List[ValidationReport]:
        """Validate batch using async AI validator"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                reports = loop.run_until_complete(
                    self.validator.validate_batch(items)
                )
            finally:
                loop.close()
            
            return reports
            
        except Exception as e:
            self.logger.error(f"AI batch validation failed: {e}")
            return self._validate_batch_basic(items)
    
    def _validate_batch_basic(self, items: List[Dict[str, Any]]) -> List[ValidationReport]:
        """Perform basic validation on batch without AI"""
        from .ai_validator import ValidationResult, ValidationReport, ValidationStatus, ValidationLevel
        
        reports = []
        
        for item in items:
            results = []
            
            # Basic validation logic (similar to basic pipeline)
            required_fields = ['title', 'pub_url', 'seller', 'price']
            for field in required_fields:
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
            
            # Calculate statistics
            total_validations = len(results)
            passed_validations = len([r for r in results if r.status == ValidationStatus.PASSED])
            failed_validations = len([r for r in results if r.status == ValidationStatus.FAILED])
            
            # Determine overall status
            if failed_validations > 0:
                overall_status = ValidationStatus.FAILED
            else:
                overall_status = ValidationStatus.PASSED
            
            # Create report
            report = ValidationReport(
                item_id=item.get('url_id', item.get('pub_url', 'unknown')),
                timestamp=datetime.now().isoformat(),
                total_validations=total_validations,
                passed_validations=passed_validations,
                failed_validations=failed_validations,
                warning_validations=0,
                overall_status=overall_status,
                results=results,
                summary=f"Basic validation: {passed_validations}/{total_validations} passed, {failed_validations} failed",
                ai_analysis="AI validation not enabled - using basic rule-based validation",
                recommendations=["Enable AI validation for more comprehensive analysis"]
            )
            
            reports.append(report)
        
        return reports
    
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
    
    def _save_validation_report(self, report: ValidationReport, spider):
        """Save validation report to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            item_id = report.item_id.replace('/', '_').replace(':', '_')[:50]
            filename = f"{spider.name}_batch_{item_id}_{timestamp}.json"
            filepath = self.reports_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._report_to_dict(report), f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Failed to save validation report: {e}")
    
    def close_spider(self, spider):
        """Process remaining items in buffer when spider closes"""
        if self.item_buffer:
            self.logger.info(f"Processing final batch of {len(self.item_buffer)} items")
            self._process_batch(spider)
