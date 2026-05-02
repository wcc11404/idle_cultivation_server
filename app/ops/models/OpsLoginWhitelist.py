from tortoise import fields, models
from tortoise.fields import UUIDField
import uuid


class OpsLoginWhitelist(models.Model):
    id = UUIDField(pk=True, default=uuid.uuid4)
    account_id = UUIDField(unique=True)
    account_username_snapshot = fields.CharField(max_length=32, null=True)
    note = fields.TextField(null=True)
    created_by = fields.CharField(max_length=64, null=True)
    created_at = fields.DatetimeField(auto_now_add=True, timezone=True)
    updated_at = fields.DatetimeField(auto_now=True, timezone=True)

    class Meta:
        table = "ops_login_whitelist"
