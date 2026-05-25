## Структура проекта

\`\`\`
mafia-game/
├── README.md
├── .gitignore
├── pyproject.toml                     # создан командой uv init
├── docker-compose.yml                 # основной compose-файл (все сервисы)
├── requirements/                      # зависимости по модулям (опционально)
│   ├── server.txt
│   ├── narrator.txt
│   └── analytics.txt
│
├── infra/                             # конфигурации Docker и окружения
│   ├── airflow/
│   │   ├── Dockerfile
│   │   ├── dags/                      # сюда монтируются DAGs из etl/dags
│   │   ├── logs/
│   │   └── plugins/
│   ├── superset/
│   │   ├── Dockerfile
│   │   └── superset_config.py
│   └── nginx/                         # если нужен reverse proxy (опционально)
│       └── default.conf
│
├── db/                                # всё, что связано с базой данных
│   ├── alembic.ini
│   ├── alembic/                       # миграции Alembic
│   │   ├── env.py
│   │   └── versions/
│   └── models/                        # SQLAlchemy модели
│       ├── __init__.py
│       ├── user.py
│       ├── game.py
│       └── stats.py
│
├── server/                            # FastAPI приложение
│   ├── __init__.py
│   ├── main.py                        # точка входа, инициализация приложения
│   ├── config.py                      # настройки (env, БД, ключи)
│   ├── dependencies.py                # зависимости FastAPI (сессии БД, текущий пользователь)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py                    # регистрация, логин
│   │   ├── lobby.py                   # создание/присоединение к игре
│   │   └── websocket.py               # WebSocket-эндпоинты
│   ├── game/                          # игровая логика
│   │   ├── __init__.py
│   │   ├── session.py                 # класс GameSession, управление фазами
│   │   ├── roles.py                   # конфигурации ролей, раздача
│   │   ├── voting.py                  # голосование, обработка команд !vote
│   │   ├── night.py                   # ночные действия
│   │   └── timer.py                   # управление таймерами
│   ├── services/                      # бизнес-логика, связь с БД и нарратором
│   │   ├── __init__.py
│   │   ├── game_service.py
│   │   └── stats_service.py
│   ├── templates/                     # Jinja2 шаблоны (если используем для игрового интерфейса)
│   │   ├── index.html
│   │   └── game.html
│   └── static/                        # статика для фронтенда (JS, CSS, аудио)
│       ├── css/
│       ├── js/
│       │   ├── chat.js                # WebSocket клиент, управление чатами
│       │   └── game.js                # логика UI: таймеры, кнопки
│       └── audio/                     # звуковые сигналы (mp3)
│
├── narrator/                          # модуль AI-ведущего (пакет)
│   ├── __init__.py
│   ├── generator.py                   # основная функция generate(event, world, context)
│   ├── prompts/
│   │   ├── cyberpunk.yaml
│   │   └── medieval.yaml
│   ├── langchain_utils.py             # настройка цепочек LangChain
│   └── content/                       # собранные вручную/автоматически фразы (кеш)
│       ├── cyberpunk.json
│       └── medieval.json
│
├── analytics/                         # Streamlit и аналитика
│   ├── app.py                         # точка входа Streamlit
│   ├── pages/                         # страницы дашборда
│   │   ├── player_stats.py
│   │   └── global_stats.py
│   ├── queries.py                     # SQL-запросы или функции для получения данных
│   └── config.py                      # подключение к БД
│
├── etl/                               # сбор контента
│   ├── dags/
│   │   └── wiki_parser_dag.py         # Airflow DAG
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── cyberpunk.py
│   │   └── medieval.py
│   └── output/                        # сохраняемые данные (или сразу в БД)
│
├── tests/
│   ├── conftest.py
│   ├── test_server/
│   ├── test_game/
│   ├── test_narrator/
│   └── test_etl/
│
└── docs/
    ├── api.md
    ├── websocket_protocol.md
    └── setup_guide.md
\`\`\`