from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.auth import RegisterRequest, LoginRequest, LoginResponse, RefreshResponse, ErrorResponse, AccountInfo
from app.db.models import Account, PlayerData
from app.core.security import verify_password, get_password_hash, create_access_token, decode_token
from app.core.config import settings
from app.core.config_loader import get_initial_player_data
from datetime import datetime, timedelta, timezone
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=dict)
async def register(request: RegisterRequest):
    """注册账号"""
    existing_account = await Account.get_or_none(username=request.username)
    if existing_account:
        return {"success": False, "error_code": 400, "message": "用户名已存在"}
    
    password_hash = get_password_hash(request.password)
    account = await Account.create(
        username=request.username,
        password_hash=password_hash
    )
    
    initial_data = get_initial_player_data(str(account.id))
    
    await PlayerData.create(
        account_id=account.id,
        data=initial_data
    )
    
    return {"success": True, "account_id": str(account.id), "message": "注册成功"}


@router.post("/login")
async def login(request: LoginRequest):
    """登录账号"""
    account = await Account.get_or_none(username=request.username)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名未注册"
        )
    
    if not verify_password(request.password, account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误"
        )
    
    if account.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被封禁"
        )
    
    account.token_version += 1
    await account.save()
    
    access_token_expires = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"account_id": str(account.id), "version": account.token_version},
        expires_delta=access_token_expires
    )
    
    player_data = await PlayerData.get_or_none(account_id=account.id)
    if not player_data:
        initial_data = get_initial_player_data(str(account.id))
        player_data = await PlayerData.create(
            account_id=account.id,
            data=initial_data
        )
    
    now = datetime.now(timezone.utc)
    last_online = player_data.updated_at
    if last_online.tzinfo is None:
        last_online = last_online.replace(tzinfo=timezone.utc)
    offline_seconds = int((now - last_online).total_seconds())
    offline_seconds = min(offline_seconds, 4 * 3600)
    
    offline_reward = {
        "spirit_energy": int(offline_seconds * 0.1),
        "spirit_stones": int(offline_seconds * 10 / 3600)
    }
    
    await player_data.save()
    
    return {
        "success": True,
        "token": access_token,
        "expires_in": int(access_token_expires.total_seconds()),
        "account_info": {
            "id": str(account.id),
            "username": account.username,
            "server_id": account.server_id
        },
        "data": player_data.data,
        "offline_reward": offline_reward if offline_seconds > 60 else None,
        "offline_seconds": offline_seconds
    }


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Token续期"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_TOKEN"
        )
    
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    
    account = await Account.get_or_none(id=account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ACCOUNT_NOT_FOUND"
        )
    
    if account.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="KICKED_OUT"
        )
    
    # 生成新 token
    access_token_expires = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    new_token = create_access_token(
        data={"account_id": str(account.id), "version": account.token_version},
        expires_delta=access_token_expires
    )
    
    return RefreshResponse(
        success=True,
        token=new_token,
        expires_in=int(access_token_expires.total_seconds())
    )


@router.post("/logout", response_model=dict)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """登出"""
    # 这里可以做一些清理工作，比如记录登出时间等
    return {"success": True, "message": "登出成功"}