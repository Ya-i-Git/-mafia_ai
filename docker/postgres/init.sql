-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Настройка производительности
ALTER SYSTEM SET max_connections = '200';
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = '0.9';
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = '100';

-- Создание пользователя для приложения (если не создан через переменные окружения)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
        CREATE USER app_user WITH PASSWORD 'app_password';
        GRANT CONNECT ON DATABASE mafia_db TO app_user;
        GRANT USAGE ON SCHEMA public TO app_user;
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
    END IF;
END
$$;

-- Создание пользователя для аналитики
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'analytics_user') THEN
        CREATE USER analytics_user WITH PASSWORD 'analytics_password';
        GRANT CONNECT ON DATABASE mafia_db TO analytics_user;
        GRANT USAGE ON SCHEMA public TO analytics_user;
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_user;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO analytics_user;
    END IF;
END
$$;