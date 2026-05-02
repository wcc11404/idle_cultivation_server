from tortoise import fields, models


class OpsSystemState(models.Model):
    id = fields.IntField(pk=True)
    login_gate_enabled = fields.BooleanField(default=False)
    login_gate_updated_by = fields.CharField(max_length=64, null=True)
    login_gate_updated_at = fields.DatetimeField(timezone=True, null=True)
    login_gate_note = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True, timezone=True)
    updated_at = fields.DatetimeField(auto_now=True, timezone=True)

    class Meta:
        table = "ops_system_state"
