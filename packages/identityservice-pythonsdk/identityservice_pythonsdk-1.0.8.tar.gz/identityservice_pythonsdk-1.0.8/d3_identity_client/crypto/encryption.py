"""
AES encryption utilities for D3 Identity Service
Provides AES-256-GCM encryption/decryption for sensitive data
"""

import secrets
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.exceptions import InvalidTag

logger = logging.getLogger(__name__)

class AESEncryption:
    """
    AES-256-GCM encryption for securing sensitive data
    Used primarily for encrypting private keys
    """
    
    def __init__(self):
        """Initialize AES encryption manager"""
        self.key_size = 32  # AES-256 key size in bytes
        self.iv_size = 12   # GCM IV size in bytes
        self.tag_size = 16  # GCM authentication tag size in bytes
        logger.debug("AESEncryption initialized with AES-256-GCM")
    
    def encrypt(self, plaintext: bytes, key: bytes) -> bytes:
        """
        Encrypt plaintext using AES-256-GCM
        
        Args:
            plaintext: Data to encrypt
            key: 32-byte encryption key
            
        Returns:
            Encrypted data with format: IV + ciphertext + tag
        """
        try:
            if len(key) != self.key_size:
                raise ValueError(f"Key must be {self.key_size} bytes, got {len(key)}")
            
            # Generate random IV for GCM
            iv = secrets.token_bytes(self.iv_size)
            
            # Create cipher
            cipher = Cipher(
                algorithm=algorithms.AES(key),
                mode=modes.GCM(iv)
            )
            encryptor = cipher.encryptor()
            
            # Encrypt data
            ciphertext = encryptor.update(plaintext) + encryptor.finalize()
            
            # Get authentication tag
            tag = encryptor.tag
            
            # Combine IV + ciphertext + tag
            encrypted_data = iv + ciphertext + tag
            
            logger.debug(f"Data encrypted: {len(plaintext)} bytes -> {len(encrypted_data)} bytes")
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: bytes, key: bytes) -> bytes:
        """
        Decrypt data using AES-256-GCM
        
        Args:
            encrypted_data: Encrypted data with format: IV + ciphertext + tag
            key: 32-byte decryption key
            
        Returns:
            Decrypted plaintext
        """
        try:
            if len(key) != self.key_size:
                raise ValueError(f"Key must be {self.key_size} bytes, got {len(key)}")
            
            if len(encrypted_data) < (self.iv_size + self.tag_size):
                raise ValueError("Encrypted data too short")
            
            # Extract components
            iv = encrypted_data[:self.iv_size]
            ciphertext = encrypted_data[self.iv_size:-self.tag_size]
            tag = encrypted_data[-self.tag_size:]
            
            # Create cipher
            cipher = Cipher(
                algorithm=algorithms.AES(key),
                mode=modes.GCM(iv, tag)
            )
            decryptor = cipher.decryptor()
            
            # Decrypt data
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            logger.debug(f"Data decrypted: {len(encrypted_data)} bytes -> {len(plaintext)} bytes")
            return plaintext
            
        except InvalidTag:
            logger.error("Decryption failed: Invalid authentication tag")
            raise ValueError("Invalid authentication tag - data may be corrupted or key is incorrect")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def generate_key(self) -> bytes:
        """
        Generate cryptographically secure AES-256 key
        
        Returns:
            32-byte random key
        """
        key = secrets.token_bytes(self.key_size)
        logger.debug("Generated new AES-256 key")
        return key
    
    def encrypt_string(self, plaintext: str, key: bytes, encoding: str = 'utf-8') -> bytes:
        """
        Encrypt string using AES-256-GCM
        
        Args:
            plaintext: String to encrypt
            key: 32-byte encryption key
            encoding: String encoding (default: utf-8)
            
        Returns:
            Encrypted data bytes
        """
        try:
            plaintext_bytes = plaintext.encode(encoding)
            return self.encrypt(plaintext_bytes, key)
        except Exception as e:
            logger.error(f"String encryption failed: {e}")
            raise
    
    def decrypt_string(self, encrypted_data: bytes, key: bytes, encoding: str = 'utf-8') -> str:
        """
        Decrypt data to string using AES-256-GCM
        
        Args:
            encrypted_data: Encrypted data bytes
            key: 32-byte decryption key
            encoding: String encoding (default: utf-8)
            
        Returns:
            Decrypted string
        """
        try:
            plaintext_bytes = self.decrypt(encrypted_data, key)
            return plaintext_bytes.decode(encoding)
        except Exception as e:
            logger.error(f"String decryption failed: {e}")
            raise
    
    def verify_key_strength(self, key: bytes) -> bool:
        """
        Verify that key meets strength requirements
        
        Args:
            key: Key to verify
            
        Returns:
            True if key is strong enough, False otherwise
        """
        try:
            if len(key) != self.key_size:
                logger.warning(f"Key length incorrect: {len(key)} bytes, expected {self.key_size}")
                return False
            
            # Check for weak keys (all zeros, all ones, etc.)
            if key == b'\x00' * self.key_size:
                logger.warning("Key is all zeros - weak key")
                return False
            
            if key == b'\xff' * self.key_size:
                logger.warning("Key is all ones - weak key")
                return False
            
            # Basic entropy check - ensure key is not repetitive
            unique_bytes = len(set(key))
            if unique_bytes < 8:  # Require at least 8 unique bytes
                logger.warning(f"Key has low entropy: only {unique_bytes} unique bytes")
                return False
            
            logger.debug("Key strength verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Key strength verification failed: {e}")
            return False