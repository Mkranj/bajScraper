FROM python:3.12-slim-trixie
# uv for recreating environment
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY scraper.py app/scraper.py
COPY pyproject.toml app/pyproject.toml
COPY uv.lock app/pyproject.toml

WORKDIR /app
RUN uv sync --locked

CMD ["uv", "run", "scraper.py", "-j", "/JSON", "--max_jitter", "10"]