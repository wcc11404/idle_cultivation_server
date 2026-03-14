from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.auth import RegisterRequest, LoginRequest, LoginResponse, RefreshResponse, ErrorResponse, AccountInfo
from app.db.models import Account, PlayerData
from app.core.security import verify_password, get_password_hash, create_access_token, decode_token
from app.core.config import settings
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from tortoise.exceptions import IntegrityError

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=dict)
async def register(request: RegisterRequest):
    """注册账号"""
    try:
        # 检查用户名是否已存在
        existing_account = await Account.get_or_none(username=request.username)
        if existing_account:
            return ErrorResponse(error_code=400, message="用户名已存在")
        
        # 创建账号
        password_hash = get_password_hash(request.password)
        account = await Account.create(
            username=request.username,
            password_hash=password_hash
        )
        
        # 创建初始游戏数据
        initial_data = {
            "player": {
                "realm": "炼气期",
                "realm_level": 1,
                "health": 500.0,
                "spirit_energy": 0.0,
                "nickname": f"修仙者{account.id[:6]}",
                "avatar_id": "default_1",
                "title_id": ""
            },
            "inventory": {
                "capacity": 50,
                "slots": {}
            },
            "spell_system": {
                "player_spells": {},
                "equipped_spells": {
                    "tuna": None,
                    "active": [],
                    "passive": []
                }
            },
            "alchemy_system": {
                "equipped_furnace_id": "",
                "learned_recipes": ["health_pill"]
            },
            "lianli_system": {
                "tower_highest_floor": 0,
                "daily_dungeon_data": {}
            },
            "timestamp": int(datetime.now().timestamp())
        }
        
        await PlayerData.create(
            account_id=account.id,
            data=initial_data
        )
        
        return {"success": True, "account_id": str(account.id), "message": "注册成功"}
    except IntegrityError:
        return ErrorResponse(error_code=400, message="用户名已存在")
    except Exception as e:
        return ErrorResponse(error_code=500, message="注册失败")


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """登录账号"""
    # 验证用户名密码
    account = await Account.get_or_none(username=request.username)
    if not account:
        return ErrorResponse(error_code=401, message="用户名或密码错误")
    
    if not verify_password(request.password, account.password_hash):
        return ErrorResponse(error_code=401, message="用户名或密码错误")
    
    if account.is_banned:
        return ErrorResponse(error_code=403, message="账号已被封禁")
    
    # 更新 token_version
    account.token_version += 1
    await account.save()
    
    # 生成 JWT Token
    access_token_expires = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"account_id": str(account.id), "version": account.token_version},
        expires_delta=access_token_expires
    )
    
    # 获取游戏数据
    player_data = await PlayerData.get_or_none(account_id=account.id)
    if not player_data:
        # 创建初始数据
        initial_data = {
            "player": {
                "realm": "炼气期",
                "realm_level": 1,
                "health": 500.0,
                "spirit_energy": 0.0,
                "nickname": f"修仙者{account.id[:6]}",
                "avatar_id": "default_1",
                "title_id": ""
            },
            "inventory": {
                "capacity": 50,
                "slots": {}
            },
            "spell_system": {
                "player_spells": {},
                "equipped_spells": {
                    "tuna": None,
                    "active": [],
                    "passive": []
                }
            },
            "alchemy_system": {
                "equipped_furnace_id": "",
                "learned_recipes": ["health_pill"]
            },
            "lianli_system": {
                "tower_highest_floor": 0,
                "daily_dungeon_data": {}
            },
            "timestamp": int(datetime.now().timestamp())
        }
        player_data = await PlayerData.create(
            account_id=account.id,
            data=initial_data
        )
    
    # 计算离线收益
    offline_seconds = int((datetime.now() - player_data.last_online_at).total_seconds())
    offline_seconds = min(offline_seconds, 4 * 3600)  # 最大4小时
    
    offline_reward = {
        "spirit_energy": int(offline_seconds * 0.1),
        "spirit_stones": int(offline_seconds * 10 / 3600)
    }
    
    # 更新最后在线时间
    player_data.last_online_at = datetime.now()
    await player_data.save()
    
    # 构造响应
    account_info = AccountInfo(
        id=account.id,
        username=account.username,
        server_id=account.server_id
    )
    
    return LoginResponse(
        success=True,
        token=access_token,
        expires_in=int(access_token_expires.total_seconds()),
        account_info=account_info,
        data=player_data.data,
        offline_reward=offline_reward if offline_seconds > 60 else None,
        offline_seconds=offline_seconds
    )


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