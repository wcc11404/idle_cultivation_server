-- 邮箱系统

CREATE TABLE mail_data (
    mail_id VARCHAR(64) PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES accounts(id),
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    -- 邮件附件 JSON 数组，元素结构由服务端 MailSystem 维护。
    attachments JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expire_at TIMESTAMPTZ NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    is_claimed BOOLEAN NOT NULL DEFAULT FALSE,
    claimed_at TIMESTAMPTZ NULL,
    -- 软删除标记。客户端列表默认过滤 true 的记录。
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_mail_data_account_id ON mail_data(account_id);
CREATE INDEX idx_mail_data_created_at ON mail_data(created_at DESC);
CREATE INDEX idx_mail_data_is_deleted ON mail_data(is_deleted);

CREATE TRIGGER update_mail_data_updated_at
BEFORE UPDATE ON mail_data
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE mail_data IS '玩家邮箱表：支持已读、已领取、软删除、附件发放。';
COMMENT ON COLUMN mail_data.attachments IS '附件 JSON 数组；单封邮件的附件发放真值。';
COMMENT ON COLUMN mail_data.is_claimed IS '附件是否已整体领取；避免重复发奖。';
COMMENT ON COLUMN mail_data.is_deleted IS '软删除标记；不直接物理删，便于审计和回溯。';
