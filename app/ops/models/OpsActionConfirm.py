from tortoise import fields, models
from tortoise.fields import UUIDField
import uuid


class OpsActionConfirm(models.Model):
    id = UUIDField(pk=True, default=uuid.uuid4)
    operator_user_id = UUIDField(index=True)
    action_type = fields.CharField(max_length=64)
    confirm_token = fields.CharField(max_length=64, unique=True)
    request_payload = fields.JSONField(default=dict)
    expires_at = fields.DatetimeField(timezone=True)
    used_at = fields.DatetimeField(timezone=True, null=True)
    created_at = fields.DatetimeField(auto_now_add=True, timezone=True)

    class Meta:
        table = "ops_action_confirms"
