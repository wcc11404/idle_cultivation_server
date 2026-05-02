from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.ops.auth.Service import OpsAuthService, ops_security
from app.ops.models import OpsUser


async def get_current_ops_user(
    credentials: HTTPAuthorizationCredentials = Depends(ops_security),
) -> OpsUser:
    return await OpsAuthService.get_current_user(credentials)


def require_ops_permission(permission: str):
    async def _checker(user: OpsUser = Depends(get_current_ops_user)) -> OpsUser:
        permissions = user.permissions if isinstance(user.permissions, list) else []
        if user.role == "super_admin" or permission in permissions:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="OPS_PERMISSION_DENIED")

    return _checker
