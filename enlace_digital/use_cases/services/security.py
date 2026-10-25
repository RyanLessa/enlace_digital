import os

import bcrypt
import jwt

MAX_BCRYPT_PASSWORD_BYTES = 72
JWT_ALGORITHM = "HS256"
SECRET_KEY = os.environ.get("SECRET_KEY", "default_secret_key")

def hash_password(password: str) -> str:
    password_bytes = _encode_password(password)
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            _encode_password(password),
            password_hash.encode("ascii"),
        )
    except (UnicodeEncodeError, ValueError):
        return False


def create_access_token(user_id: int) -> str:
    secret = SECRET_KEY.encode()
    signing_key = jwt.jwk.OctetJWK(secret, alg=JWT_ALGORITHM)
    return jwt.JWT().encode(
        {"id": user_id},
        key=signing_key,
        alg=JWT_ALGORITHM,
    )


def _encode_password(password: str) -> bytes:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_BCRYPT_PASSWORD_BYTES:
        raise ValueError("Password exceeds bcrypt's 72-byte limit.")
    return password_bytes
