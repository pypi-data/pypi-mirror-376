"""
Key derivation utilities for D3 Identity Service
Provides PBKDF2 key derivation for secure key generation from passwords
"""

import logging
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class KeyDerivation:
    """
    PBKDF2 key derivation for generating encryption keys from passwords
    Used to derive encryption keys from tenant API keys
    """
    
    def __init__(self):
        """Initialize key derivation manager"""
        self.default_iterations = 100000  # OWASP recommended minimum
        self.default_hash_algorithm = hashes.SHA256()
        logger.debug("KeyDerivation initialized with PBKDF2-HMAC-SHA256")
    
    def derive_key(
        self,
        password: str,
        salt: bytes,
        key_length: int = 32,
        iterations: int = None,
        algorithm=None
    ) -> bytes:
        """
        Derive encryption key from password using PBKDF2
        
        Args:
            password: Password/passphrase to derive from
            salt: Random salt bytes (should be 16+ bytes)
            key_length: Desired key length in bytes (default: 32 for AES-256)
            iterations: PBKDF2 iterations (default: 100000)
            algorithm: Hash algorithm (default: SHA256)
            
        Returns:
            Derived key bytes
        """
        try:
            if iterations is None:
                iterations = self.default_iterations
            if algorithm is None:
                algorithm = self.default_hash_algorithm
            
            # Validate inputs
            if len(salt) < 16:
                raise ValueError("Salt should be at least 16 bytes for security")
            if key_length < 16:
                raise ValueError("Key length should be at least 16 bytes")
            if iterations < 10000:
                logger.warning(f"Low iteration count ({iterations}) - recommend at least 10000")
            
            # Create PBKDF2 instance
            kdf = PBKDF2HMAC(
                algorithm=algorithm,
                length=key_length,
                salt=salt,
                iterations=iterations,
            )
            
            # Derive key
            password_bytes = password.encode('utf-8')
            derived_key = kdf.derive(password_bytes)
            
            logger.debug(f"Key derived: {key_length} bytes using {iterations} iterations")
            return derived_key
            
        except Exception as e:
            logger.error(f"Key derivation failed: {e}")
            raise
    
    def verify_derived_key(
        self,
        password: str,
        salt: bytes,
        expected_key: bytes,
        iterations: int = None,
        algorithm=None
    ) -> bool:
        """
        Verify that password produces expected derived key
        
        Args:
            password: Password to test
            salt: Salt used in original derivation
            expected_key: Expected derived key
            iterations: PBKDF2 iterations (default: 100000)
            algorithm: Hash algorithm (default: SHA256)
            
        Returns:
            True if password produces expected key, False otherwise
        """
        try:
            if iterations is None:
                iterations = self.default_iterations
            if algorithm is None:
                algorithm = self.default_hash_algorithm
            
            # Create PBKDF2 instance
            kdf = PBKDF2HMAC(
                algorithm=algorithm,
                length=len(expected_key),
                salt=salt,
                iterations=iterations,
            )
            
            # Verify key
            password_bytes = password.encode('utf-8')
            kdf.verify(password_bytes, expected_key)
            
            logger.debug("Key verification successful")
            return True
            
        except Exception as e:
            logger.debug(f"Key verification failed: {e}")
            return False
    
    def derive_multiple_keys(
        self,
        password: str,
        salt: bytes,
        key_specs: list,
        iterations: int = None,
        algorithm=None
    ) -> list:
        """
        Derive multiple keys from same password with different parameters
        
        Args:
            password: Password to derive from
            salt: Base salt (will be modified for each key)
            key_specs: List of (key_length, purpose) tuples
            iterations: PBKDF2 iterations (default: 100000)
            algorithm: Hash algorithm (default: SHA256)
            
        Returns:
            List of (derived_key, purpose) tuples
        """
        try:
            derived_keys = []
            
            for i, (key_length, purpose) in enumerate(key_specs):
                # Create unique salt for each key by appending index
                unique_salt = salt + i.to_bytes(4, byteorder='big')
                
                derived_key = self.derive_key(
                    password=password,
                    salt=unique_salt,
                    key_length=key_length,
                    iterations=iterations,
                    algorithm=algorithm
                )
                
                derived_keys.append((derived_key, purpose))
                logger.debug(f"Derived key for purpose: {purpose}")
            
            return derived_keys
            
        except Exception as e:
            logger.error(f"Multiple key derivation failed: {e}")
            raise
    
    def get_recommended_iterations(self, target_time_ms: int = 100) -> int:
        """
        Calculate recommended iteration count based on target computation time
        
        Args:
            target_time_ms: Target computation time in milliseconds
            
        Returns:
            Recommended iteration count
        """
        try:
            import time
            
            # Test with small number of iterations to measure performance
            test_iterations = 1000
            test_password = "test_password_for_timing"
            test_salt = b"test_salt_16byte"
            
            start_time = time.perf_counter()
            self.derive_key(
                password=test_password,
                salt=test_salt,
                iterations=test_iterations
            )
            end_time = time.perf_counter()
            
            # Calculate time per iteration
            time_per_iteration_ms = ((end_time - start_time) * 1000) / test_iterations
            
            # Calculate iterations for target time
            recommended_iterations = max(
                int(target_time_ms / time_per_iteration_ms),
                10000  # Minimum recommended iterations
            )
            
            logger.info(f"Recommended iterations for {target_time_ms}ms: {recommended_iterations}")
            return recommended_iterations
            
        except Exception as e:
            logger.error(f"Failed to calculate recommended iterations: {e}")
            return self.default_iterations
    
    def validate_salt(self, salt: bytes) -> bool:
        """
        Validate salt meets security requirements
        
        Args:
            salt: Salt to validate
            
        Returns:
            True if salt is acceptable, False otherwise
        """
        try:
            # Check minimum length
            if len(salt) < 16:
                logger.warning(f"Salt too short: {len(salt)} bytes, minimum 16 bytes")
                return False
            
            # Check for weak salts
            if salt == b'\x00' * len(salt):
                logger.warning("Salt is all zeros - weak salt")
                return False
            
            # Check entropy - ensure salt is not too repetitive
            unique_bytes = len(set(salt))
            if unique_bytes < 8:
                logger.warning(f"Salt has low entropy: only {unique_bytes} unique bytes")
                return False
            
            logger.debug("Salt validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Salt validation failed: {e}")
            return False