-- 账号表
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 登录方式一：用户名+密码（初期实现）
    username VARCHAR(20) UNIQUE NOT NULL,     -- 必填
    password_hash VARCHAR(255) NOT NULL,      -- 必填
    
    -- 登录方式二：手机号+验证码（后续扩展）
    phone VARCHAR(11) UNIQUE,                 -- 可为空
    
    -- 登录方式三：第三方登录（后续扩展）
    auth_data JSONB,                          -- TapTap 等第三方登录信息
    
    -- 通用字段
    server_id VARCHAR(20) DEFAULT 'default',  -- 区服ID
    token_version INT DEFAULT 0,              -- 单设备登录控制，每次登录+1
    is_banned BOOLEAN DEFAULT FALSE,          -- 封号标记
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 玩家数据表
CREATE TABLE player_data (
    account_id UUID PRIMARY KEY REFERENCES accounts(id),
    server_id VARCHAR(20) DEFAULT 'default',  -- 冗余存储，便于分区查询
    game_version VARCHAR(20) DEFAULT 'v1.0.0', -- 游戏版本号，记录玩家上次保存的版本
    data JSONB NOT NULL,                      -- 所有游戏数据
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_accounts_username ON accounts(username);
CREATE UNIQUE INDEX idx_accounts_phone ON accounts(phone) WHERE phone IS NOT NULL;
CREATE INDEX idx_accounts_server ON accounts(server_id);
CREATE INDEX idx_player_data_updated ON player_data(updated_at);
CREATE INDEX idx_player_data_server ON player_data(server_id);
CREATE INDEX idx_player_data_version ON player_data(game_version);

-- 初始化默认数据
INSERT INTO accounts (username, password_hash) VALUES 
('test', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW'); -- 密码: test123