from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.Auth import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse, RefreshResponse, ChangePasswordRequest, ChangePasswordResponse, ChangeNicknameRequest, ChangeNicknameResponse, ChangeAvatarRequest, ChangeAvatarResponse, LogoutResponse
from app.db.Models import Account, PlayerData
from app.core.Security import verify_password, get_password_hash, create_access_token, decode_token, security
from app.core.ServerConfig import settings
from app.core.InitPlayerInfo import create_initial_player_data_record
from app.core.Logger import logger
from app.core.AntiCheatSystem import AntiCheatSystem
from app.core.Validator import Validator
from app.core.Dependencies import get_write_game_context, get_token_info, GameContext
from app.core.WriteLock import begin_write_lock_by_username
from app.modules import PlayerSystem as GamePlayerData, AccountSystem, SpellSystem
from app.modules.player.PlayerSystem import PlayerSystem
from app.modules.alchemy.AlchemySystem import AlchemySystem
from app.modules.lianli.LianliSystem import LianliSystem
from app.modules.herb.HerbGatherSystem import HerbGatherSystem
from app.modules.task.TaskSystem import TaskSystem
from datetime import datetime, timedelta, timezone
from fastapi.security import HTTPAuthorizationCredentials
import time
import json

router = APIRouter()


EPOCH_TIME = datetime.fromtimestamp(0, timezone.utc)

NICKNAME_REASON_CODE_MAP = {
    "昵称不能为空": "ACCOUNT_NICKNAME_EMPTY",
    "昵称长度必须在4-10位之间": "ACCOUNT_NICKNAME_LENGTH_INVALID",
    "昵称不能包含空格": "ACCOUNT_NICKNAME_CONTAINS_SPACE",
    "昵称包含非法字符": "ACCOUNT_NICKNAME_INVALID_CHARACTER",
    "昵称不能全是数字": "ACCOUNT_NICKNAME_ALL_DIGITS",
    "昵称包含敏感词汇": "ACCOUNT_NICKNAME_SENSITIVE"
}

USERNAME_REASON_CODE_MAP = {
    "用户名不能为空": "ACCOUNT_REGISTER_USERNAME_EMPTY",
    "用户名长度必须在4-20位之间": "ACCOUNT_REGISTER_USERNAME_LENGTH_INVALID",
    "用户名只能包含英文、数字和下划线": "ACCOUNT_REGISTER_USERNAME_INVALID_CHARACTER"
}

PASSWORD_REASON_CODE_MAP = {
    "密码不能为空": "ACCOUNT_REGISTER_PASSWORD_EMPTY",
    "密码长度必须在6-20位之间": "ACCOUNT_REGISTER_PASSWORD_LENGTH_INVALID",
    "密码只能包含英文、数字和英文标点符号": "ACCOUNT_REGISTER_PASSWORD_INVALID_CHARACTER"
}

USERNAME_PASSWORD_REASON_CODE_MAP = {
    "用户名和密码不能相同": "ACCOUNT_REGISTER_USERNAME_PASSWORD_SAME"
}

LOGIN_REASON_CODE_MAP = {
    "username_not_found": "ACCOUNT_LOGIN_USERNAME_NOT_FOUND",
    "password_incorrect": "ACCOUNT_LOGIN_PASSWORD_INCORRECT",
    "account_banned": "ACCOUNT_LOGIN_ACCOUNT_BANNED"
}

CHANGE_PASSWORD_REASON_CODE_MAP = {
    "account_not_found": "ACCOUNT_PASSWORD_CHANGE_ACCOUNT_NOT_FOUND",
    "old_password_incorrect": "ACCOUNT_PASSWORD_CHANGE_OLD_PASSWORD_INCORRECT",
    "same_as_old": "ACCOUNT_PASSWORD_CHANGE_SAME_AS_OLD",
    "same_as_username": "ACCOUNT_PASSWORD_CHANGE_SAME_AS_USERNAME"
}


async def _reset_runtime_state(
    *,
    account_id: str,
    player_data: PlayerData,
    player_system: PlayerSystem,
    alchemy_system: AlchemySystem,
    lianli_system: LianliSystem,
    herb_system: HerbGatherSystem,
    account_system: AccountSystem,
    source: str
) -> dict:
    """统一重置登录态运行时状态（登录/登出复用）"""
    player_system.reset_cultivation_state()
    alchemy_system.reset_alchemy_state()
    lianli_system.reset_battle_state()
    herb_system.reset_gather_state()
    await AntiCheatSystem.reset_suspicious_operations(
        account_id=account_id,
        account_system=account_system,
        db_player_data=player_data
    )
    db_data = player_data.data if isinstance(player_data.data, dict) else {}
    db_data["player"] = player_system.to_dict()
    db_data["alchemy_system"] = alchemy_system.to_dict()
    db_data["lianli_system"] = lianli_system.to_dict()
    db_data["herb_system"] = herb_system.to_dict()
    db_data["account_info"] = account_system.to_dict()
    player_data.data = db_data
    logger.info(
        f"[AUTH] {source} reset runtime state - account_id: {account_id} "
        f"- suspicious_count={account_system.suspicious_operations_count} "
        f"- suspicious_type={account_system.suspicious_operation_type}"
    )
    return db_data


