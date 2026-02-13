from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

from .models import User

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, token_version: int) -> str:
    expire = timezone.now() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire, "ver": token_version, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, token_version: int) -> str:
    expire = timezone.now() + timedelta(minutes=settings.JWT_REFRESH_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire, "ver": token_version, "type": "refresh"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        return payload
    except JWTError as exc:
        raise ValueError("Invalid token") from exc


def decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        return payload
    except JWTError as exc:
        raise ValueError("Invalid token") from exc


class BearerJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != b"bearer":
            return None
        if len(auth) != 2:
            raise AuthenticationFailed("Invalid token")

        token = auth[1].decode("utf-8")
        try:
            payload = decode_access_token(token)
        except ValueError as exc:
            raise AuthenticationFailed("Invalid token") from exc

        user_id = payload.get("sub")
        token_version = payload.get("ver")
        if user_id is None:
            raise AuthenticationFailed("Invalid token")
        try:
            user = User.objects.get(id=int(user_id))
        except (User.DoesNotExist, ValueError):
            raise AuthenticationFailed("Invalid token")

        if user.token != token_version:
            raise AuthenticationFailed("Invalid token")
        if not user.is_active:
            raise PermissionDenied("탈퇴한 계정입니다.")

        return (user, token)
