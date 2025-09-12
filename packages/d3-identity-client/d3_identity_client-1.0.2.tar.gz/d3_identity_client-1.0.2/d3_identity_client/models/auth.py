"""
Authentication and authorization models for D3 Identity Service
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from datetime import datetime
from enum import Enum
from dataclasses_json import dataclass_json, LetterCase

class TokenType(Enum):
    """JWT token type enumeration"""
    ACCESS_TOKEN = "access_token"
    SERVICE_TOKEN = "service_token"
    REFRESH_TOKEN = "refresh_token"

class AuthenticationMethod(Enum):
    """Authentication method enumeration"""
    JWT = "jwt"
    API_KEY = "api_key"
    SERVICE_ACCOUNT = "service_account"

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class JwtClaims:
    """JWT token claims structure"""
    # Standard JWT claims
    issuer: str  # iss - token issuer
    audience: List[str]  # aud - intended audience
    subject: Optional[str] = None  # sub - subject identifier
    issued_at: Optional[datetime] = None  # iat - issued at time
    expires_at: Optional[datetime] = None  # exp - expiration time
    not_before: Optional[datetime] = None  # nbf - not before time
    jwt_id: Optional[str] = None  # jti - JWT ID
    
    # D3 Identity Service specific claims
    tenant_guid: str = ""
    tenant_name: str = ""
    tenant_type: str = "Vsoc"
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    role: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    service_name: Optional[str] = None
    
    # Additional custom claims
    custom_claims: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if token is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_valid_for_audience(self, required_audience: str) -> bool:
        """Check if token is valid for specific audience"""
        return required_audience in self.audience
    
    def has_permission(self, permission: str) -> bool:
        """Check if token has specific permission"""
        return permission in self.permissions
    
    def is_service_token(self) -> bool:
        """Check if this is a service-to-service token"""
        return self.service_name is not None

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TokenValidationResult:
    """Result of JWT token validation"""
    is_valid: bool
    claims: Optional[JwtClaims] = None
    error_message: Optional[str] = None
    validation_timestamp: Optional[datetime] = None
    key_id: Optional[str] = None  # Key ID used for validation

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class AuthenticationContext:
    """Authentication context for requests"""
    tenant_guid: str
    tenant_name: str
    authentication_method: AuthenticationMethod
    authenticated_at: datetime
    token_claims: Optional[JwtClaims] = None
    
    def is_service_authentication(self) -> bool:
        """Check if authentication is service-to-service"""
        return (self.authentication_method == AuthenticationMethod.SERVICE_ACCOUNT or
                (self.token_claims and self.token_claims.is_service_token()))
    
    def get_user_id(self) -> Optional[str]:
        """Get authenticated user ID if available"""
        return self.token_claims.user_id if self.token_claims else None
    
    def get_service_name(self) -> Optional[str]:
        """Get authenticated service name if available"""
        return self.token_claims.service_name if self.token_claims else None

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ServiceRegistrationInfo:
    """Information about registered internal service"""
    service_name: str
    tenant_guid: Optional[str] = None
    service_endpoints: Dict[str, str] = field(default_factory=dict)
    registration_timestamp: Optional[datetime] = None
    is_active: bool = True

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TokenGenerationRequest:
    """Request for generating JWT tokens"""
    tenant_guid: str
    claims: Dict[str, Any]
    expiration_minutes: int = 30
    token_type: TokenType = TokenType.SERVICE_TOKEN
    audience: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TokenGenerationResponse:
    """Response from JWT token generation"""
    token: str
    token_type: str
    expires_at: datetime
    issued_at: datetime
    key_id: str  # Key ID used for signing
    tenant_guid: str


# Utility functions for authentication
def create_service_claims(
    service_name: str,
    tenant_guid: str,
    tenant_name: str,
    permissions: List[str] = None
) -> JwtClaims:
    """Create JWT claims for service-to-service authentication"""
    now = datetime.utcnow()
    
    return JwtClaims(
        issuer="https://api.d3playbookIdentity.com",
        audience=["https://api.d3playbookTenant.com"],
        issued_at=now,
        tenant_guid=tenant_guid,
        tenant_name=tenant_name,
        service_name=service_name,
        permissions=permissions or [],
        custom_claims={"service_type": "internal"}
    )

def create_user_claims(
    user_id: str,
    user_name: str,
    tenant_guid: str,
    tenant_name: str,
    role: str = None,
    permissions: List[str] = None
) -> JwtClaims:
    """Create JWT claims for user authentication"""
    now = datetime.utcnow()
    
    return JwtClaims(
        issuer="https://api.d3playbookIdentity.com",
        audience=["https://api.d3playbookTenant.com"],
        subject=user_id,
        issued_at=now,
        tenant_guid=tenant_guid,
        tenant_name=tenant_name,
        user_id=user_id,
        user_name=user_name,
        role=role,
        permissions=permissions or []
    )