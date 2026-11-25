FROM ghcr.io/astral-sh/uv:0.12.2 AS uv
FROM python:3.13-slim AS dependencies

COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

FROM python:3.13-slim

ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
COPY --from=dependencies /opt/venv /opt/venv
COPY --chown=app:app . .

USER app
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn --bind 0.0.0.0:8000 --workers 2 config.wsgi:application"]
