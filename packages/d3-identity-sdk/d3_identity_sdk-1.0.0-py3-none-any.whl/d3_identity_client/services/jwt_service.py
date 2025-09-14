"""
JWT token service for D3 Identity Service
Provides Ed25519-based JWT token generation and validation
"""

import jwt
import json
import hashlib
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from ..models.tenant import TenantInfo, TenantKeyPair
from ..models.auth import JwtClaims, TokenValidationResult, TokenGenerationRequest, TokenGenerationResponse
from ..models.config import SecurityConfiguration
from ..crypto.ed25519 import Ed25519KeyManager
from ..services.etcd_service import EtcdService
from ..services.cache_service import CacheService

logger = logging.getLogger(__name__)

class JwtService:
    """
    JWT token service with Ed25519 signatures and tenant-specific key management
    Provides token generation, validation, and caching
    """
    
    def __init__(
        self, 
        etcd_service: EtcdService, 
        cache_service: Optional[CacheService] = None,
        security_config: Optional[SecurityConfiguration] = None
    ):
        """
        Initialize JWT service
        
        Args:
            etcd_service: etcd service for tenant data retrieval
            cache_service: Optional cache service for performance
            security_config: Security configuration settings
        """
        self.etcd_service = etcd_service
        self.cache_service = cache_service
        self.security_config = security_config or SecurityConfiguration()
        self.key_manager = Ed25519KeyManager()
        
        # JWT configuration
        self.default_issuer = "https://api.d3playbookIdentity.com"
        self.default_audience = ["https://api.d3playbookTenant.com"]
        
        logger.info("JwtService initialized with Ed25519 support")
    
    async def generate_token(
        self, 
        tenant_guid: str, 
        claims: Dict[str, Any],
        expiration_minutes: int = 30,
        audience: Optional[List[str]] = None
    ) -> Optional[TokenGenerationResponse]:
        """
        Generate JWT token for tenant using Ed25519 signature
        
        Args:
            tenant_guid: Tenant GUID for key lookup
            claims: Additional claims to include in token
            expiration_minutes: Token expiration time in minutes
            audience: Token audience (defaults to tenant audience)
            
        Returns:
            TokenGenerationResponse with token details or None if failed
        """
        try:
            # Get tenant information
            tenant_info = await self._get_tenant_info(tenant_guid)
            if not tenant_info:
                logger.error(f"Tenant not found: {tenant_guid}")
                return None
            
            # Get primary JWT key pair
            primary_key = tenant_info.get_primary_jwt_key_pair()
            if not primary_key:
                logger.error(f"No primary JWT key pair found for tenant: {tenant_guid}")
                return None
            
            # Decrypt private key
            private_key = self.key_manager.decrypt_private_key(
                primary_key.encrypted_private_key,
                tenant_info.api_key
            )
            
            # Prepare token claims
            now = datetime.utcnow()
            expires_at = now + timedelta(minutes=expiration_minutes)
            
            token_claims = {
                "iss": self.default_issuer,
                "aud": audience or self.default_audience,
                "iat": int(now.timestamp()),
                "exp": int(expires_at.timestamp()),
                "tenant_guid": tenant_info.tenant_guid,
                "tenant_name": tenant_info.tenant_name,
                "tenant_type": tenant_info.tenant_type.value,
                **claims  # Merge additional claims
            }
            
            # Generate JWT token with Ed25519
            token = jwt.encode(
                payload=token_claims,
                key=private_key,
                algorithm="EdDSA",
                headers={"kid": primary_key.key_id}
            )
            
            # Create response
            response = TokenGenerationResponse(
                token=token,
                token_type=claims.get("token_type", "service_token"),
                expires_at=expires_at,
                issued_at=now,
                key_id=primary_key.key_id,
                tenant_guid=tenant_info.tenant_guid
            )
            
            logger.info(f"Generated JWT token for tenant {tenant_guid} with key {primary_key.key_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate JWT token for tenant {tenant_guid}: {e}")
            return None
    
    async def validate_token(self, token: str) -> TokenValidationResult:
        """
        Validate JWT token using tenant's Ed25519 public key
        
        Args:
            token: JWT token to validate
            
        Returns:
            TokenValidationResult with validation details
        """
        try:
            # Check cache first
            token_hash = self._get_token_hash(token)
            if self.cache_service:
                cached_result = await self.cache_service.get_jwt_validation(token_hash)
                if cached_result:
                    logger.debug("JWT validation cache hit")
                    return TokenValidationResult.from_dict(json.loads(cached_result))
            
            # Decode header to get key ID and basic claims
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header.get("kid")
            
            if not key_id:
                return TokenValidationResult(
                    is_valid=False,
                    error_message="Token missing key ID (kid) in header"
                )
            
            # Get unverified claims to extract tenant GUID
            unverified_claims = jwt.decode(
                token, 
                options={"verify_signature": False, "verify_exp": False}
            )
            tenant_guid = unverified_claims.get("tenant_guid")
            
            if not tenant_guid:
                return TokenValidationResult(
                    is_valid=False,
                    error_message="Token missing tenant_guid claim"
                )
            
            # Get tenant information
            tenant_info = await self._get_tenant_info(tenant_guid)
            if not tenant_info:
                return TokenValidationResult(
                    is_valid=False,
                    error_message=f"Tenant not found: {tenant_guid}"
                )
            
            # Find key pair by key ID
            key_pair = tenant_info.key_pairs.get(key_id)
            if not key_pair or not key_pair.is_active:
                return TokenValidationResult(
                    is_valid=False,
                    error_message=f"Key pair not found or inactive: {key_id}"
                )
            
            # Load public key
            public_key = self.key_manager.load_public_key(key_pair.public_key)
            
            # Validate token with security configuration
            validation_options = {
                "verify_signature": True,
                "verify_exp": self.security_config.jwt_expiration_validation,
                "verify_aud": self.security_config.jwt_audience_validation,
                "verify_iss": self.security_config.jwt_issuer_validation,
            }
            
            # Validate token
            verified_claims = jwt.decode(
                token,
                key=public_key,
                algorithms=["EdDSA"],
                audience=self.default_audience if self.security_config.jwt_audience_validation else None,
                issuer=self.default_issuer if self.security_config.jwt_issuer_validation else None,
                options=validation_options,
                leeway=timedelta(seconds=self.security_config.get_allowed_clock_skew_seconds())
            )
            
            # Create JWT claims object
            jwt_claims = JwtClaims(
                issuer=verified_claims.get("iss", ""),
                audience=verified_claims.get("aud", []),
                subject=verified_claims.get("sub"),
                issued_at=datetime.fromtimestamp(verified_claims.get("iat", 0)),
                expires_at=datetime.fromtimestamp(verified_claims.get("exp", 0)),
                jwt_id=verified_claims.get("jti"),
                tenant_guid=verified_claims.get("tenant_guid", ""),
                tenant_name=verified_claims.get("tenant_name", ""),
                tenant_type=verified_claims.get("tenant_type", "Vsoc"),
                user_id=verified_claims.get("user_id"),
                user_name=verified_claims.get("user_name"),
                role=verified_claims.get("role"),
                permissions=verified_claims.get("permissions", []),
                service_name=verified_claims.get("service_name"),
                custom_claims={k: v for k, v in verified_claims.items() 
                             if k not in ["iss", "aud", "sub", "iat", "exp", "jti", 
                                        "tenant_guid", "tenant_name", "tenant_type", 
                                        "user_id", "user_name", "role", "permissions", "service_name"]}
            )
            
            # Create successful validation result
            result = TokenValidationResult(
                is_valid=True,
                claims=jwt_claims,
                key_id=key_id
            )
            
            # Cache successful validation
            if self.cache_service:
                await self.cache_service.set_jwt_validation(
                    token_hash, 
                    json.dumps(result.to_dict())
                )
            
            logger.debug(f"JWT token validated successfully for tenant {tenant_guid}")
            return result
            
        except jwt.ExpiredSignatureError:
            return TokenValidationResult(
                is_valid=False,
                error_message="Token has expired"
            )
        except jwt.InvalidAudienceError:
            return TokenValidationResult(
                is_valid=False,
                error_message="Invalid token audience"
            )
        except jwt.InvalidIssuerError:
            return TokenValidationResult(
                is_valid=False,
                error_message="Invalid token issuer"
            )
        except jwt.InvalidSignatureError:
            return TokenValidationResult(
                is_valid=False,
                error_message="Invalid token signature"
            )
        except Exception as e:
            logger.error(f"JWT validation failed: {e}")
            return TokenValidationResult(
                is_valid=False,
                error_message=f"Token validation error: {str(e)}"
            )
    
    async def validate_token_with_flexible_audience(
        self, 
        token: str, 
        allow_any_audience: bool = True
    ) -> TokenValidationResult:
        """
        Validate JWT token with flexible audience validation
        
        Args:
            token: JWT token to validate
            allow_any_audience: Whether to accept any audience
            
        Returns:
            TokenValidationResult with validation details
        """
        # Temporarily disable audience validation
        original_audience_validation = self.security_config.jwt_audience_validation
        
        try:
            if allow_any_audience:
                self.security_config.jwt_audience_validation = False
            
            return await self.validate_token(token)
            
        finally:
            # Restore original setting
            self.security_config.jwt_audience_validation = original_audience_validation
    
    async def generate_service_token(
        self, 
        tenant_guid: str,
        service_name: str,
        permissions: Optional[List[str]] = None,
        expiration_minutes: int = 30
    ) -> Optional[TokenGenerationResponse]:
        """
        Generate service-to-service JWT token
        
        Args:
            tenant_guid: Target tenant GUID
            service_name: Name of the requesting service
            permissions: List of permissions for the token
            expiration_minutes: Token expiration in minutes
            
        Returns:
            TokenGenerationResponse or None if failed
        """
        service_claims = {
            "service_name": service_name,
            "token_type": "service_token",
            "permissions": permissions or [],
            "service_type": "internal"
        }
        
        return await self.generate_token(
            tenant_guid=tenant_guid,
            claims=service_claims,
            expiration_minutes=expiration_minutes
        )
    
    async def generate_user_token(
        self,
        tenant_guid: str,
        user_id: str,
        user_name: str,
        role: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        expiration_minutes: int = 1440  # 24 hours
    ) -> Optional[TokenGenerationResponse]:
        """
        Generate user authentication JWT token
        
        Args:
            tenant_guid: Tenant GUID
            user_id: User identifier
            user_name: User display name
            role: User role
            permissions: User permissions
            expiration_minutes: Token expiration in minutes
            
        Returns:
            TokenGenerationResponse or None if failed
        """
        user_claims = {
            "sub": user_id,
            "user_id": user_id,
            "user_name": user_name,
            "role": role,
            "token_type": "access_token",
            "permissions": permissions or []
        }
        
        return await self.generate_token(
            tenant_guid=tenant_guid,
            claims=user_claims,
            expiration_minutes=expiration_minutes
        )
    
    async def revoke_tokens_for_key(self, tenant_guid: str, key_id: str) -> bool:
        """
        Revoke all tokens for a specific key (used during key rotation)
        
        Args:
            tenant_guid: Tenant GUID
            key_id: Key ID to revoke tokens for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.cache_service:
                # Clear all JWT validation cache entries for this tenant
                # This forces re-validation and will fail for revoked keys
                cache_stats = await self.cache_service.get_cache_stats()
                keys = await self.cache_service.cache.keys()
                
                for cache_key in keys:
                    if cache_key.startswith("jwt:"):
                        await self.cache_service.cache.delete(cache_key)
                
                logger.info(f"Cleared JWT validation cache for key rotation: {key_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke tokens for key {key_id}: {e}")
            return False
    
    async def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a token without full validation
        
        Args:
            token: JWT token
            
        Returns:
            Dictionary with token information or None if invalid
        """
        try:
            # Decode without verification to get basic info
            header = jwt.get_unverified_header(token)
            payload = jwt.decode(token, options={"verify_signature": False})
            
            return {
                "header": header,
                "payload": payload,
                "key_id": header.get("kid"),
                "tenant_guid": payload.get("tenant_guid"),
                "service_name": payload.get("service_name"),
                "user_id": payload.get("user_id"),
                "expires_at": datetime.fromtimestamp(payload.get("exp", 0)),
                "issued_at": datetime.fromtimestamp(payload.get("iat", 0))
            }
            
        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            return None
    
    def _get_token_hash(self, token: str) -> str:
        """
        Generate hash of token for cache key
        
        Args:
            token: JWT token
            
        Returns:
            SHA256 hash of token
        """
        return hashlib.sha256(token.encode('utf-8')).hexdigest()[:32]
    
    async def _get_tenant_info(self, tenant_guid: str) -> Optional[TenantInfo]:
        """
        Get tenant information from etcd with caching
        
        Args:
            tenant_guid: Tenant GUID
            
        Returns:
            TenantInfo object or None if not found
        """
        try:
            # Try cache first
            if self.cache_service:
                cached_tenant = await self.cache_service.get_tenant_info(tenant_guid)
                if cached_tenant:
                    return TenantInfo.from_dict(json.loads(cached_tenant))
            
            # Get from etcd
            tenant_key = f"tenants/{tenant_guid}"
            tenant_data = await self.etcd_service.get(tenant_key)
            
            if tenant_data:
                tenant_info = TenantInfo.from_dict(json.loads(tenant_data))
                
                # Cache for future use
                if self.cache_service:
                    await self.cache_service.set_tenant_info(
                        tenant_guid, 
                        json.dumps(tenant_info.to_dict())
                    )
                
                return tenant_info
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get tenant info for {tenant_guid}: {e}")
            return None