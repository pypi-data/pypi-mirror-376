"""
Configuration utilities for D3 Identity Service client
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from ..models.config import (
    IdentityServiceOptions, EtcdConfiguration, CacheConfiguration, 
    SecurityConfiguration, ServiceConfiguration, LoggingConfiguration,
    CacheType, LogLevel
)

logger = logging.getLogger(__name__)

class IdentityClientConfig:
    """
    Configuration manager for D3 Identity Service client
    """
    
    @staticmethod
    def load_from_environment() -> IdentityServiceOptions:
        """
        Load configuration from environment variables
        
        Returns:
            IdentityServiceOptions with environment-based configuration
        """
        try:
            # Core configuration
            tenant_guid = os.getenv('D3_TENANT_GUID')
            api_key = os.getenv('D3_API_KEY')
            jwt_token = os.getenv('D3_JWT_TOKEN')
            
            # etcd configuration
            etcd_endpoints = os.getenv('ETCD_ENDPOINTS', 'localhost:2379').split(',')
            etcd_username = os.getenv('ETCD_USERNAME')
            etcd_password = os.getenv('ETCD_PASSWORD')
            etcd_ca_cert = os.getenv('ETCD_CA_CERT')
            etcd_cert_cert = os.getenv('ETCD_CERT_CERT')
            etcd_cert_key = os.getenv('ETCD_CERT_KEY')
            etcd_timeout = int(os.getenv('ETCD_TIMEOUT', '30'))
            
            etcd_config = EtcdConfiguration(
                endpoints=etcd_endpoints,
                username=etcd_username,
                password=etcd_password,
                ca_cert=etcd_ca_cert,
                cert_cert=etcd_cert_cert,
                cert_key=etcd_cert_key,
                timeout=etcd_timeout
            )
            
            # Cache configuration
            cache_type_str = os.getenv('CACHE_TYPE', 'memory').lower()
            cache_type = CacheType.MEMORY
            
            if cache_type_str == 'redis':
                cache_type = CacheType.REDIS
            elif cache_type_str == 'hybrid':
                cache_type = CacheType.HYBRID
            
            cache_config = CacheConfiguration(
                cache_type=cache_type,
                tenant_info_ttl_minutes=int(os.getenv('CACHE_TENANT_TTL_MINUTES', '10')),
                jwt_validation_ttl_minutes=int(os.getenv('CACHE_JWT_TTL_MINUTES', '5')),
                configuration_ttl_minutes=int(os.getenv('CACHE_CONFIG_TTL_MINUTES', '15')),
                max_cache_size=int(os.getenv('CACHE_MAX_SIZE', '1000')),
                redis_host=os.getenv('REDIS_HOST', 'localhost'),
                redis_port=int(os.getenv('REDIS_PORT', '6379')),
                redis_db=int(os.getenv('REDIS_DB', '0')),
                redis_password=os.getenv('REDIS_PASSWORD'),
                redis_ssl=os.getenv('REDIS_SSL', 'false').lower() == 'true'
            )
            
            # Security configuration
            security_config = SecurityConfiguration(
                jwt_audience_validation=os.getenv('JWT_VALIDATE_AUDIENCE', 'true').lower() == 'true',
                jwt_issuer_validation=os.getenv('JWT_VALIDATE_ISSUER', 'true').lower() == 'true',
                jwt_expiration_validation=os.getenv('JWT_VALIDATE_EXPIRATION', 'true').lower() == 'true',
                jwt_clock_skew_seconds=int(os.getenv('JWT_CLOCK_SKEW_SECONDS', '300')),
                enable_rate_limiting=os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true'
            )
            
            # Service configuration (optional)
            service_config = None
            service_name = os.getenv('SERVICE_NAME')
            if service_name:
                service_config = ServiceConfiguration(
                    service_name=service_name,
                    service_version=os.getenv('SERVICE_VERSION', '1.0.0'),
                    environment=os.getenv('ENVIRONMENT', 'production'),
                    http_port=int(os.getenv('HTTP_PORT', '8080')),
                    grpc_port=int(os.getenv('GRPC_PORT', '50051')),
                    enable_service_registration=os.getenv('ENABLE_SERVICE_REGISTRATION', 'true').lower() == 'true'
                )
            
            # Logging configuration
            log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
            log_level = LogLevel.INFO
            
            try:
                log_level = LogLevel(log_level_str)
            except ValueError:
                logger.warning(f"Invalid log level '{log_level_str}', using INFO")
            
            logging_config = LoggingConfiguration(
                log_level=log_level,
                log_to_console=os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true',
                log_to_file=os.getenv('LOG_TO_FILE', 'false').lower() == 'true',
                log_file_path=os.getenv('LOG_FILE_PATH'),
                enable_json_logging=os.getenv('ENABLE_JSON_LOGGING', 'false').lower() == 'true'
            )
            
            # Feature flags
            enable_tenant_watching = os.getenv('ENABLE_TENANT_WATCHING', 'true').lower() == 'true'
            enable_configuration_caching = os.getenv('ENABLE_CONFIGURATION_CACHING', 'true').lower() == 'true'
            enable_automatic_key_rotation = os.getenv('ENABLE_AUTOMATIC_KEY_ROTATION', 'true').lower() == 'true'
            enable_service_discovery = os.getenv('ENABLE_SERVICE_DISCOVERY', 'true').lower() == 'true'
            enable_health_checks = os.getenv('ENABLE_HEALTH_CHECKS', 'true').lower() == 'true'
            
            # Debug settings
            debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
            mock_etcd_for_testing = os.getenv('MOCK_ETCD_FOR_TESTING', 'false').lower() == 'true'
            
            # Create configuration
            config = IdentityServiceOptions(
                tenant_guid=tenant_guid,
                api_key=api_key,
                jwt_token=jwt_token,
                etcd=etcd_config,
                cache=cache_config,
                security=security_config,
                service=service_config,
                logging=logging_config,
                enable_tenant_watching=enable_tenant_watching,
                enable_configuration_caching=enable_configuration_caching,
                enable_automatic_key_rotation=enable_automatic_key_rotation,
                enable_service_discovery=enable_service_discovery,
                enable_health_checks=enable_health_checks,
                debug_mode=debug_mode,
                mock_etcd_for_testing=mock_etcd_for_testing
            )
            
            logger.info("Configuration loaded from environment variables")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration from environment: {e}")
            raise
    
    @staticmethod
    def load_from_file(config_file_path: str) -> IdentityServiceOptions:
        """
        Load configuration from JSON file
        
        Args:
            config_file_path: Path to JSON configuration file
            
        Returns:
            IdentityServiceOptions with file-based configuration
        """
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Convert JSON to configuration object
            config = IdentityServiceOptions.from_dict(config_data)
            
            logger.info(f"Configuration loaded from file: {config_file_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration from file {config_file_path}: {e}")
            raise
    
    @staticmethod
    def create_development_config(
        tenant_guid: str,
        api_key: str,
        service_name: str = "DevelopmentService",
        etcd_endpoints: Optional[List[str]] = None
    ) -> IdentityServiceOptions:
        """
        Create development configuration with sensible defaults
        
        Args:
            tenant_guid: Tenant GUID for development
            api_key: Tenant API key
            service_name: Development service name
            etcd_endpoints: etcd endpoints (defaults to localhost)
            
        Returns:
            IdentityServiceOptions configured for development
        """
        etcd_config = EtcdConfiguration(
            endpoints=etcd_endpoints or ['localhost:2379'],
            timeout=10
        )
        
        cache_config = CacheConfiguration(
            cache_type=CacheType.MEMORY,
            tenant_info_ttl_minutes=5,
            jwt_validation_ttl_minutes=2,
            max_cache_size=100
        )
        
        security_config = SecurityConfiguration(
            jwt_clock_skew_seconds=60,
            enable_rate_limiting=False
        )
        
        service_config = ServiceConfiguration(
            service_name=service_name,
            environment="development",
            enable_service_registration=True
        )
        
        logging_config = LoggingConfiguration(
            log_level=LogLevel.DEBUG,
            log_to_console=True,
            include_tenant_context=True
        )
        
        config = IdentityServiceOptions(
            tenant_guid=tenant_guid,
            api_key=api_key,
            etcd=etcd_config,
            cache=cache_config,
            security=security_config,
            service=service_config,
            logging=logging_config,
            debug_mode=True,
            enable_tenant_watching=True,
            enable_configuration_caching=True
        )
        
        return config
    
    @staticmethod
    def create_production_config(
        tenant_guid: str,
        api_key: str,
        service_name: str,
        etcd_endpoints: List[str],
        redis_host: Optional[str] = None
    ) -> IdentityServiceOptions:
        """
        Create production configuration with optimal settings
        
        Args:
            tenant_guid: Tenant GUID for production
            api_key: Tenant API key  
            service_name: Production service name
            etcd_endpoints: etcd cluster endpoints
            redis_host: Redis host for caching (optional)
            
        Returns:
            IdentityServiceOptions configured for production
        """
        etcd_config = EtcdConfiguration(
            endpoints=etcd_endpoints,
            timeout=30,
            grpc_keepalive_time_ms=30000
        )
        
        cache_type = CacheType.HYBRID if redis_host else CacheType.MEMORY
        cache_config = CacheConfiguration(
            cache_type=cache_type,
            tenant_info_ttl_minutes=10,
            jwt_validation_ttl_minutes=5,
            max_cache_size=1000,
            redis_host=redis_host or 'localhost'
        )
        
        security_config = SecurityConfiguration(
            jwt_audience_validation=True,
            jwt_issuer_validation=True,
            jwt_expiration_validation=True,
            enable_rate_limiting=True
        )
        
        service_config = ServiceConfiguration(
            service_name=service_name,
            environment="production",
            enable_service_registration=True,
            health_check_interval_seconds=30
        )
        
        logging_config = LoggingConfiguration(
            log_level=LogLevel.INFO,
            log_to_console=True,
            enable_json_logging=True,
            include_tenant_context=True,
            mask_sensitive_data=True
        )
        
        config = IdentityServiceOptions(
            tenant_guid=tenant_guid,
            api_key=api_key,
            etcd=etcd_config,
            cache=cache_config,
            security=security_config,
            service=service_config,
            logging=logging_config,
            debug_mode=False,
            enable_tenant_watching=True,
            enable_configuration_caching=True,
            enable_automatic_key_rotation=True,
            enable_service_discovery=True,
            enable_health_checks=True
        )
        
        return config

def load_config_from_environment() -> IdentityServiceOptions:
    """
    Convenience function to load configuration from environment
    
    Returns:
        IdentityServiceOptions from environment variables
    """
    return IdentityClientConfig.load_from_environment()

def validate_configuration(config: IdentityServiceOptions) -> List[str]:
    """
    Validate configuration and return list of issues
    
    Args:
        config: Configuration to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    return config.validate()

def create_development_config(
    tenant_guid: str,
    api_key: str,
    service_name: str,
    etcd_endpoints: List[str] = None
) -> IdentityServiceOptions:
    """
    Create development configuration
    
    Args:
        tenant_guid: Tenant GUID
        api_key: Tenant API key
        service_name: Service name
        etcd_endpoints: etcd endpoints
        
    Returns:
        IdentityServiceOptions for development
    """
    return IdentityClientConfig.create_development_config(
        tenant_guid, api_key, service_name, etcd_endpoints
    )

def create_production_config(
    tenant_guid: str,
    api_key: str,
    service_name: str,
    etcd_endpoints: List[str],
    redis_host: Optional[str] = None
) -> IdentityServiceOptions:
    """
    Create production configuration
    
    Args:
        tenant_guid: Tenant GUID
        api_key: Tenant API key
        service_name: Service name
        etcd_endpoints: etcd endpoints
        redis_host: Redis host
        
    Returns:
        IdentityServiceOptions for production
    """
    return IdentityClientConfig.create_production_config(
        tenant_guid, api_key, service_name, etcd_endpoints, redis_host
    )