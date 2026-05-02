from tortoise import fields, models
from tortoise.fields import UUIDField
import uuid


class OpsAuthToken(models.Model):
    id = UUIDField(pk=True, default=uuid.uuid4)
    user_id = UUIDField(index=True)
    token_jti = fields.CharField(max_length=64, unique=True)
    expires_at = fields.DatetimeField(timezone=True)
    revoked_at = fields.DatetimeField(timezone=True, null=True)
    created_at = fields.DatetimeField(auto_now_add=True, timezone=True)

    class Meta:
        table = "ops_auth_tokens"
