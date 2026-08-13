from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

KEY = b'H*JiOpjzB^6JfLnJ'
IV = b'knVpV!&My7#q0MiH'

def pad(data: bytes) -> bytes:
    padder = padding.PKCS7(128).padder()  # 128 бит = 16 байт
    return padder.update(data) + padder.finalize()

def unpad(data: bytes) -> bytes:
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(data) + unpadder.finalize()

def encrypt_aes(plain: bytes) -> bytes:
    padded = pad(plain)
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(padded) + encryptor.finalize()

def decrypt_aes(ciphertext: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    return unpad(padded)
