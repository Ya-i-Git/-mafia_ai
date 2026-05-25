import os

def create_structure(base_path="."):
    # Список папок и файлов для создания
    paths = [
        # requirements (опционально, можно удалить, если всё в pyproject.toml)
        "requirements/server.txt",
        "requirements/narrator.txt",
        "requirements/analytics.txt",

        # infra
        "infra/airflow/Dockerfile",
        "infra/airflow/dags/.gitkeep",
        "infra/airflow/logs/.gitkeep",
        "infra/airflow/plugins/.gitkeep",
        "infra/superset/Dockerfile",
        "infra/superset/superset_config.py",
        "infra/nginx/default.conf",

        # db
        "db/alembic.ini",
        "db/alembic/env.py",
        "db/alembic/versions/.gitkeep",
        "db/models/__init__.py",
        "db/models/user.py",
        "db/models/game.py",
        "db/models/stats.py",

        # server
        "server/__init__.py",
        "server/main.py",
        "server/config.py",
        "server/dependencies.py",
        "server/routers/__init__.py",
        "server/routers/auth.py",
        "server/routers/lobby.py",
        "server/routers/websocket.py",
        "server/game/__init__.py",
        "server/game/session.py",
        "server/game/roles.py",
        "server/game/voting.py",
        "server/game/night.py",
        "server/game/timer.py",
        "server/services/__init__.py",
        "server/services/game_service.py",
        "server/services/stats_service.py",
        "server/templates/index.html",
        "server/templates/game.html",
        "server/static/css/.gitkeep",
        "server/static/js/chat.js",
        "server/static/js/game.js",
        "server/static/audio/.gitkeep",

        # narrator
        "narrator/__init__.py",
        "narrator/generator.py",
        "narrator/prompts/cyberpunk.yaml",
        "narrator/prompts/medieval.yaml",
        "narrator/langchain_utils.py",
        "narrator/content/cyberpunk.json",
        "narrator/content/medieval.json",

        # analytics
        "analytics/app.py",
        "analytics/pages/player_stats.py",
        "analytics/pages/global_stats.py",
        "analytics/queries.py",
        "analytics/config.py",

        # etl
        "etl/dags/wiki_parser_dag.py",
        "etl/parsers/__init__.py",
        "etl/parsers/base.py",
        "etl/parsers/cyberpunk.py",
        "etl/parsers/medieval.py",
        "etl/output/.gitkeep",

        # tests (добавляем свои тесты, uv init мог уже создать папку tests)
        "tests/conftest.py",
        "tests/test_server/.gitkeep",
        "tests/test_game/.gitkeep",
        "tests/test_narrator/.gitkeep",
        "tests/test_etl/.gitkeep",

        # docs
        "docs/api.md",
        "docs/websocket_protocol.md",
        "docs/setup_guide.md",
    ]

    # Проверяем, есть ли уже pyproject.toml (признак uv init)
    if os.path.exists(os.path.join(base_path, "pyproject.toml")):
        print("[!] Найден pyproject.toml – uv init уже выполнен. Сохраняем существующие файлы.")
    else:
        print("[+] pyproject.toml не найден, создаём минимальный для uv")
        pyproject_content = """[project]
name = "mafia-game"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    # Заполните позже
]
"""
        with open(os.path.join(base_path, "pyproject.toml"), "w", encoding="utf-8") as f:
            f.write(pyproject_content)

    # Создаём папки и файлы
    for path in paths:
        full_path = os.path.join(base_path, path)
        dirname = os.path.dirname(full_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        # Пропускаем файлы .gitkeep (они только для сохранения папок в git)
        if os.path.basename(path) == ".gitkeep":
            if not os.path.exists(full_path):
                open(full_path, "w").close()
            continue

        # Если это обычный файл и он ещё не существует, создаём
        if not os.path.exists(full_path):
            with open(full_path, "w", encoding="utf-8") as f:
                # Для __init__.py пишем минимальный комментарий
                if os.path.basename(path) == "__init__.py":
                    f.write("# package init\n")
                else:
                    f.write("")  # пустой файл
        else:
            print(f"[!] Файл уже существует, пропускаем: {full_path}")

if __name__ == "__main__":
    create_structure()
    print("\nСтруктура проекта дополнена. Можно продолжать работу!")