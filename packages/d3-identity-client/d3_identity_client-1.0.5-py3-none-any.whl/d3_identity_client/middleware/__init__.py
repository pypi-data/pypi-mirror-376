"""
Middleware integrations for D3 Identity Service client
Provides framework-specific authentication middleware
"""

from .fastapi import D3IdentityMiddleware, D3IdentityFastAPIMiddleware
from .grpc import D3IdentityGrpcInterceptor

__all__ = [
    "D3IdentityMiddleware",
    "D3IdentityFastAPIMiddleware", 
    "D3IdentityGrpcInterceptor"
]