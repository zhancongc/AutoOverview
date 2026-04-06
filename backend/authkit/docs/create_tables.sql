-- PostgreSQL 表结构（参考 snappicker 项目）
-- 数据库: paper
-- 用户: postgres

-- 删除旧表（如果存在）
DROP TABLE IF EXISTS review_records CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 用户表（参考 snappicker 的 users 表设计）
CREATE TABLE users (
    -- 基础字段
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),

    -- 用户信息（参考 snappicker）
    nickname VARCHAR(100),
    avatar_url VARCHAR(500),
    gender INTEGER DEFAULT 0 CHECK (gender IN (0, 1, 2)),
    country VARCHAR(50),
    province VARCHAR(50),
    city VARCHAR(50),
    language VARCHAR(20) DEFAULT 'zh_CN',
    phone_number VARCHAR(20),

    -- 账号状态
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    is_staff BOOLEAN DEFAULT FALSE,

    -- 论文综述相关（新增）
    review_count INTEGER DEFAULT 0,
    review_quota INTEGER DEFAULT 10,
    total_papers_used INTEGER DEFAULT 0,

    -- 时间字段
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_nickname ON users(nickname);
CREATE INDEX idx_users_created_at ON users(created_at);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 综述记录表（新增）
CREATE TABLE review_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    -- 综述内容
    topic VARCHAR(500) NOT NULL,
    review TEXT,
    statistics TEXT,

    -- 生成参数
    target_count INTEGER DEFAULT 50,
    recent_years_ratio FLOAT DEFAULT 0.5,
    english_ratio FLOAT DEFAULT 0.3,

    -- 状态
    status VARCHAR(20) DEFAULT 'completed',
    error_message TEXT,

    -- 时间字段
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_review_records_user_id ON review_records(user_id);
CREATE INDEX idx_review_records_topic ON review_records(topic);
CREATE INDEX idx_review_records_created_at ON review_records(created_at);

-- 创建更新时间触发器
CREATE TRIGGER update_review_records_updated_at BEFORE UPDATE ON review_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入测试管理员用户
-- 密码: Admin123
INSERT INTO users (email, hashed_password, nickname, is_active, is_verified, is_staff, is_superuser, review_quota)
VALUES (
    'admin@autooverview.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzW5qHl9qu',
    '管理员',
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    9999
);

-- 查看表结构
\d users
\d review_records

-- 查看测试用户
SELECT id, email, nickname, review_quota FROM users;
