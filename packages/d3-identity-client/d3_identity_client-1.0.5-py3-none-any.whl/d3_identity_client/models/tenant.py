"""
Tenant data models for D3 Identity Service
These models mirror the C# SDK models for consistency
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from datetime import datetime
from enum import Enum
import json
from dataclasses_json import dataclass_json, LetterCase

class TenantType(Enum):
    """Tenant type enumeration"""
    VSOC = "Vsoc"
    INTERNAL = "Internal"

class TenantStatus(Enum):
    """Tenant status enumeration"""
    ACTIVE = "Active"
    INACTIVE = "Inactive" 
    SUSPENDED = "Suspended"
    PENDING = "Pending"
    OFFBOARD = "Offboard"

class InternalServices(Enum):
    """Internal service names enumeration"""
    COMMAND_SERVICE = "CommandService"
    PLAYBOOK_SERVICE = "PlaybookService"
    VISUALIZATION_SERVICE = "VisualizationService"
    NOTIFICATION_SERVICE = "NotificationService"
    REPORTING_SERVICE = "ReportingService"
    INTEGRATION_SERVICE = "IntegrationService"
    AUDIT_SERVICE = "AuditService"

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TenantKeyPair:
    """Tenant cryptographic key pair for JWT signing and encryption"""
    key_id: str
    key_usage: str  # "JWT", "DataEncryption", "Communication"
    public_key: str  # Base64 encoded Ed25519 public key or PEM format
    encrypted_private_key: str  # AES-256-GCM encrypted private key
    algorithm: str = "EdDSA"  # Algorithm used (EdDSA for Ed25519)
    is_primary: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    version: int = 1

    def is_jwt_key(self) -> bool:
        """Check if this is a JWT signing key"""
        return self.key_usage == "JWT"
    
    def is_valid(self) -> bool:
        """Check if key pair is valid and not expired"""
        if not self.is_active:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass 
class EndpointConfig:
    """Service endpoint configuration"""
    url: str
    protocols: str  # "Http1", "Http2", "Http1AndHttp2"

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TenantEndpoints:
    """Tenant service endpoints configuration"""
    http: Optional[EndpointConfig] = None
    grpc: Optional[EndpointConfig] = None

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class RateLimitBucketConfiguration:
    """Rate limiting configuration using token bucket algorithm"""
    capacity: int  # Maximum tokens in bucket
    refill_tokens: int  # Tokens added per refill period
    refill_period_seconds: int  # Refill period in seconds
    tokens_per_request: int = 1  # Tokens consumed per request
    enabled: bool = True
    description: Optional[str] = None
    custom_options: Optional[Dict[str, str]] = None

    def tokens_per_minute(self) -> float:
        """Calculate tokens per minute based on refill rate"""
        return (self.refill_tokens * 60) / self.refill_period_seconds

    def max_requests_per_minute(self) -> float:
        """Calculate maximum requests per minute"""
        return self.tokens_per_minute() / self.tokens_per_request

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TenantInfo:
    """Complete tenant information model matching C# SDK EtcdTenantInfo"""
    # Identity fields
    tenant_guid: str
    tenant_name: str
    tenant_id: int
    
    # Security & Keys
    key_pairs: Dict[str, TenantKeyPair] = field(default_factory=dict)
    api_key: Optional[str] = None
    
    # Status & Configuration
    active: bool = True
    status: TenantStatus = TenantStatus.ACTIVE
    tenant_type: TenantType = TenantType.VSOC
    
    # Service Endpoints
    endpoints: Optional[TenantEndpoints] = None
    
    # JWT Configuration
    jwt_expiration_minutes: int = 1440  # 24 hours default
    
    # Tenant Limits
    max_users: int = 100
    max_sites: int = 50
    
    # Rate Limiting
    rate_limit_configurations: Optional[Dict[str, RateLimitBucketConfiguration]] = None
    
    # Advanced Configuration (flexible key-value store)
    configurations: Optional[Dict[str, Any]] = None
    
    # Hierarchy Support
    parent_tenant_guid: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_token_refresh: Optional[datetime] = None
    version: int = 1

    def __post_init__(self):
        """Post-initialization to ensure proper types"""
        # Convert string enums to proper enum types if needed
        if isinstance(self.status, str):
            self.status = TenantStatus(self.status)
        if isinstance(self.tenant_type, str):
            self.tenant_type = TenantType(self.tenant_type)
        
        # Ensure key_pairs is properly typed
        if self.key_pairs:
            typed_pairs = {}
            for key_id, key_pair in self.key_pairs.items():
                if isinstance(key_pair, dict):
                    typed_pairs[key_id] = TenantKeyPair.from_dict(key_pair)
                else:
                    typed_pairs[key_id] = key_pair
            self.key_pairs = typed_pairs

    def get_primary_jwt_key_pair(self) -> Optional[TenantKeyPair]:
        """Get the primary JWT key pair for token signing"""
        for key_pair in self.key_pairs.values():
            if (key_pair.is_primary and 
                key_pair.is_jwt_key() and 
                key_pair.is_valid()):
                return key_pair
        return None

    def get_valid_jwt_key_pairs(self) -> List[TenantKeyPair]:
        """Get all valid JWT key pairs for token validation"""
        valid_keys = []
        for key_pair in self.key_pairs.values():
            if key_pair.is_jwt_key() and key_pair.is_valid():
                valid_keys.append(key_pair)
        return sorted(valid_keys, key=lambda x: x.is_primary, reverse=True)

    def get_configuration(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key with optional default"""
        if not self.configurations:
            return default
        return self.configurations.get(key, default)
    
    def set_configuration(self, key: str, value: Any) -> None:
        """Set configuration value"""
        if not self.configurations:
            self.configurations = {}
        self.configurations[key] = value

    def get_rate_limit_config(self, limit_name: str) -> Optional[RateLimitBucketConfiguration]:
        """Get rate limit configuration by name"""
        if not self.rate_limit_configurations:
            return None
        return self.rate_limit_configurations.get(limit_name)

    def is_active_tenant(self) -> bool:
        """Check if tenant is active and not expired"""
        if not self.active or self.status != TenantStatus.ACTIVE:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

    def has_parent(self) -> bool:
        """Check if tenant has a parent (is a sub-tenant)"""
        return self.parent_tenant_guid is not None

    def get_endpoint_url(self, protocol: str = "http") -> Optional[str]:
        """Get endpoint URL for specified protocol"""
        if not self.endpoints:
            return None
        
        if protocol.lower() == "http" and self.endpoints.http:
            return self.endpoints.http.url
        elif protocol.lower() == "grpc" and self.endpoints.grpc:
            return self.endpoints.grpc.url
        
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return self.to_dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TenantInfo':
        """Create TenantInfo from dictionary"""
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        """String representation"""
        return f"TenantInfo(guid={self.tenant_guid}, name={self.tenant_name}, status={self.status.value})"
    
    def __repr__(self) -> str:
        """Detailed representation"""
        return (f"TenantInfo(tenant_guid='{self.tenant_guid}', "
                f"tenant_name='{self.tenant_name}', "
                f"tenant_id={self.tenant_id}, "
                f"status={self.status.value}, "
                f"tenant_type={self.tenant_type.value}, "
                f"active={self.active})")

# Utility functions for tenant operations
def create_default_endpoints(http_url: str, grpc_url: str) -> TenantEndpoints:
    """Create default tenant endpoints"""
    return TenantEndpoints(
        http=EndpointConfig(url=http_url, protocols="Http1"),
        grpc=EndpointConfig(url=grpc_url, protocols="Http2")
    )

def create_default_rate_limits() -> Dict[str, RateLimitBucketConfiguration]:
    """Create default rate limiting configurations"""
    return {
        "api_requests": RateLimitBucketConfiguration(
            capacity=1000,
            refill_tokens=100,
            refill_period_seconds=60,
            tokens_per_request=1,
            description="API request rate limiting"
        ),
        "authentication": RateLimitBucketConfiguration(
            capacity=100,
            refill_tokens=10,
            refill_period_seconds=60,
            tokens_per_request=1,
            description="Authentication attempt rate limiting"
        ),
        "command_execution": RateLimitBucketConfiguration(
            capacity=50,
            refill_tokens=10,
            refill_period_seconds=60,
            tokens_per_request=1,
            description="Command execution rate limiting"
        )
    }