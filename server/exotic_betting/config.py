"""
Configuration module for Exotic Bet Optimizer
=============================================

Centralized configuration management for all optimizer components
"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class OptimizationConfig:
    """Configuration for optimization parameters"""
    
    # Probability calibration
    market_efficiency_factor: float = 0.85
    model_weight: float = 0.7
    market_weight: float = 0.3
    
    # Combination generation
    min_probability_threshold: float = 0.001
    max_exacta_combinations: int = 20
    max_trifecta_combinations: int = 15
    max_superfecta_combinations: int = 10
    
    # EV signal generation
    min_ev_threshold: float = 0.05
    max_kelly_fraction: float = 0.25
    confidence_weight: float = 0.35
    
    # Risk management
    max_daily_exposure: float = 1000.0
    max_per_bet_exposure: float = 100.0
    
    # Performance tracking
    performance_window_days: int = 30
    min_confidence_threshold: float = 0.5


@dataclass
class DatabaseConfig:
    """Database configuration"""
    
    url: str = "sqlite:///exotic_bet_optimizer.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class APIConfig:
    """API configuration"""
    
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = True
    cors_origins: str = "*"
    rate_limit: str = "100/hour"
    timeout_seconds: int = 30


class ConfigManager:
    """Central configuration manager"""
    
    def __init__(self):
        self.optimization = self._load_optimization_config()
        self.database = self._load_database_config()
        self.api = self._load_api_config()
    
    def _load_optimization_config(self) -> OptimizationConfig:
        """Load optimization configuration from environment or defaults"""
        return OptimizationConfig(
            market_efficiency_factor=float(os.getenv('MARKET_EFFICIENCY_FACTOR', 0.85)),
            model_weight=float(os.getenv('MODEL_WEIGHT', 0.7)),
            market_weight=float(os.getenv('MARKET_WEIGHT', 0.3)),
            min_probability_threshold=float(os.getenv('MIN_PROBABILITY_THRESHOLD', 0.001)),
            max_exacta_combinations=int(os.getenv('MAX_EXACTA_COMBINATIONS', 20)),
            max_trifecta_combinations=int(os.getenv('MAX_TRIFECTA_COMBINATIONS', 15)),
            max_superfecta_combinations=int(os.getenv('MAX_SUPERFECTA_COMBINATIONS', 10)),
            min_ev_threshold=float(os.getenv('MIN_EV_THRESHOLD', 0.05)),
            max_kelly_fraction=float(os.getenv('MAX_KELLY_FRACTION', 0.25)),
            confidence_weight=float(os.getenv('CONFIDENCE_WEIGHT', 0.35)),
            max_daily_exposure=float(os.getenv('MAX_DAILY_EXPOSURE', 1000.0)),
            max_per_bet_exposure=float(os.getenv('MAX_PER_BET_EXPOSURE', 100.0)),
            performance_window_days=int(os.getenv('PERFORMANCE_WINDOW_DAYS', 30)),
            min_confidence_threshold=float(os.getenv('MIN_CONFIDENCE_THRESHOLD', 0.5))
        )
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration from environment or defaults"""
        return DatabaseConfig(
            url=os.getenv('DATABASE_URL', 'sqlite:///exotic_bet_optimizer.db'),
            echo=os.getenv('DATABASE_ECHO', 'False').lower() == 'true',
            pool_size=int(os.getenv('DATABASE_POOL_SIZE', 10)),
            max_overflow=int(os.getenv('DATABASE_MAX_OVERFLOW', 20)),
            pool_timeout=int(os.getenv('DATABASE_POOL_TIMEOUT', 30)),
            pool_recycle=int(os.getenv('DATABASE_POOL_RECYCLE', 3600))
        )
    
    def _load_api_config(self) -> APIConfig:
        """Load API configuration from environment or defaults"""
        return APIConfig(
            host=os.getenv('API_HOST', '0.0.0.0'),
            port=int(os.getenv('API_PORT', 5000)),
            debug=os.getenv('API_DEBUG', 'True').lower() == 'true',
            cors_origins=os.getenv('CORS_ORIGINS', '*'),
            rate_limit=os.getenv('RATE_LIMIT', '100/hour'),
            timeout_seconds=int(os.getenv('API_TIMEOUT_SECONDS', 30))
        )
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get complete configuration as dictionary"""
        return {
            'optimization': {
                'market_efficiency_factor': self.optimization.market_efficiency_factor,
                'model_weight': self.optimization.model_weight,
                'market_weight': self.optimization.market_weight,
                'min_probability_threshold': self.optimization.min_probability_threshold,
                'max_exacta_combinations': self.optimization.max_exacta_combinations,
                'max_trifecta_combinations': self.optimization.max_trifecta_combinations,
                'max_superfecta_combinations': self.optimization.max_superfecta_combinations,
                'min_ev_threshold': self.optimization.min_ev_threshold,
                'max_kelly_fraction': self.optimization.max_kelly_fraction,
                'confidence_weight': self.optimization.confidence_weight,
                'max_daily_exposure': self.optimization.max_daily_exposure,
                'max_per_bet_exposure': self.optimization.max_per_bet_exposure,
                'performance_window_days': self.optimization.performance_window_days,
                'min_confidence_threshold': self.optimization.min_confidence_threshold
            },
            'database': {
                'url': self.database.url,
                'echo': self.database.echo,
                'pool_size': self.database.pool_size,
                'max_overflow': self.database.max_overflow,
                'pool_timeout': self.database.pool_timeout,
                'pool_recycle': self.database.pool_recycle
            },
            'api': {
                'host': self.api.host,
                'port': self.api.port,
                'debug': self.api.debug,
                'cors_origins': self.api.cors_origins,
                'rate_limit': self.api.rate_limit,
                'timeout_seconds': self.api.timeout_seconds
            }
        }
    
    def update_optimization_config(self, **kwargs):
        """Update optimization configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.optimization, key):
                setattr(self.optimization, key, value)
    
    def validate_config(self) -> bool:
        """Validate configuration parameters"""
        errors = []
        
        # Validate optimization config
        opt = self.optimization
        if not 0 < opt.market_efficiency_factor <= 1:
            errors.append("market_efficiency_factor must be between 0 and 1")
        
        if abs(opt.model_weight + opt.market_weight - 1.0) > 0.001:
            errors.append("model_weight and market_weight must sum to 1.0")
        
        if opt.min_ev_threshold < 0:
            errors.append("min_ev_threshold must be non-negative")
        
        if not 0 < opt.max_kelly_fraction <= 1:
            errors.append("max_kelly_fraction must be between 0 and 1")
        
        # Validate database config
        if not self.database.url:
            errors.append("Database URL must be provided")
        
        # Validate API config
        if not 1 <= self.api.port <= 65535:
            errors.append("API port must be between 1 and 65535")
        
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True


