## Структура проекта
```
mafia-game/
├── backend/                        # весь Python‑код и ресурсы
│   ├── server/                     # FastAPI приложение
│   │   ├── __init__.py
│   │   ├── main.py                 # точка входа
│   │   ├── config.py               # настройки (БД, ключи, провайдеры)
│   │   ├── dependencies.py         # зависимости FastAPI (сессии БД)
│   │   ├── routers/                # REST + WebSocket эндпоинты
│   │   │   ├── auth.py
│   │   │   ├── lobby.py
│   │   │   └── websocket.py
│   │   ├── game/                   # игровая логика
│   │   │   ├── session.py
│   │   │   ├── roles.py
│   │   │   ├── constants.py
│   │   │   └── ...                 # player.py, voting.py, night.py при необходимости
│   │   └── services/               # слой бизнес‑логики (game_manager, stats)
│   │       ├── game_manager.py
│   │       └── stats_service.py
│   │
│   ├── narrator/                   # AI‑ведущий
│   │   ├── generator.py            # асинхронный вызов цепочки
│   │   ├── graph.py                # граф LangGraph
│   │   ├── schemas.py
│   │   ├── events.py               # константы событий
│   │   ├── prompts/                # YAML‑промпты по мирам
│   │   │   ├── cyberpunk.yaml
│   │   │   └── medieval.yaml
│   │   └── content/                # собранные (ETL) фразы/факты
│   │       ├── cyberpunk.json
│   │       └── medieval.json
│   │
│   ├── db/                         # модели SQLAlchemy + миграции Alembic
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── game.py
│   │   │   └── stats.py
│   │   ├── alembic.ini
│   │   └── alembic/
│   │
│   ├── etl/                        # сбор контента (Airflow DAG + парсеры)
│   │   ├── dags/
│   │   │   └── wiki_parser_dag.py
│   │   ├── parsers/
│   │   │   ├── base.py
│   │   │   ├── cyberpunk.py
│   │   │   └── medieval.py
│   │   └── output/
│   │
│   ├── analytics/                  # Streamlit дашборд (аналитика)
│   │   ├── app.py
│   │   ├── pages/
│   │   ├── queries.py
│   │   └── config.py
│   │
│   ├── tests/                      # все тесты
│   │   ├── conftest.py
│   │   ├── test_server/
│   │   ├── test_game/
│   │   ├── test_narrator/
│   │   └── test_etl/
│   │
│   ├── requirements/               # зависимости по группам
│   │   ├── server.txt
│   │   ├── narrator.txt
│   │   ├── analytics.txt
│   │   └── dev.txt
│   │
│   └── pyproject.toml              # общие настройки, зависимости, pytest
│
├── frontend/                       # React (Vite) приложение
│   ├── public/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── docker/                         # всё, что нужно для сборки и запуска
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   ├── nginx/
│   │   └── default.conf
│   └── superset/
│       └── superset_config.py
│
├── docker-compose.yml              # основной compose (postgres, backend, frontend, nginx, airflow, superset)
├── .env                            # переменные окружения (SECRET_KEY, DATABASE_URL, GROQ_API_KEY и т.д.)
└── README.md
```

uv pip install -e ./backend - Установить все зависимости backend
cd frontend
npm install