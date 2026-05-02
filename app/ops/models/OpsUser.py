from tortoise import fields, models
from tortoise.fields import UUIDField
import uuid


class OpsUser(models.Model):
    id = UUIDField(pk=True, default=uuid.uuid4)
    username = fields.CharField(max_length=32, unique=True)
    password_hash = fields.CharField(max_length=255)
    role = fields.CharField(max_length=32, default="super_admin")
    permissions = fields.JSONField(default=list)
    is_active = fields.BooleanField(default=True)
    last_login_at = fields.DatetimeField(timezone=True, null=True)
    created_at = fields.DatetimeField(auto_now_add=True, timezone=True)
    updated_at = fields.DatetimeField(auto_now=True, timezone=True)

    class Meta:
        table = "ops_users"
