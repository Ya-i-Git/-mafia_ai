import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context

# Добавляем корневую директорию проекта в sys.path,
# чтобы можно было импортировать модули из backend
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from backend.db.base import Base
from backend.db.config import DatabaseConfig

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Интерпретируем файл конфигурации логов.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные моделей – Alembic будет отслеживать изменения в этих таблицах
target_metadata = Base.metadata


def get_sync_url() -> str:
    """Возвращает синхронный URL для подключения к PostgreSQL."""
    return DatabaseConfig.get_database_url()


def run_migrations_offline() -> None:
    """Запуск миграций в offline-режиме (без подключения к БД)."""
    url = get_sync_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Вспомогательная функция для выполнения миграций с переданным соединением."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Запуск миграций в online-режиме (с реальным подключением к БД)."""
    # Создаём синхронный движок из конфигурации Alembic,
    # но подставляем наш URL из DatabaseConfig.
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_sync_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())