# Global configuration instance
config = ConfigManager()


# Environment-specific configurations
ENVIRONMENTS = {
    'development': {
        'database_url': 'sqlite:///exotic_bet_optimizer_dev.db',
        'api_debug': True,
        'min_ev_threshold': 0.03,  # Lower threshold for testing
    },
    'testing': {
        'database_url': 'sqlite:///:memory:',
        'api_debug': False,
        'min_ev_threshold': 0.01,  # Very low threshold for testing
    },
    'production': {
        'database_url': os.getenv('PRODUCTION_DATABASE_URL', 'postgresql://localhost/exotic_bet_optimizer'),
        'api_debug': False,
        'min_ev_threshold': 0.08,  # Higher threshold for production
        'max_kelly_fraction': 0.15,  # Conservative Kelly for production
    }
}


def load_environment_config(env: str = 'development'):
    """Load configuration for specific environment"""
    if env not in ENVIRONMENTS:
        raise ValueError(f"Unknown environment: {env}. Available: {list(ENVIRONMENTS.keys())}")
    
    env_config = ENVIRONMENTS[env]
    
    # Update configuration
    if 'database_url' in env_config:
        config.database.url = env_config['database_url']
    
    if 'api_debug' in env_config:
        config.api.debug = env_config['api_debug']
    
    if 'min_ev_threshold' in env_config:
        config.optimization.min_ev_threshold = env_config['min_ev_threshold']
    
    if 'max_kelly_fraction' in env_config:
        config.optimization.max_kelly_fraction = env_config['max_kelly_fraction']
    
    print(f"Configuration loaded for environment: {env}")
    return config


if __name__ == "__main__":
    # Test configuration
    print("🔧 Configuration Test")
    print("=" * 30)
    
    # Load development config
    dev_config = load_environment_config('development')
    
    # Validate configuration
    is_valid = dev_config.validate_config()
    print(f"Configuration valid: {is_valid}")
    
    # Display configuration
    config_dict = dev_config.get_config_dict()
    print("\nConfiguration Summary:")
    for section, params in config_dict.items():
        print(f"\n{section.upper()}:")
        for key, value in params.items():
            print(f"  {key}: {value}")
    
    print("\n✅ Configuration module test complete!")