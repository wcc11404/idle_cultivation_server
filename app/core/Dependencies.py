"""
API依赖注入

提供统一的依赖注入函数，减少API中的重复代码
"""

import copy
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from app.core.Security import get_current_user, decode_token, security
from app.db.Models import PlayerData, Account
from app.modules import PlayerSystem, SpellSystem, InventorySystem, AlchemySystem, LianliSystem, HerbGatherSystem, AccountSystem, TaskSystem
from app.core.Logger import logger
from app.core.DailyReset import run_daily_reset_if_needed
from app.core.WriteLock import begin_write_lock_by_account_id
from dataclasses import dataclass


@dataclass
class GameContext:
    """游戏上下文，包含所有游戏系统"""
    account: Account
    player_data: PlayerData
    db_data: Dict[str, Any]
    player: PlayerSystem
    spell_system: SpellSystem
    inventory_system: InventorySystem
    alchemy_system: AlchemySystem
    lianli_system: LianliSystem
    herb_system: HerbGatherSystem
    task_system: TaskSystem
    account_system: AccountSystem
    
    def save(self):
        """保存所有系统数据到db_data"""
        self.db_data["player"] = self.player.to_dict()
        self.db_data["spell_system"] = self.spell_system.to_dict()
        self.db_data["inventory"] = self.inventory_system.to_dict()
        self.db_data["alchemy_system"] = self.alchemy_system.to_dict()
        self.db_data["lianli_system"] = self.lianli_system.to_dict()
        self.db_data["herb_system"] = self.herb_system.to_dict()
        self.db_data["task_system"] = self.task_system.to_dict()
        self.db_data["account_info"] = self.account_system.to_dict()
        self.player_data.data = copy.deepcopy(self.db_data)


def _build_game_context(account: Account, player_data: PlayerData) -> GameContext:
    db_data = copy.deepcopy(player_data.data)

    spell_system = SpellSystem.from_dict(db_data.get("spell_system", {}))
    inventory_system = InventorySystem.from_dict(db_data.get("inventory", {}))
    alchemy_system = AlchemySystem.from_dict(db_data.get("alchemy_system", {}))
    lianli_system = LianliSystem.from_dict(db_data.get("lianli_system", {}))
    herb_system = HerbGatherSystem.from_dict(db_data.get("herb_system", {}))
    task_system = TaskSystem.from_dict(db_data.get("task_system", {}))
    account_system = AccountSystem.from_dict(db_data.get("account_info", {}))

    player_data_dict = db_data.get("player", {})
    player = PlayerSystem(
        health=float(player_data_dict.get("health", 100.0)),
        spirit_energy=float(player_data_dict.get("spirit_energy", 0.0)),
        realm=player_data_dict.get("realm", "炼气期"),
        realm_level=player_data_dict.get("realm_level", 1),
        spell_system=spell_system
    )
    player.is_cultivating = player_data_dict.get("is_cultivating", False)
    player.last_cultivation_report_time = player_data_dict.get("last_cultivation_report_time", 0.0)
    player.cultivation_effect_carry_seconds = float(player_data_dict.get("cultivation_effect_carry_seconds", 0.0))

    return GameContext(
        account=account,
        player_data=player_data,
        db_data=db_data,
        player=player,
        spell_system=spell_system,
        inventory_system=inventory_system,
        alchemy_system=alchemy_system,
        lianli_system=lianli_system,
        herb_system=herb_system,
        task_system=task_system,
        account_system=account_system
    )


async def get_game_context(credentials: HTTPAuthorizationCredentials = Depends(security)) -> GameContext:
    """
    获取游戏上下文（依赖注入）
    
    自动处理：
    1. Token验证
    2. 玩家数据加载
    3. 各系统初始化
    
    Returns:
        GameContext: 包含所有游戏系统的上下文对象
    """
    current_user = await get_current_user(credentials)
    
    player_data = await PlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    return _build_game_context(current_user, player_data)


async def get_write_game_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> GameContext:
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        logger.warning("[AUTH] INVALID_TOKEN")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_TOKEN"
        )

    account_id = str(payload.get("account_id", ""))
    token_version = payload.get("version")
    endpoint = f"{request.method} {request.url.path}"
    async with begin_write_lock_by_account_id(
        endpoint=endpoint,
        account_id=account_id,
        token_version=token_version,
        lock_player=True,
    ) as locked:
        if not locked.player_data:
            logger.warning(f"[GAME] 玩家数据不存在 - account_id: {account_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="玩家数据不存在"
            )
        run_daily_reset_if_needed(locked.player_data)
        yield _build_game_context(locked.account, locked.player_data)


async def get_token_info(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    获取token信息（依赖注入）
    
    Returns:
        dict: 包含token, account_id, token_version的字典
    """
    token = credentials.credentials
    payload = decode_token(token) or {}
    return {
        "token": token,
        "account_id": payload.get("account_id"),
        "token_version": payload.get("version")
    }
