# D3 Identity Service Python Client

Python client library for D3 Identity Service integration, providing multi-tenant authentication, JWT token management, and distributed configuration management.

## Features

- **Ed25519 JWT Authentication**: Modern cryptographic signatures for enhanced security
- **Multi-tenant Support**: Tenant-specific configuration and key management
- **Real-time Configuration**: Live configuration updates via etcd watching
- **Service Registration**: Automatic service discovery and health monitoring
- **High-performance Caching**: Memory and Redis-based caching with TTL
- **Framework Integration**: FastAPI and gRPC middleware for seamless integration
- **Comprehensive Security**: Key rotation, rate limiting, and audit logging

## Installation

```bash
pip install -e .
```

### Requirements

- Python 3.8+
- etcd cluster (for distributed configuration)
- Redis (optional, for caching)

## Quick Start

### 1. Environment Configuration

Set the following environment variables:

```bash
export D3_TENANT_GUID="your-tenant-guid"
export D3_API_KEY="your-tenant-api-key"
export ETCD_ENDPOINTS="etcd1:2379,etcd2:2379,etcd3:2379"
export SERVICE_NAME="YourService"
```

### 2. Basic Usage

```python
import asyncio
from d3_identity_client import D3IdentityClient

async def main():
    # Create and initialize client
    async with D3IdentityClient() as client:
        # Get tenant information
        tenant_info = await client.get_tenant_info()
        print(f"Tenant: {tenant_info.tenant_name}")
        
        # Generate service token
        token = await client.generate_service_token(
            service_name="MyService",
            permissions=["read", "write"]
        )
        
        # Validate token
        result = await client.validate_token(token)
        if result.is_valid:
            print(f"Token valid for tenant: {result.claims.tenant_name}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. FastAPI Integration

```python
from fastapi import FastAPI, Depends
from d3_identity_client import D3IdentityClient, create_service_auth_dependency

app = FastAPI()

# Initialize client (do this at startup)
identity_client = None

@app.on_event("startup")
async def startup():
    global identity_client
    identity_client = await create_client()

@app.on_event("shutdown") 
async def shutdown():
    if identity_client:
        await identity_client.cleanup()

# Create authentication dependency
auth_required = create_service_auth_dependency(
    identity_client.auth_service,
    required_service="MyService"
)

@app.get("/protected")
async def protected_endpoint(auth_context=auth_required):
    return {
        "message": "Success",
        "tenant": auth_context.tenant_name,
        "service": auth_context.get_service_name()
    }
```

### 4. gRPC Integration

```python
import grpc
from grpc import aio
from d3_identity_client import D3IdentityGrpcInterceptor, create_client

async def create_grpc_server():
    # Initialize client
    client = await create_client()
    
    # Create interceptor
    auth_interceptor = D3IdentityGrpcInterceptor(
        client.auth_service,
        require_auth=True
    )
    
    # Create server with interceptor
    server = aio.server(interceptors=[auth_interceptor])
    
    # Add your service handlers
    # my_pb2_grpc.add_MyServiceServicer_to_server(MyServiceHandler(), server)
    
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    
    await server.start()
    await server.wait_for_termination()
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `D3_TENANT_GUID` | Tenant GUID | Required |
| `D3_API_KEY` | Tenant API key | Required |
| `ETCD_ENDPOINTS` | etcd endpoints (comma-separated) | `localhost:2379` |
| `ETCD_USERNAME` | etcd authentication username | None |
| `ETCD_PASSWORD` | etcd authentication password | None |
| `CACHE_TYPE` | Cache type: `memory`, `redis`, `hybrid` | `memory` |
| `REDIS_HOST` | Redis host for caching | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `SERVICE_NAME` | Service name for registration | None |
| `LOG_LEVEL` | Logging level | `INFO` |

### Programmatic Configuration

```python
from d3_identity_client import IdentityServiceOptions, create_production_config

config = create_production_config(
    tenant_guid="your-tenant-guid",
    api_key="your-api-key",
    service_name="YourService",
    etcd_endpoints=["etcd1:2379", "etcd2:2379"],
    redis_host="redis.example.com"
)

client = D3IdentityClient(config)
```

## Advanced Usage

### Tenant Watching

Monitor tenant configuration changes in real-time:

```python
async def tenant_change_callback(tenant_info):
    print(f"Tenant configuration updated: {tenant_info.tenant_name}")
    # Update application configuration based on tenant changes

await client.watch_tenant(tenant_guid, tenant_change_callback)
```

### Service Discovery

Register and discover internal services:

