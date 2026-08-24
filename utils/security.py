import hashlib
import os

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """
    Hashes a password using PBKDF2 with SHA-256 and salt.
    Returns (hashed_password_hex, salt_hex).
    """
    if not salt:
        salt_bytes = os.urandom(16)
        salt = salt_bytes.hex()
    else:
        salt_bytes = bytes.fromhex(salt)
    
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_bytes,
        100000
    )
    return key.hex(), salt

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """
    Verifies a password against a stored PBKDF2 SHA-256 hash and salt.
    """
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == stored_hash
