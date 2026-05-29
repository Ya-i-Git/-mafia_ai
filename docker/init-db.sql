-- docker/init-db.sql
-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Создание пользователя для приложения (если не существует)
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE rolname = 'mafia_app') THEN
      CREATE ROLE mafia_app WITH LOGIN PASSWORD 'app_password';
   END IF;
END
$do$;

-- Предоставление прав
GRANT CONNECT ON DATABASE mafia_db TO mafia_app;
GRANT USAGE ON SCHEMA public TO mafia_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mafia_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mafia_app;

-- Создание таблиц (если не существуют)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    role VARCHAR(20) DEFAULT 'player',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Пользователи игры Мафия';
COMMENT ON COLUMN users.username IS 'Имя пользователя для входа';
COMMENT ON COLUMN users.password_hash IS 'Хеш пароля с солью';