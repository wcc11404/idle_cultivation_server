from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.auth import RegisterRequest, LoginRequest, LoginResponse, RefreshResponse, ErrorResponse, AccountInfo, ChangePasswordRequest, ChangePasswordResponse, ChangeNicknameRequest, ChangeNicknameResponse, ChangeAvatarRequest, ChangeAvatarResponse
from app.db.Models import Account, PlayerData
from app.core.Security import verify_password, get_password_hash, create_access_token, decode_token, security, get_current_user
from app.core.ServerConfig import settings
from app.core.InitPlayerInfo import get_initial_player_data
from app.core.Logger import logger
from app.core.AntiCheatSystem import AntiCheatSystem
from app.core.Validator import Validator
from app.modules import PlayerSystem as GamePlayerData, AccountSystem
from datetime import datetime, timedelta, timezone
from fastapi.security import HTTPAuthorizationCredentials
import time
import json

router = APIRouter()


@router.post("/register", response_model=dict)
async def register(request: RegisterRequest):
    """注册账号"""
    start_time = time.time()
    logger.info(f"[IN] POST /auth/register - {json.dumps(request.dict(), ensure_ascii=False)}")
    
    is_valid, message = Validator.validate_username(request.username)
    if not is_valid:
        logger.info(f"[OUT] POST /auth/register - {message} - 耗时: {time.time() - start_time:.4f}s")
        return {
            "success": False,
            "operation_id": request.operation_id,
            "timestamp": request.timestamp,
            "error_code": 400,
            "message": message
        }
    
    is_valid, message = Validator.validate_password(request.password)
    if not is_valid:
        logger.info(f"[OUT] POST /auth/register - {message} - 耗时: {time.time() - start_time:.4f}s")
        return {
            "success": False,
            "operation_id": request.operation_id,
            "timestamp": request.timestamp,
            "error_code": 400,
            "message": message
        }
    
    is_valid, message = Validator.validate_username_password_different(request.username, request.password)
    if not is_valid:
        logger.info(f"[OUT] POST /auth/register - {message} - 耗时: {time.time() - start_time:.4f}s")
        return {
            "success": False,
            "operation_id": request.operation_id,
            "timestamp": request.timestamp,
            "error_code": 400,
            "message": message
        }
    
    existing_account = await Account.get_or_none(username=request.username)
    if existing_account:
        logger.info(f"[OUT] POST /auth/register - 用户名已存在 - 耗时: {time.time() - start_time:.4f}s")
        return {
            "success": False,
            "operation_id": request.operation_id,
            "timestamp": request.timestamp,
            "error_code": 400,
            "message": "用户名已存在"
        }
    
    password_hash = get_password_hash(request.password)
    account = await Account.create(
        username=request.username,
        password_hash=password_hash
    )
    
    initial_data = get_initial_player_data(str(account.id))
    
    # 为新注册用户设置一个特殊的 last_online_at 值（使用 epoch 时间0）
    from datetime import datetime, timezone
    epoch_time = datetime.fromtimestamp(0, timezone.utc)
    
    await PlayerData.create(
        account_id=account.id,
        data=initial_data,
        last_online_at=epoch_time
    )
    
    # 为新注册用户生成初始token
    access_token_expires = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"account_id": str(account.id), "version": account.token_version},
        expires_delta=access_token_expires
    )
    
    response_data = {
        "success": True,
        "operation_id": request.operation_id,
        "timestamp": request.timestamp,
        "account_id": str(account.id),
        "token": access_token,
        "message": "注册成功"
    }
    logger.info(f"[OUT] POST /auth/register - {json.dumps(response_data, ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/login")
