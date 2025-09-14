"""
Ed25519 cryptographic key management for D3 Identity Service
Provides Ed25519 key pair generation, encryption/decryption, and JWT signing
"""

import base64
import secrets
import logging
from typing import Tuple, Optional
from dataclasses import dataclass
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature
from .encryption import AESEncryption
from .key_derivation import KeyDerivation

logger = logging.getLogger(__name__)

@dataclass
class Ed25519KeyPair:
    """Ed25519 key pair container"""
    public_key: ed25519.Ed25519PublicKey
    private_key: ed25519.Ed25519PrivateKey
    key_id: str
    
    def public_key_pem(self) -> str:
        """Get public key in PEM format"""
        pem_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem_bytes.decode('utf-8')
    
    def private_key_pem(self) -> str:
        """Get private key in PEM format"""
        pem_bytes = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        return pem_bytes.decode('utf-8')
    
    def public_key_base64(self) -> str:
        """Get public key as base64 encoded string"""
        return base64.b64encode(self.public_key_pem().encode('utf-8')).decode('utf-8')
    
    def private_key_base64(self) -> str:
        """Get private key as base64 encoded string"""
        return base64.b64encode(self.private_key_pem().encode('utf-8')).decode('utf-8')

class Ed25519KeyManager:
    """
    Ed25519 key management for JWT signing and tenant authentication
    Handles key generation, encryption/decryption, and format conversions
    """
    
    def __init__(self):
        """Initialize Ed25519 key manager"""
        self.aes_encryption = AESEncryption()
        self.key_derivation = KeyDerivation()
        logger.debug("Ed25519KeyManager initialized")
    
    def generate_key_pair(self, key_id: Optional[str] = None) -> Ed25519KeyPair:
        """
        Generate new Ed25519 key pair
        
        Args:
            key_id: Optional key identifier, generates UUID if not provided
            
        Returns:
            Ed25519KeyPair with generated keys
        """
        try:
            if not key_id:
                key_id = secrets.token_urlsafe(16)
            
            # Generate Ed25519 private key
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            key_pair = Ed25519KeyPair(
                public_key=public_key,
                private_key=private_key,
                key_id=key_id
            )
            
            logger.info(f"Generated Ed25519 key pair with ID: {key_id}")
            return key_pair
            
        except Exception as e:
            logger.error(f"Failed to generate Ed25519 key pair: {e}")
            raise
    
    def generate_key_pair_strings(self, key_id: Optional[str] = None) -> Tuple[str, str, str]:
        """
        Generate Ed25519 key pair and return as base64 encoded strings
        
        Args:
            key_id: Optional key identifier
            
        Returns:
            Tuple of (key_id, public_key_base64, private_key_base64)
        """
        key_pair = self.generate_key_pair(key_id)
        return (
            key_pair.key_id,
            key_pair.public_key_base64(),
            key_pair.private_key_base64()
        )
    
    def encrypt_private_key(self, private_key: str, tenant_api_key: str) -> str:
        """
        Encrypt private key using tenant API key with AES-256-GCM
        
        Args:
            private_key: Private key in base64 or PEM format
            tenant_api_key: Tenant API key for encryption
            
        Returns:
            Base64 encoded encrypted private key
        """
        try:
            # Ensure private key is in proper format
            if private_key.startswith('-----BEGIN'):
                # Already PEM format
                private_key_bytes = private_key.encode('utf-8')
            else:
                # Assume base64 encoded PEM
                private_key_bytes = base64.b64decode(private_key.encode('utf-8'))
            
            # Derive encryption key from tenant API key
            salt = secrets.token_bytes(16)
            derived_key = self.key_derivation.derive_key(
                password=tenant_api_key,
                salt=salt,
                iterations=100000,
                key_length=32
            )
            
            # Encrypt private key
            encrypted_data = self.aes_encryption.encrypt(private_key_bytes, derived_key)
            
            # Combine salt + encrypted_data and encode as base64
            combined_data = salt + encrypted_data
            encrypted_private_key = base64.b64encode(combined_data).decode('utf-8')
            
            logger.debug("Private key encrypted successfully")
            return encrypted_private_key
            
        except Exception as e:
            logger.error(f"Failed to encrypt private key: {e}")
            raise
    
    def decrypt_private_key(self, encrypted_private_key: str, tenant_api_key: str) -> ed25519.Ed25519PrivateKey:
        """
        Decrypt private key using tenant API key
        
        Args:
            encrypted_private_key: Base64 encoded encrypted private key
            tenant_api_key: Tenant API key for decryption
            
        Returns:
            Ed25519PrivateKey object
        """
        try:
            # Decode from base64
            combined_data = base64.b64decode(encrypted_private_key.encode('utf-8'))
            
            # Extract salt and encrypted data
            salt = combined_data[:16]
            encrypted_data = combined_data[16:]
            
            # Derive decryption key
            derived_key = self.key_derivation.derive_key(
                password=tenant_api_key,
                salt=salt,
                iterations=100000,
                key_length=32
            )
            
            # Decrypt private key
            private_key_bytes = self.aes_encryption.decrypt(encrypted_data, derived_key)
            
            # Load private key from PEM
            private_key = serialization.load_pem_private_key(
                private_key_bytes, 
                password=None
            )
            
            if not isinstance(private_key, ed25519.Ed25519PrivateKey):
                raise ValueError("Decrypted key is not an Ed25519 private key")
            
            logger.debug("Private key decrypted successfully")
            return private_key
            
        except Exception as e:
            logger.error(f"Failed to decrypt private key: {e}")
            raise
    
    def load_public_key(self, public_key: str) -> ed25519.Ed25519PublicKey:
        """
        Load Ed25519 public key from string
        
        Args:
            public_key: Public key in base64 encoded PEM or raw PEM format
            
        Returns:
            Ed25519PublicKey object
        """
        try:
            # Handle different input formats
            if public_key.startswith('-----BEGIN'):
                # Already PEM format
                public_key_bytes = public_key.encode('utf-8')
            else:
                # Assume base64 encoded PEM
                public_key_bytes = base64.b64decode(public_key.encode('utf-8'))
            
            # Load public key from PEM
            loaded_key = serialization.load_pem_public_key(public_key_bytes)
            
            if not isinstance(loaded_key, ed25519.Ed25519PublicKey):
                raise ValueError("Key is not an Ed25519 public key")
            
            logger.debug("Public key loaded successfully")
            return loaded_key
            
        except Exception as e:
            logger.error(f"Failed to load public key: {e}")
            raise
    
    def load_private_key(self, private_key: str) -> ed25519.Ed25519PrivateKey:
        """
        Load Ed25519 private key from string
        
        Args:
            private_key: Private key in base64 encoded PEM or raw PEM format
            
        Returns:
            Ed25519PrivateKey object
        """
        try:
            # Handle different input formats
            if private_key.startswith('-----BEGIN'):
                # Already PEM format
                private_key_bytes = private_key.encode('utf-8')
            else:
                # Assume base64 encoded PEM
                private_key_bytes = base64.b64decode(private_key.encode('utf-8'))
            
            # Load private key from PEM
            loaded_key = serialization.load_pem_private_key(
                private_key_bytes,
                password=None
            )
            
            if not isinstance(loaded_key, ed25519.Ed25519PrivateKey):
                raise ValueError("Key is not an Ed25519 private key")
            
            logger.debug("Private key loaded successfully")
            return loaded_key
            
        except Exception as e:
            logger.error(f"Failed to load private key: {e}")
            raise
    
    def sign_data(self, data: bytes, private_key: ed25519.Ed25519PrivateKey) -> bytes:
        """
        Sign data using Ed25519 private key
        
        Args:
            data: Data to sign
            private_key: Ed25519 private key for signing
            
        Returns:
            Signature bytes
        """
        try:
            signature = private_key.sign(data)
            logger.debug(f"Data signed successfully, signature length: {len(signature)}")
            return signature
            
        except Exception as e:
            logger.error(f"Failed to sign data: {e}")
            raise
    
    def verify_signature(
        self, 
        data: bytes, 
        signature: bytes, 
        public_key: ed25519.Ed25519PublicKey
    ) -> bool:
        """
        Verify signature using Ed25519 public key
        
        Args:
            data: Original data that was signed
            signature: Signature to verify
            public_key: Ed25519 public key for verification
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            public_key.verify(signature, data)
            logger.debug("Signature verification successful")
            return True
            
        except InvalidSignature:
            logger.debug("Signature verification failed")
            return False
        except Exception as e:
            logger.error(f"Error during signature verification: {e}")
            return False
    
    def validate_key_pair(self, public_key: str, private_key: str) -> bool:
        """
        Validate that public and private keys form a valid pair
        
        Args:
            public_key: Public key string
            private_key: Private key string
            
        Returns:
            True if keys form a valid pair, False otherwise
        """
        try:
            # Load both keys
            pub_key = self.load_public_key(public_key)
            priv_key = self.load_private_key(private_key)
            
            # Generate test data and sign it
            test_data = b"test_key_pair_validation"
            signature = self.sign_data(test_data, priv_key)
            
            # Verify signature with public key
            is_valid = self.verify_signature(test_data, signature, pub_key)
            
            if is_valid:
                logger.debug("Key pair validation successful")
            else:
                logger.warning("Key pair validation failed - keys do not match")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Key pair validation error: {e}")
            return False
    
    def get_public_key_from_private(self, private_key: ed25519.Ed25519PrivateKey) -> ed25519.Ed25519PublicKey:
        """
        Extract public key from private key
        
        Args:
            private_key: Ed25519 private key
            
        Returns:
            Corresponding Ed25519 public key
        """
        try:
            public_key = private_key.public_key()
            logger.debug("Public key extracted from private key")
            return public_key
            
        except Exception as e:
            logger.error(f"Failed to extract public key from private key: {e}")
            raise