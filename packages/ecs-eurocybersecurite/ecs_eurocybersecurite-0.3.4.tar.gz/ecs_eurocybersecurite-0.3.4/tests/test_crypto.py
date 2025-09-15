from ecs.crypto import hash_text
import hashlib

def test_hash_text():
    text = "mypassword"
    assert hash_text(text) == hashlib.sha256(text.encode('utf-8')).hexdigest()