async def login(request: LoginRequest):
    """登录账号"""
    start_time = time.time()
    logger.info(f"[IN] POST /auth/login - {json.dumps(request.dict(), ensure_ascii=False)}")
    
    account = await Account.get_or_none(username=request.username)
    if not account:
        logger.warning(f"[OUT] POST /auth/login - 用户名未注册 - username: {request.username} - 耗时: {time.time() - start_time:.4f}s")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名未注册"
        )
    
    if not verify_password(request.password, account.password_hash):
        logger.warning(f"[OUT] POST /auth/login - 密码错误 - username: {request.username} - 耗时: {time.time() - start_time:.4f}s")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误"
        )
    
    if account.is_banned:
        logger.warning(f"[OUT] POST /auth/login - 账号已被封禁 - username: {request.username} - 耗时: {time.time() - start_time:.4f}s")
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
    
    # 检查是否需要每日重置
    def check_daily_reset(player_data):
        from datetime import datetime, timezone, timedelta
        current_time = datetime.now(timezone.utc)
        last_login = player_data.last_online_at
        
        # 计算上次登录日期和当前日期（基于重置时间）
        def get_reset_date(t):
            reset_time = t.replace(hour=settings.DAILY_RESET_HOUR, minute=0, second=0, microsecond=0)
            if t < reset_time:
                return reset_time - timedelta(days=1)
            return reset_time
        
        last_reset_date = get_reset_date(last_login)
        current_reset_date = get_reset_date(current_time)
        
        # 如果日期不同，执行重置
        if last_reset_date != current_reset_date:
            logger.info(f"[GAME] 执行每日重置 - account_id: {account.id}")
            # 重置破镜草洞穴次数
            if "lianli_system" in player_data.data and "daily_dungeon_data" in player_data.data["lianli_system"]:
                daily_dungeon_data = player_data.data["lianli_system"]["daily_dungeon_data"]
                if "foundation_herb_cave" in daily_dungeon_data:
                    max_count = daily_dungeon_data["foundation_herb_cave"].get("max_count", 3)
                    daily_dungeon_data["foundation_herb_cave"]["remaining_count"] = max_count
            return True
        return False
    
    # 执行每日重置检查
    if check_daily_reset(player_data):
        await player_data.save()
    
    # 首次登录时，将 last_online_at 从 epoch 0 更新为当前时间
    from datetime import datetime, timezone
    epoch_time = datetime.fromtimestamp(0, timezone.utc)
    if player_data.last_online_at == epoch_time:
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
    
    response_data = {
        "success": True,
        "operation_id": request.operation_id,
        "timestamp": request.timestamp,
        "token": access_token,
        "expires_in": int(access_token_expires.total_seconds()),
        "account_info": {
            "id": str(account.id),
            "username": account.username,
            "server_id": account.server_id
        },
        "data": player_data.data
    }
    logger.info(f"[OUT] POST /auth/login - {json.dumps(response_data, ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Token续期"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id") if payload else ""
    token_version = payload.get("version") if payload else ""
    logger.info(f"[IN] POST /auth/refresh - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    if not payload:
        logger.warning(f"[OUT] POST /auth/refresh - INVALID_TOKEN - 耗时: {time.time() - start_time:.4f}s")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_TOKEN"
        )
    
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    
    account = await Account.get_or_none(id=account_id)
    if not account:
        logger.warning(f"[OUT] POST /auth/refresh - ACCOUNT_NOT_FOUND - account_id: {account_id} - 耗时: {time.time() - start_time:.4f}s")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ACCOUNT_NOT_FOUND"
        )
    
    if account.token_version != token_version:
        logger.warning(f"[OUT] POST /auth/refresh - KICKED_OUT - account_id: {account_id} - 耗时: {time.time() - start_time:.4f}s")
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
    
    response_data = RefreshResponse(
        success=True,
        token=new_token,
        expires_in=int(access_token_expires.total_seconds())
    )
    logger.info(f"[OUT] POST /auth/refresh - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/logout", response_model=dict)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """登出"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id") if payload else ""
    token_version = payload.get("version") if payload else ""
    logger.info(f"[IN] POST /auth/logout - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    current_user = await get_current_user(credentials)
    
    player_data = await PlayerData.get_or_none(account_id=current_user.id)
    if player_data:
        db_data = player_data.data
        
        if db_data.get("player", {}).get("is_cultivating", False):
            db_data["player"]["is_cultivating"] = False
            logger.info(f"[GAME] 登出时停止修炼 - account_id: {current_user.id}")
        
        account_system = AccountSystem.from_dict(db_data.get("account_info", {}))
        await AntiCheatSystem.reset_suspicious_operations(
            account_id=str(current_user.id),
            account_system=account_system,
            db_player_data=player_data
        )
        
        db_data["account_info"] = account_system.to_dict()
        player_data.data = db_data
        await player_data.save()
    
    response_data = {"success": True, "message": "登出成功"}
    logger.info(f"[OUT] POST /auth/logout - {json.dumps(response_data, ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/change_password", response_model=ChangePasswordResponse)
async def change_password(request: ChangePasswordRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """修改密码"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id") if payload else ""
    token_version = payload.get("version") if payload else ""
    logger.info(f"[IN] POST /auth/change_password - account_id: {account_id} - token_version: {token_version}")
    
    current_user = await get_current_user(credentials)
    
    account = await Account.get_or_none(id=current_user.id)
    if not account:
        logger.warning(f"[OUT] POST /auth/change_password - 账号不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账号不存在"
        )
    
    if not verify_password(request.old_password, account.password_hash):
        logger.warning(f"[OUT] POST /auth/change_password - 旧密码错误 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    if request.old_password == request.new_password:
        logger.warning(f"[OUT] POST /auth/change_password - 新密码不能与旧密码相同 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与旧密码相同"
        )
    
    if account.username == request.new_password:
        logger.warning(f"[OUT] POST /auth/change_password - 新密码不能与用户名相同 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与用户名相同"
        )
    
    account.password_hash = get_password_hash(request.new_password)
    account.token_version += 1
    await account.save()
    
    access_token_expires = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    new_token = create_access_token(
        data={"account_id": str(account.id), "version": account.token_version},
        expires_delta=access_token_expires
    )
    
    response_data = ChangePasswordResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        message="密码修改成功"
    )
    logger.info(f"[OUT] POST /auth/change_password - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/change_nickname", response_model=ChangeNicknameResponse)
