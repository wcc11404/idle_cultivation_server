-- 账号与玩家主数据

CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 当前正式登录主键。
    username VARCHAR(20) UNIQUE NOT NULL,
    -- bcrypt 哈希后的密码，不保存明文。
    password_hash VARCHAR(255) NOT NULL,

    -- 预留：手机号登录。
    phone VARCHAR(11) UNIQUE,
    -- 预留：第三方登录原始数据。
    auth_data JSONB,

    -- 区服标识，当前默认单服 default。
    server_id VARCHAR(20) DEFAULT 'default',
    -- 玩家 token 版本号。
    -- 每次重新登录、封禁、强制下线等场景都会提升该值，让旧 token 失效。
    token_version INT DEFAULT 0,
    -- 永久封禁标记。
    is_banned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE player_data (
    -- 与 accounts 一对一，玩家唯一主键直接复用 account_id。
    account_id UUID PRIMARY KEY REFERENCES accounts(id),
    -- 冗余区服字段，便于后续分区查询或多服迁移。
    server_id VARCHAR(20) DEFAULT 'default',
    -- 玩家最近一次存档时的游戏版本，用于后续版本迁移判断。
    game_version VARCHAR(20) DEFAULT 'v1.0.0',
    -- 权威游戏存档 JSON。
    data JSONB NOT NULL,
    -- 玩家最后在线时间，仅在主动赋值后保存时更新。
    last_online_at TIMESTAMPTZ NOT NULL,
    -- 玩家上次执行每日重置的时间，用于跨天任务/副本刷新。
    last_daily_reset_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_accounts_username ON accounts(username);
CREATE UNIQUE INDEX idx_accounts_phone ON accounts(phone) WHERE phone IS NOT NULL;
CREATE INDEX idx_accounts_server ON accounts(server_id);
CREATE INDEX idx_player_data_updated ON player_data(updated_at);
CREATE INDEX idx_player_data_last_online ON player_data(last_online_at);
CREATE INDEX idx_player_data_last_daily_reset ON player_data(last_daily_reset_at);
CREATE INDEX idx_player_data_server ON player_data(server_id);
CREATE INDEX idx_player_data_version ON player_data(game_version);

CREATE TRIGGER update_accounts_updated_at
BEFORE UPDATE ON accounts
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_player_data_updated_at
BEFORE UPDATE ON player_data
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE accounts IS '账号主表：保存登录身份、封禁状态、token 版本等账号级信息。';
COMMENT ON COLUMN accounts.username IS '当前正式登录账号名，服务端校验长度与字符集。';
COMMENT ON COLUMN accounts.password_hash IS 'bcrypt 密码哈希，不保存明文密码。';
COMMENT ON COLUMN accounts.token_version IS '玩家 token 版本号；递增后旧 token 全部失效。';
COMMENT ON COLUMN accounts.is_banned IS '永久封禁标记；true 时游戏登录直接拒绝。';

COMMENT ON TABLE player_data IS '玩家权威存档表：账号一对一，data 字段保存完整游戏 JSON。';
COMMENT ON COLUMN player_data.data IS '完整玩家存档 JSON，包含 account_info/player/inventory 等主线数据。';
COMMENT ON COLUMN player_data.last_online_at IS '最近在线时间，用于活跃度判断与运维查询。';
COMMENT ON COLUMN player_data.last_daily_reset_at IS '最近一次每日重置时间，用于跨天刷新任务和副本次数。';
