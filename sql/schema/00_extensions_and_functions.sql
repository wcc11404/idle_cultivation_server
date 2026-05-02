-- 基础扩展与公共函数
-- 这个文件只放跨子系统复用的数据库能力。

-- 生成 UUID 主键所需扩展。
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 统一维护 updated_at 的触发器函数。
-- 约定：凡是存在 updated_at 的表，都通过这个函数在 UPDATE 时自动刷新时间。
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
