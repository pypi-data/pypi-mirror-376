"""
Authentication service for D3 Identity Service
Provides high-level authentication and authorization utilities
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from ..models.tenant import TenantInfo
from ..models.auth import (
    JwtClaims, TokenValidationResult, AuthenticationContext, 
    AuthenticationMethod, create_service_claims, create_user_claims
)
from ..services.jwt_service import JwtService
from ..services.tenant_service import TenantService

logger = logging.getLogger(__name__)

class AuthService:
    """
    High-level authentication service providing unified authentication interface
    """
    
    def __init__(self, jwt_service: JwtService, tenant_service: TenantService):
        """
        Initialize authentication service
        
        Args:
            jwt_service: JWT token service
            tenant_service: Tenant management service
        """
        self.jwt_service = jwt_service
        self.tenant_service = tenant_service
        
        logger.info("AuthService initialized")
    
    async def authenticate_service_token(
        self, 
        token: str, 
        required_service: Optional[str] = None,
        required_permissions: Optional[List[str]] = None
    ) -> Optional[AuthenticationContext]:
        """
        Authenticate service-to-service token
        
        Args:
            token: JWT token to authenticate
            required_service: Required service name (optional)
            required_permissions: Required permissions (optional)
            
        Returns:
            AuthenticationContext or None if authentication failed
        """
        try:
            # Validate token
            validation_result = await self.jwt_service.validate_token(token)
            
            if not validation_result.is_valid or not validation_result.claims:
                logger.debug(f"Token validation failed: {validation_result.error_message}")
                return None
            
            claims = validation_result.claims
            
            # Check if it's a service token
            if not claims.is_service_token():
                logger.debug("Token is not a service token")
                return None
            
            # Check required service
            if required_service and claims.service_name != required_service:
                logger.debug(f"Service mismatch: expected {required_service}, got {claims.service_name}")
                return None
            
            # Check required permissions
            if required_permissions:
                missing_permissions = [p for p in required_permissions if not claims.has_permission(p)]
                if missing_permissions:
                    logger.debug(f"Missing permissions: {missing_permissions}")
                    return None
            
            # Get tenant information
            tenant_info = await self.tenant_service.get_tenant(claims.tenant_guid)
            if not tenant_info or not tenant_info.is_active_tenant():
                logger.debug(f"Tenant not found or inactive: {claims.tenant_guid}")
                return None
            
            # Create authentication context
            context = AuthenticationContext(
                tenant_guid=claims.tenant_guid,
                tenant_name=claims.tenant_name,
                authentication_method=AuthenticationMethod.SERVICE_ACCOUNT,
                authenticated_at=datetime.utcnow(),
                token_claims=claims
            )
            
            logger.debug(f"Service token authenticated successfully: {claims.service_name}")
            return context
            
        except Exception as e:
            logger.error(f"Service token authentication failed: {e}")
            return None
    
    async def authenticate_user_token(
        self, 
        token: str,
        required_role: Optional[str] = None,
        required_permissions: Optional[List[str]] = None
    ) -> Optional[AuthenticationContext]:
        """
        Authenticate user token
        
        Args:
            token: JWT token to authenticate
            required_role: Required user role (optional)
            required_permissions: Required permissions (optional)
            
        Returns:
            AuthenticationContext or None if authentication failed
        """
        try:
            # Validate token
            validation_result = await self.jwt_service.validate_token(token)
            
            if not validation_result.is_valid or not validation_result.claims:
                logger.debug(f"Token validation failed: {validation_result.error_message}")
                return None
            
            claims = validation_result.claims
            
            # Check if it's a user token
            if claims.is_service_token():
                logger.debug("Token is a service token, expected user token")
                return None
            
            # Check required role
            if required_role and claims.role != required_role:
                logger.debug(f"Role mismatch: expected {required_role}, got {claims.role}")
                return None
            
            # Check required permissions
            if required_permissions:
                missing_permissions = [p for p in required_permissions if not claims.has_permission(p)]
                if missing_permissions:
                    logger.debug(f"Missing permissions: {missing_permissions}")
                    return None
            
            # Get tenant information
            tenant_info = await self.tenant_service.get_tenant(claims.tenant_guid)
            if not tenant_info or not tenant_info.is_active_tenant():
                logger.debug(f"Tenant not found or inactive: {claims.tenant_guid}")
                return None
            
            # Create authentication context
            context = AuthenticationContext(
                tenant_guid=claims.tenant_guid,
                tenant_name=claims.tenant_name,
                authentication_method=AuthenticationMethod.JWT,
                authenticated_at=datetime.utcnow(),
                token_claims=claims
            )
            
            logger.debug(f"User token authenticated successfully: {claims.user_name}")
            return context
            
        except Exception as e:
            logger.error(f"User token authentication failed: {e}")
            return None
    
    async def authenticate_any_token(
        self, 
        token: str,
        allow_service_tokens: bool = True,
        allow_user_tokens: bool = True
    ) -> Optional[AuthenticationContext]:
        """
        Authenticate any valid token (service or user)
        
        Args:
            token: JWT token to authenticate
            allow_service_tokens: Whether to accept service tokens
            allow_user_tokens: Whether to accept user tokens
            
        Returns:
            AuthenticationContext or None if authentication failed
        """
        try:
            # Validate token
            validation_result = await self.jwt_service.validate_token(token)
            
            if not validation_result.is_valid or not validation_result.claims:
                logger.debug(f"Token validation failed: {validation_result.error_message}")
                return None
            
            claims = validation_result.claims
            
            # Check token type restrictions
            if claims.is_service_token() and not allow_service_tokens:
                logger.debug("Service tokens not allowed")
                return None
            
            if not claims.is_service_token() and not allow_user_tokens:
                logger.debug("User tokens not allowed")
                return None
            
            # Get tenant information
            tenant_info = await self.tenant_service.get_tenant(claims.tenant_guid)
            if not tenant_info or not tenant_info.is_active_tenant():
                logger.debug(f"Tenant not found or inactive: {claims.tenant_guid}")
                return None
            
            # Determine authentication method
            auth_method = (AuthenticationMethod.SERVICE_ACCOUNT 
                         if claims.is_service_token() 
                         else AuthenticationMethod.JWT)
            
            # Create authentication context
            context = AuthenticationContext(
                tenant_guid=claims.tenant_guid,
                tenant_name=claims.tenant_name,
                authentication_method=auth_method,
                authenticated_at=datetime.utcnow(),
                token_claims=claims
            )
            
            logger.debug(f"Token authenticated successfully: {claims.tenant_guid}")
            return context
            
        except Exception as e:
            logger.error(f"Token authentication failed: {e}")
            return None
    
    async def generate_service_authentication(
        self,
        tenant_guid: str,
        service_name: str,
        permissions: Optional[List[str]] = None,
        expiration_minutes: int = 30
    ) -> Optional[str]:
        """
        Generate authentication token for service
        
        Args:
            tenant_guid: Target tenant GUID
            service_name: Service name
            permissions: Service permissions
            expiration_minutes: Token expiration in minutes
            
        Returns:
            JWT token string or None if failed
        """
        try:
            # Get tenant to validate it exists and is active
            tenant_info = await self.tenant_service.get_tenant(tenant_guid)
            if not tenant_info or not tenant_info.is_active_tenant():
                logger.error(f"Tenant not found or inactive: {tenant_guid}")
                return None
            
            # Generate service token
            token_response = await self.jwt_service.generate_service_token(
                tenant_guid=tenant_guid,
                service_name=service_name,
                permissions=permissions,
                expiration_minutes=expiration_minutes
            )
            
            if token_response:
                logger.info(f"Generated service token for {service_name} in tenant {tenant_guid}")
                return token_response.token
            else:
                logger.error(f"Failed to generate service token for {service_name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate service authentication: {e}")
            return None
    
    async def check_permission(
        self, 
        context: AuthenticationContext, 
        required_permission: str
    ) -> bool:
        """
        Check if authentication context has required permission
        
        Args:
            context: Authentication context
            required_permission: Permission to check
            
        Returns:
            True if permission is granted, False otherwise
        """
        try:
            if not context.token_claims:
                return False
            
            return context.token_claims.has_permission(required_permission)
            
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False
    
    async def check_tenant_access(
        self, 
        context: AuthenticationContext, 
        target_tenant_guid: str
    ) -> bool:
        """
        Check if authentication context has access to target tenant
        
        Args:
            context: Authentication context
            target_tenant_guid: Target tenant GUID to check access for
            
        Returns:
            True if access is granted, False otherwise
        """
        try:
            # Same tenant access is always allowed
            if context.tenant_guid == target_tenant_guid:
                return True
            
            # Get both tenants to check hierarchy
            source_tenant = await self.tenant_service.get_tenant(context.tenant_guid)
            target_tenant = await self.tenant_service.get_tenant(target_tenant_guid)
            
            if not source_tenant or not target_tenant:
                return False
            
            # Check if source tenant is parent of target tenant
            if target_tenant.parent_tenant_guid == context.tenant_guid:
                return True
            
            # Check if both tenants have same parent (sibling access)
            if (source_tenant.parent_tenant_guid and 
                source_tenant.parent_tenant_guid == target_tenant.parent_tenant_guid):
                return True
            
            # Service tokens with appropriate permissions can access any tenant
            if (context.is_service_authentication() and 
                context.token_claims and
                context.token_claims.has_permission("cross_tenant_access")):
                return True
            
            logger.debug(f"Tenant access denied: {context.tenant_guid} -> {target_tenant_guid}")
            return False
            
        except Exception as e:
            logger.error(f"Tenant access check failed: {e}")
            return False
    
    async def refresh_authentication_context(
        self, 
        context: AuthenticationContext
    ) -> Optional[AuthenticationContext]:
        """
        Refresh authentication context with latest tenant information
        
        Args:
            context: Current authentication context
            
        Returns:
            Updated AuthenticationContext or None if refresh failed
        """
        try:
            # Get latest tenant information
            tenant_info = await self.tenant_service.get_tenant(context.tenant_guid)
            if not tenant_info or not tenant_info.is_active_tenant():
                logger.debug(f"Tenant no longer active: {context.tenant_guid}")
                return None
            
            # Update context with latest tenant name
            updated_context = AuthenticationContext(
                tenant_guid=context.tenant_guid,
                tenant_name=tenant_info.tenant_name,
                authentication_method=context.authentication_method,
                authenticated_at=context.authenticated_at,
                token_claims=context.token_claims,
                service_info=context.service_info,
                session_id=context.session_id,
                client_ip=context.client_ip,
                user_agent=context.user_agent
            )
            
            logger.debug(f"Authentication context refreshed: {context.tenant_guid}")
            return updated_context
            
        except Exception as e:
            logger.error(f"Failed to refresh authentication context: {e}")
            return None
    
    def is_token_near_expiration(
        self, 
        context: AuthenticationContext, 
        threshold_minutes: int = 5
    ) -> bool:
        """
        Check if token is near expiration
        
        Args:
            context: Authentication context
            threshold_minutes: Minutes before expiration to consider "near"
            
        Returns:
            True if token expires within threshold, False otherwise
        """
        try:
            if not context.token_claims or not context.token_claims.expires_at:
                return False
            
            time_to_expiration = context.token_claims.expires_at - datetime.utcnow()
            threshold = timedelta(minutes=threshold_minutes)
            
            return time_to_expiration <= threshold
            
        except Exception as e:
            logger.error(f"Token expiration check failed: {e}")
            return True  # Assume near expiration on error for safety