```python
# Register service
await client.register_internal_service(
    service_name="MyService",
    service_endpoints={
        "http": "http://myservice:8080",
        "grpc": "grpc://myservice:50051"
    }
)

# Discover services
services = await client.get_all_internal_services()
command_service = services.get("CommandService")
if command_service:
    http_endpoint = command_service.get_endpoint("http")
```

### Custom Authentication

Implement custom authentication logic:

```python
from d3_identity_client import AuthService

async def custom_auth_handler(token: str):
    # Validate token
    context = await client.authenticate_token(token)
    
    if not context:
        raise AuthenticationError("Invalid token")
    
    # Check custom business rules
    if not context.token_claims.has_permission("custom_action"):
        raise AuthorizationError("Insufficient permissions")
    
    return context
```

### Multi-tenant Operations

Work with multiple tenants:

```python
# Get multiple tenants
tenant_guids = ["guid1", "guid2", "guid3"]
tenants = await client.get_multiple_tenants(tenant_guids)

for guid, tenant in tenants.items():
    if tenant and tenant.is_active_tenant():
        print(f"Active tenant: {tenant.tenant_name}")
```

## Security Features

### Key Rotation

The client automatically handles key rotation:

```python
# Keys are automatically rotated by the Identity Service
# Client handles both current and previous keys for validation
# No manual intervention required
```

### Rate Limiting

Configure tenant-specific rate limiting:

```python
tenant_info = await client.get_tenant_info()
api_limit = tenant_info.get_rate_limit_config("api_requests")

if api_limit:
    print(f"API rate limit: {api_limit.max_requests_per_minute()}/minute")
```

### Permissions

Check permissions in your application:

```python
async def check_permissions(auth_context, required_permission):
    if not await client.auth_service.check_permission(auth_context, required_permission):
        raise PermissionError(f"Permission '{required_permission}' required")
```

## Health Monitoring

Monitor client health:

```python
@app.get("/health")
async def health_check():
    health_status = await client.health_check()
    
    if health_status["status"] == "healthy":
        return {"status": "OK", "details": health_status}
    else:
        raise HTTPException(status_code=503, detail="Service unhealthy")
```

## Error Handling

The client provides comprehensive error handling:

```python
from d3_identity_client import TokenValidationResult

async def safe_token_validation(token: str):
    try:
        result = await client.validate_token(token)
        
        if result.is_valid:
            return result.claims
        else:
            logger.warning(f"Token validation failed: {result.error_message}")
            return None
            
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return None
```

## Development Mode

For development and testing:

```python
from d3_identity_client import create_development_config

config = create_development_config(
    tenant_guid="dev-tenant-guid",
    api_key="dev-api-key",
    service_name="DevService"
)

config.debug_mode = True
config.logging.log_level = LogLevel.DEBUG

client = D3IdentityClient(config)
```

## Testing

Mock the client for unit testing:

```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
async def mock_client():
    client = AsyncMock(spec=D3IdentityClient)
    client.authenticate_token.return_value = AuthenticationContext(...)
    return client
```

## Migration from Legacy Authentication

Replace existing JWT authentication:

```python
# Before (legacy)
def verify_jwt_token(token):
    return jwt.decode(token, secret_key, algorithms=["HS256"])

# After (D3 Identity Service)
async def verify_jwt_token(token):
    result = await client.validate_token(token)
    return result.claims if result.is_valid else None
```

## Performance Considerations

- **Caching**: Enable Redis caching for production deployments
- **Connection Pooling**: Client automatically manages etcd connections
- **Token Caching**: JWT validation results are cached for performance
- **Batch Operations**: Use `get_multiple_tenants()` for bulk operations

## Troubleshooting

### Common Issues

1. **etcd Connection Failed**
   ```python
   # Check etcd endpoints and credentials
   health = await client.health_check()
   print(health["etcd"])
   ```

2. **Token Validation Failures**
   ```python
   # Check token format and expiration
   token_info = await client.jwt_service.get_token_info(token)
   print(f"Token expires: {token_info['expires_at']}")
   ```

3. **Tenant Not Found**
   ```python
   # Verify tenant GUID and status
   tenant = await client.get_tenant_info()
   if tenant:
       print(f"Tenant status: {tenant.status}")
   ```

### Debug Logging

Enable debug logging for detailed information:

```python
import logging
logging.getLogger("d3_identity_client").setLevel(logging.DEBUG)
```

## Support

For issues and questions:
- Check the [troubleshooting guide](docs/troubleshooting.md)
- Review [API documentation](docs/api.md)
- Submit issues on GitHub

## License

MIT License - see LICENSE file for details.