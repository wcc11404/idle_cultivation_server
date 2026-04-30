from datetime import datetime, timezone
from typing import Dict, List

from app.game.application.InitPlayerInfo import create_initial_player_data_record
from app.core.security.Security import get_password_hash, verify_password
from app.core.db.Models import Account, PlayerData
from unit_test.support.TestSupportConfig import (
    HUMAN_TEST_USERNAME,
    TEST_PASSWORD,
    TEST_USERNAME,
)


EPOCH_TIME = datetime.fromtimestamp(0, timezone.utc)


async def _ensure_single_test_account(username: str) -> Dict[str, object]:
    account = await Account.get_or_none(username=username)
    created_account = False
    created_player_data = False
    reset_password = False

    password_hash = get_password_hash(TEST_PASSWORD)

    if not account:
        account = await Account.create(
            username=username,
            password_hash=password_hash,
            is_banned=False,
        )
        created_account = True
        reset_password = True
    else:
        updates = []
        if account.is_banned:
            account.is_banned = False
            updates.append("is_banned")
        if not account.password_hash or not verify_password(TEST_PASSWORD, account.password_hash):
            account.password_hash = password_hash
            updates.append("password_hash")
            reset_password = True
        if updates:
            await account.save(update_fields=updates)

    player_data = await PlayerData.get_or_none(account_id=account.id)
    if not player_data:
        await create_initial_player_data_record(account, EPOCH_TIME)
        created_player_data = True

    return {
        "username": username,
        "created_account": created_account,
        "created_player_data": created_player_data,
        "password_reset": reset_password,
    }


async def ensure_test_account_exists() -> dict:
    """确保固定测试账号和基础玩家数据存在。"""
    managed_accounts: List[str] = [TEST_USERNAME, HUMAN_TEST_USERNAME]
    results = []
    for username in managed_accounts:
        results.append(await _ensure_single_test_account(username))
    return {
        "managed_accounts": results
    }