@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest):
    """注册账号"""
    start_time = time.time()
    logger.info(f"[IN] POST /auth/register - {json.dumps(request.dict(), ensure_ascii=False)}")
    
    is_valid, message = Validator.validate_username(request.username)
    if not is_valid:
        logger.info(f"[OUT] POST /auth/register - {message} - 耗时: {time.time() - start_time:.4f}s")
        return RegisterResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code=USERNAME_REASON_CODE_MAP.get(message, "ACCOUNT_REGISTER_USERNAME_INVALID"),
            reason_data={"username": request.username}
        )
    
    is_valid, message = Validator.validate_password(request.password)
    if not is_valid:
        logger.info(f"[OUT] POST /auth/register - {message} - 耗时: {time.time() - start_time:.4f}s")
        return RegisterResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code=PASSWORD_REASON_CODE_MAP.get(message, "ACCOUNT_REGISTER_PASSWORD_INVALID"),
            reason_data={"username": request.username}
        )
    
    is_valid, message = Validator.validate_username_password_different(request.username, request.password)
    if not is_valid:
        logger.info(f"[OUT] POST /auth/register - {message} - 耗时: {time.time() - start_time:.4f}s")
        return RegisterResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code=USERNAME_PASSWORD_REASON_CODE_MAP.get(message, "ACCOUNT_REGISTER_USERNAME_PASSWORD_INVALID"),
            reason_data={"username": request.username}
        )
    
    existing_account = await Account.get_or_none(username=request.username)
    if existing_account:
        logger.info(f"[OUT] POST /auth/register - 用户名已存在 - 耗时: {time.time() - start_time:.4f}s")
        return RegisterResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="ACCOUNT_REGISTER_USERNAME_EXISTS",
            reason_data={"username": request.username}
        )
    
    password_hash = get_password_hash(request.password)
    account = await Account.create(
        username=request.username,
        password_hash=password_hash
    )
    
    # 为新注册用户设置一个特殊的 last_online_at 值（使用 epoch 时间0）
    await create_initial_player_data_record(account, EPOCH_TIME)
    
    # 为新注册用户生成初始token
    access_token_expires = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"account_id": str(account.id), "version": account.token_version},
        expires_delta=access_token_expires
    )
    
    response_data = RegisterResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code="ACCOUNT_REGISTER_SUCCEEDED",
        reason_data={"username": request.username},
        token=access_token
    )
    logger.info(f"[OUT] POST /auth/register - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """登录账号"""
    start_time = time.time()
    logger.info(f"[IN] POST /auth/login - {json.dumps(request.dict(), ensure_ascii=False)}")
    
    async with begin_write_lock_by_username(
        endpoint="POST /api/auth/login",
        username=request.username,
        lock_player=True,
        allow_missing_account=True,
    ) as locked:
        account = locked.account
        player_data = locked.player_data
        if not account:
            logger.warning(f"[OUT] POST /auth/login - 用户名未注册 - username: {request.username} - 耗时: {time.time() - start_time:.4f}s")
            return LoginResponse(
                success=False,
                operation_id=request.operation_id,
                timestamp=request.timestamp,
                reason_code=LOGIN_REASON_CODE_MAP["username_not_found"],
                reason_data={"username": request.username},
                token="",
                expires_in=0,
                account_info={"id": "00000000-0000-0000-0000-000000000000", "username": "", "server_id": ""},
                data={}
            )

        if not verify_password(request.password, account.password_hash):
            logger.warning(f"[OUT] POST /auth/login - 密码错误 - username: {request.username} - 耗时: {time.time() - start_time:.4f}s")
            return LoginResponse(
                success=False,
                operation_id=request.operation_id,
                timestamp=request.timestamp,
                reason_code=LOGIN_REASON_CODE_MAP["password_incorrect"],
                reason_data={"username": request.username},
                token="",
                expires_in=0,
                account_info={"id": "00000000-0000-0000-0000-000000000000", "username": "", "server_id": ""},
                data={}
            )

        if account.is_banned:
            logger.warning(f"[OUT] POST /auth/login - 账号已被封禁 - username: {request.username} - 耗时: {time.time() - start_time:.4f}s")
            return LoginResponse(
                success=False,
                operation_id=request.operation_id,
                timestamp=request.timestamp,
                reason_code=LOGIN_REASON_CODE_MAP["account_banned"],
                reason_data={"username": request.username},
                token="",
                expires_in=0,
                account_info={"id": "00000000-0000-0000-0000-000000000000", "username": "", "server_id": ""},
                data={}
            )

        account.token_version += 1
        await account.save()

        access_token_expires = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
        access_token = create_access_token(
            data={"account_id": str(account.id), "version": account.token_version},
            expires_delta=access_token_expires
        )

        if not player_data:
            player_data = await create_initial_player_data_record(account, EPOCH_TIME)
    
        # 检查是否需要每日重置
        current_time = datetime.now(timezone.utc)
        last_login = player_data.last_online_at

        def get_reset_date(t):
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            else:
                t = t.astimezone(timezone.utc)
            reset_time = t.replace(hour=settings.DAILY_RESET_HOUR, minute=0, second=0, microsecond=0)
            if t < reset_time:
                return reset_time - timedelta(days=1)
            return reset_time

        last_reset_date = get_reset_date(last_login)
        current_reset_date = get_reset_date(current_time)
        if last_reset_date != current_reset_date:
            logger.info(f"[GAME] 执行每日重置 - account_id: {account.id}")
            lianli_system_data = player_data.data.get("lianli_system", {})
            lianli_system = LianliSystem.from_dict(lianli_system_data)
            lianli_system.reset_daily_dungeons()
            player_data.data["lianli_system"] = lianli_system.to_dict()
            task_system_data = player_data.data.get("task_system", {})
            task_system = TaskSystem.from_dict(task_system_data)
            task_system.reset_daily_state()
            player_data.data["task_system"] = task_system.to_dict()

        player_dict = player_data.data.get("player", {})
        login_spell = SpellSystem.from_dict(player_data.data.get("spell_system", {}))
        login_player = GamePlayerData(
            health=float(player_dict.get("health", 100.0)),
            spirit_energy=float(player_dict.get("spirit_energy", 0.0)),
            realm=player_dict.get("realm", "炼气期"),
            realm_level=player_dict.get("realm_level", 1),
            spell_system=login_spell
        )
        login_player.is_cultivating = bool(player_dict.get("is_cultivating", False))
        login_player.last_cultivation_report_time = float(player_dict.get("last_cultivation_report_time", 0.0))
        login_player.cultivation_effect_carry_seconds = float(player_dict.get("cultivation_effect_carry_seconds", 0.0))
        login_alchemy = AlchemySystem.from_dict(player_data.data.get("alchemy_system", {}))
        login_lianli = LianliSystem.from_dict(player_data.data.get("lianli_system", {}))
        login_herb = HerbGatherSystem.from_dict(player_data.data.get("herb_system", {}))
        login_account = AccountSystem.from_dict(player_data.data.get("account_info", {}))
        await _reset_runtime_state(
            account_id=str(account.id),
            player_data=player_data,
            player_system=login_player,
            alchemy_system=login_alchemy,
            lianli_system=login_lianli,
            herb_system=login_herb,
            account_system=login_account,
            source="login"
        )

        await player_data.save()

        response_data = LoginResponse(
            success=True,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="ACCOUNT_LOGIN_SUCCEEDED",
            reason_data={"username": request.username},
            token=access_token,
            expires_in=int(access_token_expires.total_seconds()),
            account_info={
                "id": str(account.id),
                "username": account.username,
                "server_id": account.server_id
            },
            data=player_data.data
        )
        logger.info(f"[OUT] POST /auth/login - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
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
        reason_code="ACCOUNT_REFRESH_SUCCEEDED",
        reason_data={},
        token=new_token,
        expires_in=int(access_token_expires.total_seconds())
    )
    logger.info(f"[OUT] POST /auth/refresh - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info)
):
    """登出"""
    start_time = time.time()
    logger.info(f"[IN] POST /auth/logout - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    reset_db_data = await _reset_runtime_state(
        account_id=str(ctx.account.id),
        player_data=ctx.player_data,
        player_system=ctx.player,
        alchemy_system=ctx.alchemy_system,
        lianli_system=ctx.lianli_system,
        herb_system=ctx.herb_system,
        account_system=ctx.account_system,
        source="logout"
    )
    ctx.db_data = reset_db_data
    # 更新上次登录时间
    ctx.player_data.last_online_at = datetime.now(timezone.utc)
    await ctx.player_data.save()
    
    response_data = LogoutResponse(
        success=True,
        reason_code="ACCOUNT_LOGOUT_SUCCEEDED",
        reason_data={}
    )
    logger.info(f"[OUT] POST /auth/logout - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/change_password", response_model=ChangePasswordResponse)
async def change_password(request: ChangePasswordRequest):
    """修改密码"""
    start_time = time.time()
    logger.info(f"[IN] POST /auth/change_password - username: {request.username}")
    
    async with begin_write_lock_by_username(
        endpoint="POST /api/auth/change_password",
        username=request.username,
        lock_player=True,
        allow_missing_account=True,
    ) as locked:
        account = locked.account
        player_data = locked.player_data

        if not account:
            logger.warning(f"[OUT] POST /auth/change_password - 账号不存在 - username: {request.username}")
            return ChangePasswordResponse(
                success=False,
                operation_id=request.operation_id,
                timestamp=request.timestamp,
                reason_code=CHANGE_PASSWORD_REASON_CODE_MAP["account_not_found"],
                reason_data={"username": request.username}
            )

        if not verify_password(request.old_password, account.password_hash):
            logger.warning(f"[OUT] POST /auth/change_password - 旧密码错误 - username: {request.username}")
            return ChangePasswordResponse(
                success=False,
                operation_id=request.operation_id,
                timestamp=request.timestamp,
                reason_code=CHANGE_PASSWORD_REASON_CODE_MAP["old_password_incorrect"],
                reason_data={"username": request.username}
            )

        if request.old_password == request.new_password:
            logger.warning(f"[OUT] POST /auth/change_password - 新密码不能与旧密码相同 - username: {request.username}")
            return ChangePasswordResponse(
                success=False,
                operation_id=request.operation_id,
                timestamp=request.timestamp,
                reason_code=CHANGE_PASSWORD_REASON_CODE_MAP["same_as_old"],
                reason_data={"username": request.username}
            )

        if account.username == request.new_password:
            logger.warning(f"[OUT] POST /auth/change_password - 新密码不能与用户名相同 - username: {request.username}")
            return ChangePasswordResponse(
                success=False,
                operation_id=request.operation_id,
                timestamp=request.timestamp,
                reason_code=CHANGE_PASSWORD_REASON_CODE_MAP["same_as_username"],
                reason_data={"username": request.username}
            )

        account.password_hash = get_password_hash(request.new_password)
        account.token_version += 1
        await account.save()

        if player_data:
            player_data.last_online_at = datetime.now(timezone.utc)
            await player_data.save()

        response_data = ChangePasswordResponse(
            success=True,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="ACCOUNT_PASSWORD_CHANGE_SUCCEEDED",
            reason_data={"username": request.username}
        )
        logger.info(f"[OUT] POST /auth/change_password - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
        return response_data


@router.post("/change_nickname", response_model=ChangeNicknameResponse)
async def change_nickname(
    request: ChangeNicknameRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info)
):
    """修改昵称"""
    start_time = time.time()
    logger.info(
        f"[IN] POST /auth/change_nickname - nickname: {request.nickname} - "
        f"account_id: {token_info['account_id']} - token_version: {token_info['token_version']}"
    )
    
    is_valid, message = Validator.validate_nickname(request.nickname)
    if not is_valid:
        logger.info(f"[OUT] POST /auth/change_nickname - {message} - 耗时: {time.time() - start_time:.4f}s")
        return ChangeNicknameResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            nickname=request.nickname,
            reason_code=NICKNAME_REASON_CODE_MAP.get(message, "ACCOUNT_NICKNAME_INVALID"),
            reason_data={
                "nickname": request.nickname
            }
        )
    
    player_data = ctx.player_data
    db_data = player_data.data
    if "account_info" not in db_data:
        db_data["account_info"] = {}
    
    db_data["account_info"]["nickname"] = request.nickname
    player_data.data = db_data
    # 更新上次登录时间
    player_data.last_online_at = datetime.now(timezone.utc)
    await player_data.save()
    
    response_data = ChangeNicknameResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        nickname=request.nickname,
        reason_code="ACCOUNT_NICKNAME_CHANGE_SUCCEEDED",
        reason_data={
            "nickname": request.nickname
        }
    )
    logger.info(f"[OUT] POST /auth/change_nickname - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/change_avatar", response_model=ChangeAvatarResponse)
async def change_avatar(
    request: ChangeAvatarRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info)
):
    """修改头像"""
    start_time = time.time()
    logger.info(
        f"[IN] POST /auth/change_avatar - avatar_id: {request.avatar_id} - "
        f"account_id: {token_info['account_id']} - token_version: {token_info['token_version']}"
    )

    player_data = ctx.player_data
    db_data = player_data.data
    if "account_info" not in db_data:
        db_data["account_info"] = {}
    
    db_data["account_info"]["avatar_id"] = request.avatar_id
    player_data.data = db_data
    # 更新上次登录时间
    player_data.last_online_at = datetime.now(timezone.utc)
    await player_data.save()
    
    response_data = ChangeAvatarResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        avatar_id=request.avatar_id,
        reason_code="ACCOUNT_AVATAR_CHANGE_SUCCEEDED",
        reason_data={"avatar_id": request.avatar_id}
    )
    logger.info(f"[OUT] POST /auth/change_avatar - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data
