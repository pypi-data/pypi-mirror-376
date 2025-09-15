import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_LEN = 12

def encrypt_file(src: str, dst: str, key: bytes, aad: bytes = b""):
    aes = AESGCM(key)
    with open(src, "rb") as f: pt = f.read()
    nonce = os.urandom(NONCE_LEN)
    ct = aes.encrypt(nonce, pt, aad)
    with open(dst, "wb") as f: f.write(nonce + ct)

def decrypt_file(src: str, dst: str, key: bytes, aad: bytes = b""):
    with open(src, "rb") as f: blob = f.read()
    nonce, ct = blob[:NONCE_LEN], blob[NONCE_LEN:]
    aes = AESGCM(key)
    pt = aes.decrypt(nonce, ct, aad)
    with open(dst, "wb") as f: f.write(pt)
