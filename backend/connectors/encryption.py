from cryptography.fernet import Fernet
from django.conf import settings
import base64
import logging

logger = logging.getLogger(__name__)


def get_fernet():
    """
    Returns a Fernet instance using the encryption key from settings.
    Fernet is a symmetric encryption algorithm — the same key
    is used to encrypt and decrypt.
    """
    key = settings.ENCRYPTION_KEY
    if not key:
        raise ValueError("ENCRYPTION_KEY is not set in environment variables.")
    return Fernet(key.encode())


def encrypt_password(password: str) -> str:
    """
    Encrypts a password before storing it in the database.
    Even if someone gets database access, they can't read passwords.
    Returns the encrypted password as a string.
    """
    if not password:
        return ''
    try:
        f = get_fernet()
        encrypted = f.encrypt(password.encode())
        return encrypted.decode()
    except Exception:
        logger.error("Failed to encrypt password.")
        raise ValueError("Encryption failed.")


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypts a password retrieved from the database.
    Only called internally when making actual database connections.
    Returns the original plain text password.
    """
    if not encrypted_password:
        return ''
    try:
        f = get_fernet()
        decrypted = f.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception:
        logger.error("Failed to decrypt password.")
        raise ValueError("Decryption failed.")