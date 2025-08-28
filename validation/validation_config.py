#!/usr/bin/env python3
"""
Configuration for AI Validation System
Contains validation rules, thresholds, and AI provider settings
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationRules:
    """Validation rules and thresholds"""
    
    # Field requirements
    required_fields: List[str] = field(default_factory=lambda: [
        'title', 'pub_url', 'seller', 'price'
    ])
    
    optional_fields: List[str] = field(default_factory=lambda: [
        'original_price', 'currency', 'reviews_count', 'rating', 
        'availability', 'features', 'images', 'description'
    ])
    
    # Price validation
    price_ranges: Dict[str, Any] = field(default_factory=lambda: {
        'min_price': 0.01,
        'max_price': 1000000.0,
        'currency_required': True,
        'default_currency': 'UYU',
        'price_formats': [
            r'^\d+$',                    # 100
            r'^\d+,\d+$',                # 100,50
            r'^\d+\.\d+$',               # 100.50
            r'^\d+\.\d+,\d+$',          # 1.234,56
            r'^\d+\.\d+\.\d+,\d+$',     # 1.234.567,89
        ]
    })
    
    # URL validation
    url_patterns: Dict[str, str] = field(default_factory=lambda: {
        'mercadolibre_pattern': r'https?://(?:www\.)?(?:mercadolibre\.com\.uy|articulo\.mercadolibre\.com\.uy|listado\.mercadolibre\.com\.uy)',
        'image_pattern': r'https?://.*\.(?:jpg|jpeg|png|webp|gif)(?:\?.*)?$',
        'product_pattern': r'https?://(?:www\.)?(?:mercadolibre\.com\.uy|articulo\.mercadolibre\.com\.uy)/[^/]+',
        'category_pattern': r'https?://(?:www\.)?listado\.mercadolibre\.com\.uy/[^/]+'
    })
    
    # Data consistency
    data_consistency: Dict[str, Any] = field(default_factory=lambda: {
        'discount_tolerance': 0.01,  # 1% tolerance for discount calculations
        'price_consistency': True,
        'seller_format': True,
        'url_consistency': True,
        'image_consistency': True
    })
    
    # Seller validation
    seller_validation: Dict[str, Any] = field(default_factory=lambda: {
        'remove_prefixes': ['Por ', 'Vendedor: ', 'Seller: '],
        'default_value': 'no seller found',
        'min_length': 2,
        'max_length': 100,
        'forbidden_values': ['', 'N/A', 'None', 'null', 'undefined']
    })
    
    # Content validation
    content_validation: Dict[str, Any] = field(default_factory=lambda: {
        'title_min_length': 3,
        'title_max_length': 200,
        'description_min_length': 10,
        'description_max_length': 5000,
        'features_min_count': 0,
        'features_max_count': 50,
        'images_min_count': 0,
        'images_max_count': 20
    })


@dataclass
class AIProviderConfig:
    """AI provider configuration"""
    
    # OpenAI configuration
    openai: Dict[str, Any] = field(default_factory=lambda: {
        'default_model': 'gpt-4',
        'fallback_model': 'gpt-3.5-turbo',
        'max_tokens': 2000,
        'temperature': 0.1,
        'timeout': 30,
        'max_retries': 3
    })
    
    # Anthropic configuration
    anthropic: Dict[str, Any] = field(default_factory=lambda: {
        'default_model': 'claude-3-sonnet-20240229',
        'fallback_model': 'claude-3-haiku-20240307',
        'max_tokens': 2000,
        'temperature': 0.1,
        'timeout': 30,
        'max_retries': 3
    })
    
    # Google configuration
    google: Dict[str, Any] = field(default_factory=lambda: {
        'default_model': 'gemini-pro',
        'fallback_model': 'gemini-pro',
        'max_tokens': 2000,
        'temperature': 0.1,
        'timeout': 30,
        'max_retries': 3
    })


@dataclass
class ValidationPipelineConfig:
    """Validation pipeline configuration"""
    
    # General settings
    enable_ai_validation: bool = True
    enable_rule_validation: bool = True
    enable_batch_processing: bool = True
    
    # Pipeline settings
    batch_size: int = 10
    max_concurrent_validations: int = 5
    save_reports: bool = True
    reports_dir: str = "validation_reports"
    
    # Error handling
    drop_invalid_items: bool = False
    continue_on_error: bool = True
    log_validation_errors: bool = True
    
    # Performance
    validation_timeout: int = 60
    cache_validation_results: bool = True
    cache_ttl: int = 3600  # 1 hour


@dataclass
class ValidationConfig:
    """Main validation configuration"""
    
    # Validation rules
    rules: ValidationRules = field(default_factory=ValidationRules)
    
    # AI providers
    ai_providers: AIProviderConfig = field(default_factory=AIProviderConfig)
    
    # Pipeline settings
    pipeline: ValidationPipelineConfig = field(default_factory=ValidationPipelineConfig)
    
    # Output settings
    output_formats: List[str] = field(default_factory=lambda: ['json', 'csv', 'html'])
    output_dir: str = "validation_reports"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "validation.log"
    
    # Environment-specific overrides
    environment: str = "development"
    
    def __post_init__(self):
        """Post-initialization setup"""
        # Create output directory
        Path(self.output_dir).mkdir(exist_ok=True)
        
        # Set environment-specific values
        self._apply_environment_overrides()
    
    def _apply_environment_overrides(self):
        """Apply environment-specific configuration overrides"""
        env = os.getenv('VALIDATION_ENVIRONMENT', self.environment).lower()
        
        if env == 'production':
            self.pipeline.enable_ai_validation = True
            self.pipeline.batch_size = 50
            self.pipeline.max_concurrent_validations = 10
            self.log_level = "WARNING"
            
        elif env == 'staging':
            self.pipeline.enable_ai_validation = True
            self.pipeline.batch_size = 25
            self.pipeline.max_concurrent_validations = 5
            self.log_level = "INFO"
            
        elif env == 'development':
            self.pipeline.enable_ai_validation = True
            self.pipeline.batch_size = 5
            self.pipeline.max_concurrent_validations = 2
            self.log_level = "DEBUG"
            
        elif env == 'testing':
            self.pipeline.enable_ai_validation = False
            self.pipeline.batch_size = 1
            self.pipeline.max_concurrent_validations = 1
            self.log_level = "DEBUG"
    
    @classmethod
    def from_environment(cls) -> 'ValidationConfig':
        """Create configuration from environment variables"""
        config = cls()
        
        # Override with environment variables
        if os.getenv('VALIDATION_ENABLE_AI'):
            config.pipeline.enable_ai_validation = os.getenv('VALIDATION_ENABLE_AI').lower() == 'true'
        
        if os.getenv('VALIDATION_BATCH_SIZE'):
            config.pipeline.batch_size = int(os.getenv('VALIDATION_BATCH_SIZE'))
        
        if os.getenv('VALIDATION_LOG_LEVEL'):
            config.log_level = os.getenv('VALIDATION_LOG_LEVEL')
        
        if os.getenv('VALIDATION_OUTPUT_DIR'):
            config.output_dir = os.getenv('VALIDATION_OUTPUT_DIR')
        
        return config
    
    @classmethod
    def from_file(cls, config_path: str) -> 'ValidationConfig':
        """Create configuration from JSON file"""
        import json
        
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Create config instance
        config = cls()
        
        # Update with file data
        if 'rules' in config_data:
            for key, value in config_data['rules'].items():
                if hasattr(config.rules, key):
                    setattr(config.rules, key, value)
        
        if 'pipeline' in config_data:
            for key, value in config_data['pipeline'].items():
                if hasattr(config.pipeline, key):
                    setattr(config.pipeline, key, value)
        
        if 'ai_providers' in config_data:
            for provider, settings in config_data['ai_providers'].items():
                if hasattr(config.ai_providers, provider):
                    provider_config = getattr(config.ai_providers, provider)
                    for key, value in settings.items():
                        if hasattr(provider_config, key):
                            setattr(provider_config, key, value)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'rules': {
                'required_fields': self.rules.required_fields,
                'optional_fields': self.rules.optional_fields,
                'price_ranges': self.rules.price_ranges,
                'url_patterns': self.rules.url_patterns,
                'data_consistency': self.rules.data_consistency,
                'seller_validation': self.rules.seller_validation,
                'content_validation': self.rules.content_validation
            },
            'ai_providers': {
                'openai': self.ai_providers.openai,
                'anthropic': self.ai_providers.anthropic,
                'google': self.ai_providers.google
            },
            'pipeline': {
                'enable_ai_validation': self.pipeline.enable_ai_validation,
                'enable_rule_validation': self.pipeline.enable_rule_validation,
                'enable_batch_processing': self.pipeline.enable_batch_processing,
                'batch_size': self.pipeline.batch_size,
                'max_concurrent_validations': self.pipeline.max_concurrent_validations,
                'save_reports': self.pipeline.save_reports,
                'reports_dir': self.pipeline.reports_dir,
                'drop_invalid_items': self.pipeline.drop_invalid_items,
                'continue_on_error': self.pipeline.continue_on_error,
                'log_validation_errors': self.pipeline.log_validation_errors,
                'validation_timeout': self.pipeline.validation_timeout,
                'cache_validation_results': self.pipeline.cache_validation_results,
                'cache_ttl': self.pipeline.cache_ttl
            },
            'output_formats': self.output_formats,
            'output_dir': self.output_dir,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'environment': self.environment
        }
    
    def save_to_file(self, config_path: str):
        """Save configuration to JSON file"""
        import json
        
        config_path = Path(config_path)
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


# Default configuration
DEFAULT_CONFIG = ValidationConfig()

# Environment-specific configurations
PRODUCTION_CONFIG = ValidationConfig()
PRODUCTION_CONFIG.environment = "production"
PRODUCTION_CONFIG.pipeline.enable_ai_validation = True
PRODUCTION_CONFIG.pipeline.batch_size = 50
PRODUCTION_CONFIG.pipeline.max_concurrent_validations = 10
PRODUCTION_CONFIG.log_level = "WARNING"

STAGING_CONFIG = ValidationConfig()
STAGING_CONFIG.environment = "staging"
STAGING_CONFIG.pipeline.enable_ai_validation = True
STAGING_CONFIG.pipeline.batch_size = 25
STAGING_CONFIG.pipeline.max_concurrent_validations = 5
STAGING_CONFIG.log_level = "INFO"

DEVELOPMENT_CONFIG = ValidationConfig()
DEVELOPMENT_CONFIG.environment = "development"
DEVELOPMENT_CONFIG.pipeline.enable_ai_validation = True
DEVELOPMENT_CONFIG.pipeline.batch_size = 5
DEVELOPMENT_CONFIG.pipeline.max_concurrent_validations = 2
DEVELOPMENT_CONFIG.log_level = "DEBUG"

TESTING_CONFIG = ValidationConfig()
TESTING_CONFIG.environment = "testing"
TESTING_CONFIG.pipeline.enable_ai_validation = False
TESTING_CONFIG.pipeline.batch_size = 1
TESTING_CONFIG.pipeline.max_concurrent_validations = 1
TESTING_CONFIG.log_level = "DEBUG"


def get_config(environment: str = None) -> ValidationConfig:
    """Get configuration for specified environment"""
    if environment is None:
        environment = os.getenv('VALIDATION_ENVIRONMENT', 'development')
    
    config_map = {
        'production': PRODUCTION_CONFIG,
        'staging': STAGING_CONFIG,
        'development': DEVELOPMENT_CONFIG,
        'testing': TESTING_CONFIG
    }
    
    return config_map.get(environment.lower(), DEFAULT_CONFIG)


def create_config_file(config_path: str = "validation_config.json"):
    """Create a default configuration file"""
    config = DEFAULT_CONFIG
    config.save_to_file(config_path)
    print(f"Configuration file created: {config_path}")
    return config_path
