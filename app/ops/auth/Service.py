from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid
from typing import Any

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config.ServerConfig import settings
from app.core.db.Models import Account
from app.core.security.Security import create_access_token, decode_token, get_password_hash, verify_password
from app.ops.models import OpsAuthToken, OpsLoginWhitelist, OpsSystemState, OpsUser

ops_security = HTTPBearer()
OPS_TOKEN_EXPIRE_HOURS = 24
OPS_DEFAULT_PERMISSIONS = [
    "player.view",
    "player.ban",
    "player.kick",
    "grant.item",
    "grant.mail",
    "system.view",
    "system.control",
    "audit.view",
]


class OpsAuthService:
    @staticmethod
    async def ensure_bootstrap_data() -> None:
        await OpsSystemState.get_or_create(
            id=1,
            defaults={
                "login_gate_enabled": False,
                "login_gate_note": "initial",
            },
        )
        exists = await OpsUser.filter(username=settings.OPS_BOOTSTRAP_USERNAME).exists()
        if not exists:
            await OpsUser.create(
                username=settings.OPS_BOOTSTRAP_USERNAME,
                password_hash=get_password_hash(settings.OPS_BOOTSTRAP_PASSWORD),
                role="super_admin",
                permissions=OPS_DEFAULT_PERMISSIONS,
                is_active=True,
            )
        await OpsAuthService.ensure_default_whitelist_accounts()

    @staticmethod
    async def ensure_default_whitelist_accounts() -> None:
        for username in ("test", "test2"):
            account = await Account.get_or_none(username=username)
            if not account:
                continue
            await OpsLoginWhitelist.update_or_create(
                defaults={
                    "account_username_snapshot": account.username,
                    "note": "default test whitelist",
                    "created_by": "system_init",
                },
                account_id=account.id,
            )

    @staticmethod
    async def login(username: str, password: str) -> dict[str, Any]:
        user = await OpsUser.get_or_none(username=username)
        if not user or not user.is_active or not verify_password(password, user.password_hash):
            return {
                "success": False,
                "reason_code": "OPS_LOGIN_INVALID_CREDENTIALS",
                "reason_data": {"username": username},
            }

        expires_at = datetime.now(timezone.utc) + timedelta(hours=OPS_TOKEN_EXPIRE_HOURS)
        jti = uuid.uuid4().hex
        token = create_access_token(
            {
                "ops": True,
                "ops_user_id": str(user.id),
                "ops_username": user.username,
                "ops_role": user.role,
                "jti": jti,
            },
            expires_delta=timedelta(hours=OPS_TOKEN_EXPIRE_HOURS),
        )
        await OpsAuthToken.create(user_id=user.id, token_jti=jti, expires_at=expires_at)
        user.last_login_at = datetime.now(timezone.utc)
        await user.save()
        return {
            "success": True,
            "reason_code": "OPS_LOGIN_SUCCEEDED",
            "reason_data": {"username": username},
            "token": token,
            "expires_in": int(timedelta(hours=OPS_TOKEN_EXPIRE_HOURS).total_seconds()),
            "user": OpsAuthService.serialize_user(user),
        }

    @staticmethod
    async def logout(token: str) -> dict[str, Any]:
        payload = decode_token(token) or {}
        jti = str(payload.get("jti", ""))
        if not jti:
            return {"success": True, "reason_code": "OPS_LOGOUT_SUCCEEDED", "reason_data": {}}
        row = await OpsAuthToken.get_or_none(token_jti=jti)
        if row and row.revoked_at is None:
            row.revoked_at = datetime.now(timezone.utc)
            await row.save()
        return {"success": True, "reason_code": "OPS_LOGOUT_SUCCEEDED", "reason_data": {}}

    @staticmethod
    async def get_user_by_token(token: str) -> OpsUser:
        payload = decode_token(token)
        if not payload or not payload.get("ops"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OPS_INVALID_TOKEN")
        user_id = str(payload.get("ops_user_id", ""))
        jti = str(payload.get("jti", ""))
        user = await OpsUser.get_or_none(id=user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OPS_USER_NOT_FOUND")
        token_row = await OpsAuthToken.get_or_none(token_jti=jti, user_id=user.id)
        if not token_row or token_row.revoked_at is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OPS_TOKEN_REVOKED")
        if token_row.expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OPS_TOKEN_EXPIRED")
        return user

    @staticmethod
    async def get_current_user(credentials: HTTPAuthorizationCredentials) -> OpsUser:
        return await OpsAuthService.get_user_by_token(credentials.credentials)

    @staticmethod
    def serialize_user(user: OpsUser) -> dict[str, Any]:
        return {
            "id": str(user.id),
            "username": user.username,
            "role": user.role,
            "permissions": user.permissions if isinstance(user.permissions, list) else [],
            "is_active": bool(user.is_active),
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        }
