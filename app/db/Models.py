from tortoise import fields, models
from tortoise.fields import UUIDField
import uuid


class Account(models.Model):
    """账号模型"""
    id = UUIDField(pk=True, default=uuid.uuid4)
    username = fields.CharField(max_length=20, unique=True, null=False)
    password_hash = fields.CharField(max_length=255, null=False)
    phone = fields.CharField(max_length=11, unique=True, null=True)
    auth_data = fields.JSONField(null=True)
    server_id = fields.CharField(max_length=20, default="default")
    token_version = fields.IntField(default=0)
    is_banned = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True, timezone=True)
    updated_at = fields.DatetimeField(auto_now=True, timezone=True)

    class Meta:
        table = "accounts"


class PlayerData(models.Model):
    """玩家数据模型"""
    account_id = UUIDField(pk=True)
    server_id = fields.CharField(max_length=20, default="default")
    game_version = fields.CharField(max_length=20, default="v1.0.0")
    data = fields.JSONField(null=False)
    last_online_at = fields.DatetimeField(timezone=True)
    last_daily_reset_at = fields.DatetimeField(timezone=True)
    updated_at = fields.DatetimeField(auto_now=True, timezone=True)

    class Meta:
        table = "player_data"


class MailData(models.Model):
    """邮箱邮件模型（软删）"""
    mail_id = fields.CharField(max_length=64, pk=True)
    account_id = UUIDField(index=True)
    title = fields.CharField(max_length=100, null=False)
    content = fields.TextField(null=False)
    attachments = fields.JSONField(default=list)
    created_at = fields.DatetimeField(timezone=True, auto_now_add=True)
    expire_at = fields.DatetimeField(timezone=True, null=True)

    is_read = fields.BooleanField(default=False)
    is_claimed = fields.BooleanField(default=False)
    claimed_at = fields.DatetimeField(timezone=True, null=True)

    is_deleted = fields.BooleanField(default=False, index=True)
    deleted_at = fields.DatetimeField(timezone=True, null=True)

    updated_at = fields.DatetimeField(auto_now=True, timezone=True)

    class Meta:
        table = "mail_data"
