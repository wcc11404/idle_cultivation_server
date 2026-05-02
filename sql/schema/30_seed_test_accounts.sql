-- 默认测试账号
-- 说明：密码哈希对应明文 test123。

INSERT INTO accounts (username, password_hash, is_banned) VALUES
('test', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', FALSE),
('test2', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', FALSE)
ON CONFLICT (username) DO UPDATE
SET password_hash = EXCLUDED.password_hash,
    is_banned = FALSE;
