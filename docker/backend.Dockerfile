FROM python:3.12-slim

WORKDIR /app

# Копируем requirements
COPY backend/requirements/*.txt ./requirements/
RUN pip install --no-cache-dir -r requirements/server.txt
RUN pip install --no-cache-dir -r requirements/narrator.txt

# Копируем весь код
COPY backend /app/backend
COPY .env /app/.env

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "backend.server.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]