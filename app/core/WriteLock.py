from __future__ import annotations

import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Optional

from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

from app.core.Logger import logger
from app.db.Models import Account, PlayerData


WRITE_LOCK_TIMEOUT_MS = 1000
WRITE_LOCK_TIMEOUT_SQL = "1s"
WRITE_CONFLICT_REASON_CODE = "GAME_WRITE_CONFLICT_RETRY"


@dataclass
class LockedResources:
    connection: object
    account: Optional[Account]
    player_data: Optional[PlayerData]
    wait_ms: int


class WriteConflictError(Exception):
    def __init__(self, *, endpoint: str, account_id: str = "", wait_ms: int = WRITE_LOCK_TIMEOUT_MS):
        super().__init__(WRITE_CONFLICT_REASON_CODE)
        self.endpoint = endpoint
        self.account_id = account_id
        self.wait_ms = wait_ms


def is_lock_timeout_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    return "lock timeout" in text


def build_write_conflict_payload() -> dict:
    return {
        "success": False,
        "operation_id": None,
        "timestamp": None,
        "reason_code": WRITE_CONFLICT_REASON_CODE,
        "reason_data": {
            "retryable": True,
            "lock_timeout_ms": WRITE_LOCK_TIMEOUT_MS,
        },
    }


@asynccontextmanager
async def begin_write_lock_by_account_id(
    *,
    endpoint: str,
    account_id: str,
    token_version: Optional[int] = None,
    lock_player: bool = True,
    allow_missing_account: bool = False,
) -> AsyncIterator[LockedResources]:
    lock_start = time.monotonic()
    try:
        async with in_transaction() as conn:
            await conn.execute_query(f"SET LOCAL lock_timeout = '{WRITE_LOCK_TIMEOUT_SQL}'")

            account = await Account.filter(id=account_id).using_db(conn).select_for_update().first()
            if not account and not allow_missing_account:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="ACCOUNT_NOT_FOUND",
                )

            if account and token_version is not None and account.token_version != token_version:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="KICKED_OUT",
                )

            player_data = None
            if lock_player and account:
                player_data = await PlayerData.filter(account_id=account.id).using_db(conn).select_for_update().first()

            wait_ms = int((time.monotonic() - lock_start) * 1000)
            logger.info(
                f"[LOCK] write lock acquired - endpoint: {endpoint} - account_id: {account_id} "
                f"- wait_ms: {wait_ms} - timed_out: False"
            )
            yield LockedResources(connection=conn, account=account, player_data=player_data, wait_ms=wait_ms)
    except Exception as exc:
        if is_lock_timeout_error(exc):
            wait_ms = int((time.monotonic() - lock_start) * 1000)
            logger.warning(
                f"[LOCK] write lock timeout - endpoint: {endpoint} - account_id: {account_id} "
                f"- wait_ms: {wait_ms} - timed_out: True"
            )
            raise WriteConflictError(endpoint=endpoint, account_id=account_id, wait_ms=wait_ms) from exc
        raise


@asynccontextmanager
async def begin_write_lock_by_username(
    *,
    endpoint: str,
    username: str,
    lock_player: bool = True,
    allow_missing_account: bool = False,
) -> AsyncIterator[LockedResources]:
    lock_start = time.monotonic()
    try:
        async with in_transaction() as conn:
            await conn.execute_query(f"SET LOCAL lock_timeout = '{WRITE_LOCK_TIMEOUT_SQL}'")
            account = await Account.filter(username=username).using_db(conn).select_for_update().first()
            if account is None and not allow_missing_account:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="ACCOUNT_NOT_FOUND",
                )

            player_data = None
            account_id = ""
            if account is not None:
                account_id = str(account.id)
                if lock_player:
                    player_data = await PlayerData.filter(account_id=account.id).using_db(conn).select_for_update().first()

            wait_ms = int((time.monotonic() - lock_start) * 1000)
            logger.info(
                f"[LOCK] write lock acquired - endpoint: {endpoint} - account_id: {account_id} "
                f"- wait_ms: {wait_ms} - timed_out: False"
            )
            yield LockedResources(connection=conn, account=account, player_data=player_data, wait_ms=wait_ms)
    except Exception as exc:
        if is_lock_timeout_error(exc):
            wait_ms = int((time.monotonic() - lock_start) * 1000)
            logger.warning(
                f"[LOCK] write lock timeout - endpoint: {endpoint} - username: {username} "
                f"- wait_ms: {wait_ms} - timed_out: True"
            )
            raise WriteConflictError(endpoint=endpoint, wait_ms=wait_ms) from exc
        raise
