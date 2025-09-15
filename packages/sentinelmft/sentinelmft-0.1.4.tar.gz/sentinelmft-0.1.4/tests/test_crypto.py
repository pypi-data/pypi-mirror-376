from src.sentinelmft.crypto.aesgcm import encrypt_file, decrypt_file
import os, tempfile

def test_roundtrip():
    key = b"x"*32
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "a.txt")
        enc = os.path.join(d, "a.enc")
        out = os.path.join(d, "a.out")
        open(src,"wb").write(b"hello")
        encrypt_file(src, enc, key)
        decrypt_file(enc, out, key)
        assert open(out,"rb").read() == b"hello"

