from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config.ServerConfig import settings
from app.core.db.Models import Account
from app.core.logging.Logger import logger

security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    if len(password) > 72:
        password = password[:72]
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """解码令牌"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Account:
    """获取当前用户"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        logger.warning("[AUTH] INVALID_TOKEN")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_TOKEN"
        )
    
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    
    account = await Account.get_or_none(id=account_id)
    if not account:
        logger.warning(f"[AUTH] ACCOUNT_NOT_FOUND - account_id: {account_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ACCOUNT_NOT_FOUND"
        )
    
    if account.token_version != token_version:
        logger.warning(f"[AUTH] KICKED_OUT - account_id: {account_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="KICKED_OUT"
        )
    
    return account
