"""
D3 Identity Service Python Client Library

This library provides Python integration with the D3 Identity Service for:
- Multi-tenant authentication and authorization
- JWT token management with Ed25519 signatures
- Real-time configuration management via etcd
- Service registration and discovery
- Cryptographic key management and rotation

Main Components:
- D3IdentityClient: Primary client interface
- TenantInfo: Tenant data model
- JwtService: Token generation and validation
- EtcdService: Distributed configuration management
"""

from .client import D3IdentityClient
from .models.tenant import (
    TenantInfo,
    TenantKeyPair,
    TenantEndpoints,
    EndpointConfig,
    TenantType,
    TenantStatus,
    RateLimitBucketConfiguration,
    InternalServices
)
from .models.auth import (
    JwtClaims,
    TokenValidationResult,
    ServiceRegistrationInfo
)
from .services.tenant_service import TenantService
from .services.jwt_service import JwtService
from .services.etcd_service import EtcdService
from .services.auth_service import AuthService
from .crypto.ed25519 import Ed25519KeyManager
from .utils.config import IdentityClientConfig, create_development_config, create_production_config
from .models.config import (
    IdentityServiceOptions,
    EtcdConfiguration,
    CacheConfiguration,
    SecurityConfiguration,
    ServiceConfiguration,
    LoggingConfiguration,
    CacheType,
    LogLevel
)
from .controllers import (
    TestController,
    TestEndpoints,
    GrpcController,
    TestRequest,
    TestResponse,
    RegisterRequest,
    RegisterResponse
)

# Optional middleware imports (only if dependencies are available)
try:
    from .middleware.fastapi import D3IdentityMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    D3IdentityMiddleware = None
    FASTAPI_AVAILABLE = False

try:
    from .middleware.grpc import D3IdentityGrpcInterceptor
    GRPC_MIDDLEWARE_AVAILABLE = True
except ImportError:
    D3IdentityGrpcInterceptor = None
    GRPC_MIDDLEWARE_AVAILABLE = False

# Version information
__version__ = "1.0.0"
__author__ = "D3 Security"
__email__ = "support@d3security.com"

# Public API exports
__all__ = [
    # Main client
    "D3IdentityClient",
    
    # Data models
    "TenantInfo",
    "TenantKeyPair", 
    "TenantEndpoints",
    "EndpointConfig",
    "TenantType",
    "TenantStatus",
    "RateLimitBucketConfiguration",
    "InternalServices",
    
    # Authentication models
    "JwtClaims",
    "TokenValidationResult",
    "ServiceRegistrationInfo",
    
    # Core services
    "TenantService",
    "JwtService", 
    "EtcdService",
    "AuthService",
    
    # Cryptography
    "Ed25519KeyManager",
    
    # Configuration
    "IdentityClientConfig",
    "IdentityServiceOptions",
    "EtcdConfiguration", 
    "CacheConfiguration",
    "SecurityConfiguration",
    "ServiceConfiguration",
    "LoggingConfiguration",
    "CacheType",
    "LogLevel",
    "create_development_config",
    "create_production_config",
    
    # Middleware (if available)
    # "D3IdentityMiddleware",  # Available if FASTAPI_AVAILABLE
    # "D3IdentityGrpcInterceptor",  # Available if GRPC_MIDDLEWARE_AVAILABLE
    
    # Version
    "__version__"
    # Controllers
    "TestController",
    "TestEndpoints", 
    "GrpcController",
    "TestRequest",
    "TestResponse",
    "RegisterRequest",
    "RegisterResponse",
]