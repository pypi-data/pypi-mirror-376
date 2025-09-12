"""
Configuration models for D3 Identity Service client
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from enum import Enum
from dataclasses_json import dataclass_json, LetterCase

class LogLevel(Enum):
    """Logging level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class CacheType(Enum):
    """Cache implementation type"""
    MEMORY = "memory"
    REDIS = "redis"
    HYBRID = "hybrid"  # Memory with Redis backup

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class EtcdConfiguration:
    """etcd connection configuration"""
    endpoints: List[str] = field(default_factory=lambda: ["localhost:2379"])
    username: Optional[str] = None
    password: Optional[str] = None
    ca_cert: Optional[str] = None  # Path to CA certificate file
    cert_cert: Optional[str] = None  # Path to client certificate file
    cert_key: Optional[str] = None  # Path to client private key file
    timeout: int = 30  # Connection timeout in seconds
    grpc_keepalive_time_ms: int = 30000  # gRPC keepalive time
    grpc_keepalive_timeout_ms: int = 5000  # gRPC keepalive timeout
    grpc_keepalive_permit_without_calls: bool = True
    grpc_http2_max_pings_without_data: int = 0
    grpc_http2_min_time_between_pings_ms: int = 10000
    grpc_http2_min_ping_interval_without_data_ms: int = 300000
    
    def has_tls(self) -> bool:
        """Check if TLS is configured"""
        return any([self.ca_cert, self.cert_cert, self.cert_key])
    
    def has_authentication(self) -> bool:
        """Check if authentication is configured"""
        return self.username is not None and self.password is not None
    
    def get_endpoint_urls(self) -> List[str]:
        """Get properly formatted endpoint URLs"""
        formatted_endpoints = []
        for endpoint in self.endpoints:
            if not endpoint.startswith(('http://', 'https://')):
                # Default to http if no scheme specified
                endpoint = f"http://{endpoint}"
            formatted_endpoints.append(endpoint)
        return formatted_endpoints

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class CacheConfiguration:
    """Cache configuration settings"""
    cache_type: CacheType = CacheType.MEMORY
    tenant_info_ttl_minutes: int = 10  # Tenant info cache TTL
    jwt_validation_ttl_minutes: int = 5  # JWT validation cache TTL
    configuration_ttl_minutes: int = 15  # Configuration cache TTL
    max_cache_size: int = 1000  # Maximum number of cached items
    
    # Redis-specific settings (if cache_type is REDIS or HYBRID)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_ssl: bool = False
    redis_connection_pool_size: int = 10
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        protocol = "rediss" if self.redis_ssl else "redis"
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SecurityConfiguration:
    """Security and cryptography configuration"""
    jwt_audience_validation: bool = True  # Validate JWT audience
    jwt_issuer_validation: bool = True  # Validate JWT issuer
    jwt_expiration_validation: bool = True  # Validate JWT expiration
    jwt_clock_skew_seconds: int = 300  # Allow 5 minutes clock skew
    
    # Key rotation settings
    key_rotation_check_interval_minutes: int = 15  # How often to check for key rotation
    key_validation_cache_minutes: int = 5  # How long to cache key validation results
    
    # Encryption settings
    private_key_encryption_algorithm: str = "AES-256-GCM"
    pbkdf2_iterations: int = 100000  # PBKDF2 iterations for key derivation
    
    # Rate limiting
    enable_rate_limiting: bool = True
    default_rate_limit_requests_per_minute: int = 100
    
    def get_allowed_clock_skew_seconds(self) -> int:
        """Get allowed clock skew for JWT validation"""
        return self.jwt_clock_skew_seconds if self.jwt_expiration_validation else 0

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ServiceConfiguration:
    """Service-specific configuration"""
    service_name: str
    service_version: str = "1.0.0"
    environment: str = "production"  # development, staging, production
    
    # Service endpoints
    http_port: int = 8080
    grpc_port: int = 50051
    health_check_path: str = "/health"
    metrics_path: str = "/metrics"
    
    # Registration settings
    enable_service_registration: bool = True
    registration_retry_attempts: int = 3
    registration_retry_delay_seconds: int = 5
    
    # Health check settings
    health_check_interval_seconds: int = 30
    health_check_timeout_seconds: int = 5
    
    def get_http_url(self, host: str = "localhost") -> str:
        """Get HTTP service URL"""
        return f"http://{host}:{self.http_port}"
    
    def get_grpc_url(self, host: str = "localhost") -> str:
        """Get gRPC service URL"""
        return f"grpc://{host}:{self.grpc_port}"
    
    def get_health_check_url(self, host: str = "localhost") -> str:
        """Get health check URL"""
        return f"http://{host}:{self.http_port}{self.health_check_path}"

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class LoggingConfiguration:
    """Logging configuration"""
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_to_console: bool = True
    log_to_file: bool = False
    log_file_path: Optional[str] = None
    log_file_max_size_mb: int = 100
    log_file_backup_count: int = 5
    
    # Structured logging
    enable_json_logging: bool = False
    include_tenant_context: bool = True
    include_request_id: bool = True
    
    # Sensitive data filtering
    mask_sensitive_data: bool = True
    sensitive_fields: List[str] = field(default_factory=lambda: [
        "password", "api_key", "private_key", "secret", "token", "authorization"
    ])

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class IdentityServiceOptions:
    """Complete configuration options for D3 Identity Service client"""
    # Core configuration
    tenant_guid: Optional[str] = None
    api_key: Optional[str] = None
    jwt_token: Optional[str] = None  # For initialization via JWT
    
    # Component configurations
    etcd: EtcdConfiguration = field(default_factory=EtcdConfiguration)
    cache: CacheConfiguration = field(default_factory=CacheConfiguration)
    security: SecurityConfiguration = field(default_factory=SecurityConfiguration)
    service: Optional[ServiceConfiguration] = None
    logging: LoggingConfiguration = field(default_factory=LoggingConfiguration)
    
    # Feature flags
    enable_tenant_watching: bool = True
    enable_configuration_caching: bool = True
    enable_automatic_key_rotation: bool = True
    enable_service_discovery: bool = True
    enable_health_checks: bool = True
    
    # Advanced settings
    initialization_timeout_seconds: int = 30
    graceful_shutdown_timeout_seconds: int = 10
    max_concurrent_requests: int = 100
    request_timeout_seconds: int = 30
    
    # Development/debug settings
    debug_mode: bool = False
    trace_requests: bool = False
    mock_etcd_for_testing: bool = False
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of validation errors"""
        errors = []
        
        # Check required fields for normal operation
        if not self.mock_etcd_for_testing and not self.etcd.endpoints:
            errors.append("etcd.endpoints is required")
        
        # Validate cache configuration
        if self.cache.cache_type == CacheType.REDIS:
            if not self.cache.redis_host:
                errors.append("cache.redis_host is required when using Redis cache")
        
        # Validate service configuration if provided
        if self.service:
            if not self.service.service_name:
                errors.append("service.service_name is required when service configuration is provided")
        
        # Validate tenant identification
        if not any([self.tenant_guid, self.jwt_token]):
            errors.append("Either tenant_guid or jwt_token must be provided for tenant identification")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if configuration is valid"""
        return len(self.validate()) == 0
    
    def get_tenant_identification(self) -> Dict[str, Optional[str]]:
        """Get tenant identification information"""
        return {
            "tenant_guid": self.tenant_guid,
            "api_key": self.api_key,
            "jwt_token": self.jwt_token
        }

# Utility functions for configuration
def create_development_config(
    tenant_guid: str,
    api_key: str,
    service_name: str = "TestService"
) -> IdentityServiceOptions:
    """Create development configuration with debugging enabled"""
    config = IdentityServiceOptions()
    config.tenant_guid = tenant_guid
    config.api_key = api_key
    config.debug_mode = True
    config.logging.log_level = LogLevel.DEBUG
    config.logging.log_to_console = True
    config.service = ServiceConfiguration(service_name=service_name, environment="development")
    return config

def create_production_config(
    tenant_guid: str,
    api_key: str,
    etcd_endpoints: List[str],
    service_name: str,
    redis_host: Optional[str] = None
) -> IdentityServiceOptions:
    """Create production configuration with optimal settings"""
    config = IdentityServiceOptions()
    config.tenant_guid = tenant_guid
    config.api_key = api_key
    config.etcd.endpoints = etcd_endpoints
    config.logging.log_level = LogLevel.INFO
    config.logging.enable_json_logging = True
    config.service = ServiceConfiguration(service_name=service_name, environment="production")
    
    if redis_host:
        config.cache.cache_type = CacheType.HYBRID
        config.cache.redis_host = redis_host
    
    return config