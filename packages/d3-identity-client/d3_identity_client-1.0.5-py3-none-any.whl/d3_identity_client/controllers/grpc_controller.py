"""
gRPC controller for SDK functionality validation
Matches C# IdentitySdkClientGrpcController
"""

import logging
import grpc
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from ..models.auth import AuthenticationContext
from ..services.auth_service import AuthService
from ..services.tenant_service import TenantService

logger = logging.getLogger(__name__)

# Protobuf message models (would need actual .proto definitions)
class TestConnectionRequest:
    """TestConnectionRequest protobuf message model"""
    def __init__(self, message: str = "", tenant_guid: str = ""):
        self.message = message
        self.tenant_guid = tenant_guid

class TestConnectionResponse:
    """TestConnectionResponse protobuf message model"""
    def __init__(self, status: str = "", message: str = "", tenant_info: Optional[Dict] = None):
        self.status = status
        self.message = message
        self.tenant_info = tenant_info or {}

class GrpcController:
    """
    gRPC controller for Identity Service SDK
    Matches C# IdentitySdkClientGrpcController
    """
    
    def __init__(self, auth_service: AuthService, tenant_service: TenantService):
        """
        Initialize gRPC controller
        
        Args:
            auth_service: Authentication service
            tenant_service: Tenant service
        """
        self.auth_service = auth_service
        self.tenant_service = tenant_service
        
        logger.info("GrpcController initialized")
    
    async def test_connection(
        self, 
        request: TestConnectionRequest, 
        context: grpc.ServicerContext
    ) -> TestConnectionResponse:
        """
        Test connection gRPC method
        Matches C# IdentitySdkClientGrpcController.TestConnection
        
        Args:
            request: TestConnectionRequest
            context: gRPC context
            
        Returns:
            TestConnectionResponse
        """
        try:
            # Authenticate gRPC request
            auth_context = await self._authenticate_grpc_request(context)
            if not auth_context:
                return TestConnectionResponse(
                    status="Unauthenticated",
                    message="Authentication required for test connection"
                )
            
            tenant_guid = auth_context.tenant_guid
            logger.info(f"TestConnection called for tenant {tenant_guid}")
            
            # Get tenant information
            tenant_info = await self.tenant_service.get_tenant(tenant_guid)
            
            if tenant_info:
                tenant_data = {
                    "tenant_guid": tenant_info.tenant_guid,
                    "tenant_name": tenant_info.tenant_name,
                    "tenant_type": tenant_info.tenant_type.value,
                    "status": tenant_info.status.value,
                    "active": tenant_info.active,
                    "jwt_expiration_minutes": tenant_info.jwt_expiration_minutes,
                    "max_users": tenant_info.max_users,
                    "max_sites": tenant_info.max_sites
                }
                
                return TestConnectionResponse(
                    status="OK",
                    message=f"Connection test successful for tenant {tenant_info.tenant_name}",
                    tenant_info=tenant_data
                )
            else:
                return TestConnectionResponse(
                    status="Error",
                    message=f"Tenant {tenant_guid} not found"
                )
                
        except Exception as e:
            logger.error(f"TestConnection failed: {e}")
            return TestConnectionResponse(
                status="Error",
                message=f"Connection test failed: {str(e)}"
            )
    
    async def _authenticate_grpc_request(self, context: grpc.ServicerContext) -> Optional[AuthenticationContext]:
        """
        Authenticate gRPC request using metadata
        
        Args:
            context: gRPC servicer context
            
        Returns:
            AuthenticationContext if valid, None otherwise
        """
        try:
            # Get metadata from context
            metadata = dict(context.invocation_metadata())
            
            # Look for authorization header
            auth_token = None
            if 'authorization' in metadata:
                auth_header = metadata['authorization']
                if auth_header.startswith('Bearer '):
                    auth_token = auth_header[7:]  # Remove "Bearer " prefix
            
            if not auth_token:
                logger.debug("No authorization token found in gRPC metadata")
                return None
            
            # Authenticate token
            auth_context = await self.auth_service.authenticate_any_token(auth_token)
            
            if auth_context:
                logger.debug(f"gRPC authentication successful for tenant: {auth_context.tenant_guid}")
                return auth_context
            else:
                logger.debug("gRPC authentication failed - invalid token")
                return None
                
        except Exception as e:
            logger.error(f"gRPC authentication error: {e}")
            return None

def create_grpc_servicer(auth_service: AuthService, tenant_service: TenantService):
    """
    Factory function to create gRPC servicer
    
    Args:
        auth_service: Authentication service
        tenant_service: Tenant service
        
    Returns:
        gRPC servicer instance
    """
    return GrpcController(auth_service, tenant_service)