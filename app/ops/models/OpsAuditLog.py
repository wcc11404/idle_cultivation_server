from tortoise import fields, models
from tortoise.fields import UUIDField
import uuid


class OpsAuditLog(models.Model):
    id = UUIDField(pk=True, default=uuid.uuid4)
    operator_user_id = UUIDField(null=True)
    operator_username = fields.CharField(max_length=32, null=True)
    action_type = fields.CharField(max_length=64)
    target_scope = fields.CharField(max_length=32, default="single")
    target_payload = fields.JSONField(default=dict)
    request_payload = fields.JSONField(default=dict)
    result = fields.CharField(max_length=16, default="success")
    reason_code = fields.CharField(max_length=128, null=True)
    ip = fields.CharField(max_length=64, null=True)
    user_agent = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True, timezone=True)

    class Meta:
        table = "ops_audit_logs"
