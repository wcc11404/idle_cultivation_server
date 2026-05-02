-- 运维系统表

CREATE TABLE IF NOT EXISTS ops_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(32) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    -- 当前一期默认角色字段，后续可扩展更细权限模型。
    role VARCHAR(32) NOT NULL DEFAULT 'super_admin',
    -- 权限列表 JSON，当前主要为扩展预留。
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_system_state (
    -- 固定单行全局状态表，当前约定唯一记录 id=1。
    id INT PRIMARY KEY,
    -- 登录闸门总开关；开启后只有白名单账号允许进入游戏。
    login_gate_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    login_gate_updated_by VARCHAR(64) NULL,
    login_gate_updated_at TIMESTAMPTZ NULL,
    login_gate_note TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_login_whitelist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- 白名单真值使用 account_id，而不是昵称，避免名字变更带来歧义。
    account_id UUID UNIQUE NOT NULL REFERENCES accounts(id),
    -- 冗余用户名快照，便于后台列表展示与历史排查。
    account_username_snapshot VARCHAR(32) NULL,
    note TEXT NULL,
    created_by VARCHAR(64) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_user_id UUID NULL,
    operator_username VARCHAR(32) NULL,
    action_type VARCHAR(64) NOT NULL,
    -- 目标范围：single / batch / all 等。
    target_scope VARCHAR(32) NOT NULL DEFAULT 'single',
    -- 操作目标的结构化描述，例如账号列表、全服标记、邮件目标等。
    target_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- 原始请求参数快照，用于长期审计回溯。
    request_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result VARCHAR(16) NOT NULL DEFAULT 'success',
    reason_code VARCHAR(128) NULL,
    ip VARCHAR(64) NULL,
    user_agent TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_auth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    -- 运维 token 的 jti，用于登出和显式撤销。
    token_jti VARCHAR(64) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_action_confirms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_user_id UUID NOT NULL,
    action_type VARCHAR(64) NOT NULL,
    -- preview/confirm 两段式高危操作确认令牌。
    confirm_token VARCHAR(64) UNIQUE NOT NULL,
    request_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ops_users_username ON ops_users(username);
CREATE INDEX IF NOT EXISTS idx_ops_audit_logs_action_type ON ops_audit_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_ops_audit_logs_created_at ON ops_audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ops_auth_tokens_user_id ON ops_auth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_ops_action_confirms_operator_user_id ON ops_action_confirms(operator_user_id);

INSERT INTO ops_system_state (id, login_gate_enabled, login_gate_note)
VALUES (1, FALSE, 'initial')
ON CONFLICT (id) DO NOTHING;

INSERT INTO ops_login_whitelist (account_id, account_username_snapshot, note, created_by)
SELECT id, username, 'default test whitelist', 'sql_init'
FROM accounts
WHERE username IN ('test', 'test2')
ON CONFLICT (account_id) DO UPDATE
SET account_username_snapshot = EXCLUDED.account_username_snapshot,
    note = EXCLUDED.note,
    created_by = EXCLUDED.created_by;

CREATE TRIGGER update_ops_users_updated_at
BEFORE UPDATE ON ops_users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ops_system_state_updated_at
BEFORE UPDATE ON ops_system_state
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ops_login_whitelist_updated_at
BEFORE UPDATE ON ops_login_whitelist
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE ops_users IS '运维账号表：与玩家账号隔离的后台登录身份。';
COMMENT ON COLUMN ops_users.role IS '运维角色；一期默认 super_admin，后续可扩展更细角色。';
COMMENT ON COLUMN ops_users.permissions IS '权限 JSON 数组；当前主要作后续扩展预留。';

COMMENT ON TABLE ops_system_state IS '全局运维状态表：当前主要承载登录闸门。';
COMMENT ON COLUMN ops_system_state.login_gate_enabled IS '登录闸门；true 时只有白名单账号可以登录游戏。';
COMMENT ON COLUMN ops_system_state.login_gate_note IS '登录闸门备注，记录维护说明或开启原因。';

COMMENT ON TABLE ops_login_whitelist IS '登录闸门白名单表：当登录闸门开启时，这里的账号仍可进入游戏。';
COMMENT ON COLUMN ops_login_whitelist.account_id IS '白名单账号真值主键；避免使用可变昵称。';
COMMENT ON COLUMN ops_login_whitelist.account_username_snapshot IS '加入白名单时的用户名快照，便于后台展示。';

COMMENT ON TABLE ops_audit_logs IS '运维审计日志：永久保留的后台操作流水。';
COMMENT ON COLUMN ops_audit_logs.target_payload IS '目标对象结构化快照，例如 account_ids、all_accounts 等。';
COMMENT ON COLUMN ops_audit_logs.request_payload IS '原始请求快照，用于追溯具体发放/封禁参数。';
COMMENT ON COLUMN ops_audit_logs.result IS '操作结果，通常为 success 或 failed。';

COMMENT ON TABLE ops_auth_tokens IS '运维 token 台账：支持登出、撤销与过期检查。';
COMMENT ON COLUMN ops_auth_tokens.token_jti IS 'JWT 唯一标识；用于判断 token 是否已撤销。';

COMMENT ON TABLE ops_action_confirms IS '高危操作二次确认表：承载 preview/confirm 两段式确认令牌。';
COMMENT ON COLUMN ops_action_confirms.confirm_token IS '高危操作确认令牌；confirm 阶段必须带回。';
COMMENT ON COLUMN ops_action_confirms.request_payload IS 'preview 阶段冻结下来的请求快照，confirm 时按此执行。';
