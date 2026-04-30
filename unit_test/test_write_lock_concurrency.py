from __future__ import annotations

import asyncio
import threading
import time
import uuid
from typing import Any

import asyncpg
import requests

from app.core.config.ServerConfig import settings
from unit_test.support.TestSupportConfig import (
    HUMAN_TEST_USERNAME,
    TEST_PASSWORD,
    TEST_USERNAME,
)


def _request_params() -> dict[str, Any]:
    return {
        "operation_id": str(uuid.uuid4()),
        "timestamp": time.time(),
    }


def _login(base_url: str, username: str) -> tuple[str, str]:
    response = requests.post(
        f"{base_url}/auth/login",
        json={
            "username": username,
            "password": TEST_PASSWORD,
            **_request_params(),
        },
    )
    data = response.json()
    assert data.get("success") is True, f"登录失败: username={username}, data={data}"
    return str(data.get("token", "")), str(data.get("account_info", {}).get("id", ""))


def _authed_post(base_url: str, token: str, path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    response = requests.post(
        f"{base_url}{path}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.status_code, response.json()


def _hold_player_row_lock(account_id: str, hold_seconds: float) -> None:
    async def _runner() -> None:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        trx = conn.transaction()
        await trx.start()
        try:
            await conn.execute("SET LOCAL lock_timeout = '5s'")
            await conn.fetchrow(
                "SELECT account_id FROM player_data WHERE account_id = $1 FOR UPDATE",
                account_id,
            )
            await asyncio.sleep(hold_seconds)
        finally:
            await trx.rollback()
            await conn.close()

    asyncio.run(_runner())


def test_same_account_same_endpoint_serialized(reset_client_state, base_url: str):
    token = str(reset_client_state.token)
    avatar_ids = ["serial_avatar_a", "serial_avatar_b"]
    barrier = threading.Barrier(3)
    results: list[tuple[int, dict[str, Any]]] = []

    def _worker(avatar_id: str) -> None:
        barrier.wait()
        results.append(
            _authed_post(
                base_url,
                token,
                "/auth/change_avatar",
                {"avatar_id": avatar_id, **_request_params()},
            )
        )

    t1 = threading.Thread(target=_worker, args=(avatar_ids[0],))
    t2 = threading.Thread(target=_worker, args=(avatar_ids[1],))
    t1.start()
    t2.start()
    barrier.wait()
    t1.join()
    t2.join()

    assert len(results) == 2
    for status_code, body in results:
        assert status_code == 200, body
        assert body.get("success") is True, body

    state = reset_client_state.get_game_data()
    assert state["success"] is True
    final_avatar = state["data"]["account_info"]["avatar_id"]
    assert final_avatar in set(avatar_ids)


def test_same_account_cross_endpoint_no_lost_update(reset_client_state, base_url: str):
    token = str(reset_client_state.token)
    nickname = "并发道友"
    avatar_id = "cross_lock_avatar"
    barrier = threading.Barrier(3)
    results: list[tuple[int, dict[str, Any]]] = []

    def _nickname_worker() -> None:
        barrier.wait()
        results.append(
            _authed_post(
                base_url,
                token,
                "/auth/change_nickname",
                {"nickname": nickname, **_request_params()},
            )
        )

    def _avatar_worker() -> None:
        barrier.wait()
        results.append(
            _authed_post(
                base_url,
                token,
                "/auth/change_avatar",
                {"avatar_id": avatar_id, **_request_params()},
            )
        )

    t1 = threading.Thread(target=_nickname_worker)
    t2 = threading.Thread(target=_avatar_worker)
    t1.start()
    t2.start()
    barrier.wait()
    t1.join()
    t2.join()

    assert len(results) == 2
    for status_code, body in results:
        assert status_code == 200, body
        assert body.get("success") is True, body

    state = reset_client_state.get_game_data()
    assert state["success"] is True
    assert state["data"]["account_info"]["nickname"] == nickname
    assert state["data"]["account_info"]["avatar_id"] == avatar_id


def test_same_account_lock_timeout_returns_conflict(reset_client_state, base_url: str):
    token = str(reset_client_state.token)
    account_id = str(reset_client_state.account_id)
    locker = threading.Thread(target=_hold_player_row_lock, args=(account_id, 2.0))
    locker.start()
    time.sleep(0.2)

    status_code, body = _authed_post(
        base_url,
        token,
        "/auth/change_avatar",
        {"avatar_id": "timeout_avatar", **_request_params()},
    )

    locker.join()
    assert status_code == 409, body
    assert body.get("success") is False
    assert body.get("reason_code") == "GAME_WRITE_CONFLICT_RETRY"
    assert body.get("reason_data", {}).get("retryable") is True
    assert int(body.get("reason_data", {}).get("lock_timeout_ms", 0)) == 1000


def test_different_accounts_do_not_block_each_other(base_url: str):
    token_a, account_id_a = _login(base_url, TEST_USERNAME)
    token_b, _ = _login(base_url, HUMAN_TEST_USERNAME)

    locker = threading.Thread(target=_hold_player_row_lock, args=(account_id_a, 2.0))
    locker.start()
    time.sleep(0.2)

    status_code, body = _authed_post(
        base_url,
        token_b,
        "/auth/change_avatar",
        {"avatar_id": "other_account_avatar", **_request_params()},
    )

    locker.join()
    assert status_code == 200, body
    assert body.get("success") is True
