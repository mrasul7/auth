
import datetime
import jwt 
import bcrypt
from config import settings
from fastapi.security import HTTPBearer

http_bearer = HTTPBearer()
EXPIRE_ACCESS_TOKEN_MINUTES = 30

def create_access_token(payload: dict) -> str:
    data = payload.copy()
    data["exp"] = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=EXPIRE_ACCESS_TOKEN_MINUTES)
    data["iat"] = datetime.datetime.now(tz=datetime.timezone.utc)
    token = jwt.encode(payload=data, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    return token


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, key=settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token invalid")
    except jwt.InvalidTokenError:
        raise Exception("Token invalid")


def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password=password.encode(), salt=bcrypt.gensalt())

def verify_password(password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(password=password.encode(), hashed_password=hashed_password)

