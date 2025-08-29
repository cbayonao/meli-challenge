# Configuración de validación con OpenAI para Meli Challenge
# Archivo: validation_config.py

VALIDATION_CONFIG = {
    # Configuración general
    'enable_ai': True,
    'model': 'gpt-4',
    'batch_size': 5,
    'save_reports': True,
    'reports_dir': 'validation_reports',
    'log_level': 'INFO',
    
    # Configuración de OpenAI
    'openai': {
        'model': 'gpt-4',
        'fallback_model': 'gpt-3.5-turbo',
        'max_tokens': 2000,
        'temperature': 0.1,
        'timeout': 30,
        'max_retries': 3
    },
    
    # Configuración de validación
    'validation': {
        'drop_invalid_items': False,
        'enable_basic_validation': True,
        'enable_ai_validation': True,
        'save_detailed_reports': True,
        'generate_recommendations': True
    },
    
    # Configuración de rate limiting
    'rate_limiting': {
        'enable': True,
        'max_requests_per_minute': 60,
        'max_requests_per_hour': 1000,
        'retry_on_error': True,
        'exponential_backoff': True
    },
    
    # Configuración de reportes
    'reports': {
        'formats': ['json', 'csv', 'html'],
        'include_ai_analysis': True,
        'include_recommendations': True,
        'include_statistics': True,
        'auto_generate_summary': True
    }
}

# Configuración específica para diferentes entornos
VALIDATION_CONFIG_DEV = {
    **VALIDATION_CONFIG,
    'log_level': 'DEBUG',
    'batch_size': 3,
    'save_reports': True,
    'openai': {
        **VALIDATION_CONFIG['openai'],
        'model': 'gpt-3.5-turbo'  # Modelo más barato para desarrollo
    }
}

VALIDATION_CONFIG_PROD = {
    **VALIDATION_CONFIG,
    'log_level': 'INFO',
    'batch_size': 10,
    'save_reports': True,
    'openai': {
        **VALIDATION_CONFIG['openai'],
        'model': 'gpt-4'  # Modelo más preciso para producción
    }
}

# Función para obtener configuración según el entorno
def get_validation_config(environment='default'):
    """Obtener configuración de validación según el entorno"""
    configs = {
        'default': VALIDATION_CONFIG,
        'dev': VALIDATION_CONFIG_DEV,
        'development': VALIDATION_CONFIG_DEV,
        'prod': VALIDATION_CONFIG_PROD,
        'production': VALIDATION_CONFIG_PROD
    }
    return configs.get(environment, VALIDATION_CONFIG)

# Función para validar configuración
def validate_config(config):
    """Validar que la configuración sea correcta"""
    required_keys = ['enable_ai', 'model', 'batch_size']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Configuración requerida faltante: {key}")
    
    if config['enable_ai'] and 'openai' not in config:
        raise ValueError("Configuración de OpenAI requerida cuando enable_ai=True")
    
    return True

# Función para imprimir configuración
def print_config(config, title="Configuración de Validación"):
    """Imprimir configuración de manera legible"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")
    
    for key, value in config.items():
        if isinstance(value, dict):
            print(f"\n📁 {key.upper()}:")
            for sub_key, sub_value in value.items():
                print(f"  • {sub_key}: {sub_value}")
        else:
            print(f"• {key}: {value}")
    
    print(f"\n{'='*60}")

if __name__ == "__main__":
    # Mostrar configuraciones disponibles
    print("🔧 CONFIGURACIONES DISPONIBLES:")
    print("1. default - Configuración estándar")
    print("2. dev/development - Configuración para desarrollo")
    print("3. prod/production - Configuración para producción")
    
    # Mostrar configuración por defecto
    print_config(VALIDATION_CONFIG)
    
    # Mostrar configuración de desarrollo
    print_config(VALIDATION_CONFIG_DEV, "Configuración de Desarrollo")
    
    # Mostrar configuración de producción
    print_config(VALIDATION_CONFIG_PROD, "Configuración de Producción")
