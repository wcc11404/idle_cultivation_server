from datetime import datetime, timezone

from app.core.InitPlayerInfo import create_initial_player_data_record
from app.core.Security import get_password_hash, verify_password
from app.db.Models import Account, PlayerData
from unit_test.support.test_support_config import TEST_PASSWORD, TEST_USERNAME


EPOCH_TIME = datetime.fromtimestamp(0, timezone.utc)


async def ensure_test_account_exists() -> dict:
    """确保固定测试账号和基础玩家数据存在。"""
    account = await Account.get_or_none(username=TEST_USERNAME)
    created_account = False
    created_player_data = False
    reset_password = False

    password_hash = get_password_hash(TEST_PASSWORD)

    if not account:
        account = await Account.create(
            username=TEST_USERNAME,
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
        "username": TEST_USERNAME,
        "created_account": created_account,
        "created_player_data": created_player_data,
        "password_reset": reset_password,
    }