async def change_nickname(request: ChangeNicknameRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """修改昵称"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id") if payload else ""
    token_version = payload.get("version") if payload else ""
    logger.info(f"[IN] POST /auth/change_nickname - nickname: {request.nickname} - account_id: {account_id} - token_version: {token_version}")
    
    is_valid, message = Validator.validate_nickname(request.nickname)
    if not is_valid:
        logger.info(f"[OUT] POST /auth/change_nickname - {message} - 耗时: {time.time() - start_time:.4f}s")
        return ChangeNicknameResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            nickname=request.nickname,
            message=message
        )
    
    current_user = await get_current_user(credentials)
    
    player_data = await PlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[OUT] POST /auth/change_nickname - 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    if "account_info" not in db_data:
        db_data["account_info"] = {}
    
    db_data["account_info"]["nickname"] = request.nickname
    player_data.data = db_data
    await player_data.save()
    
    response_data = ChangeNicknameResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        nickname=request.nickname,
        message="昵称修改成功"
    )
    logger.info(f"[OUT] POST /auth/change_nickname - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/change_avatar", response_model=ChangeAvatarResponse)
async def change_avatar(request: ChangeAvatarRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """修改头像"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id") if payload else ""
    token_version = payload.get("version") if payload else ""
    logger.info(f"[IN] POST /auth/change_avatar - avatar_id: {request.avatar_id} - account_id: {account_id} - token_version: {token_version}")
    
    current_user = await get_current_user(credentials)
    
    player_data = await PlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[OUT] POST /auth/change_avatar - 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    if "account_info" not in db_data:
        db_data["account_info"] = {}
    
    db_data["account_info"]["avatar_id"] = request.avatar_id
    player_data.data = db_data
    await player_data.save()
    
    response_data = ChangeAvatarResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        avatar_id=request.avatar_id,
        message="头像修改成功"
    )
    logger.info(f"[OUT] POST /auth/change_avatar - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data



