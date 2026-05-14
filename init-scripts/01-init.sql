-- ClawSwarm 数据库初始化脚本
-- 此脚本在 PostgreSQL 容器首次启动时自动执行

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 打印初始化信息
\echo 'ClawSwarm Database initialized'
